"""Build the processed Parquet layer and one-row-per-user feature table.

Raw CSV files are read only. Only transactions whose user_id exists in the
experiment users file are written to the processed experiment dataset.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_DIR = ROOT / "logs"

USERS_CSV = RAW_DIR / "users_data_final_case_study.csv"
REVENUE_CSV = RAW_DIR / "revenue_data_final_case_study.csv"
USERS_PARQUET = PROCESSED_DIR / "users.parquet"
REVENUE_PARQUET = PROCESSED_DIR / "revenue_experiment.parquet"
USER_FEATURES_PARQUET = PROCESSED_DIR / "user_features.parquet"
REPORT_PATH = LOG_DIR / "processed_build_report.json"

CHUNK_SIZE = 250_000
RETENTION_DAYS = (1, 3, 7, 14, 30)
MONEY_COLUMNS = ("revenue_amount", "cashout_amount", "earning_amount")


def prepare_users() -> pd.DataFrame:
    users = pd.read_csv(USERS_CSV, low_memory=False)
    if users["user_id"].duplicated().any():
        raise ValueError("users CSV contains duplicate user_id values")

    for column in ["user_id", "variation", "country_code", "platform", "os_version", "channel"]:
        users[column] = users[column].astype("string")
    for column in ["assignment_dt", "install_dt"]:
        users[column] = pd.to_datetime(users[column], errors="coerce")
    for column in ["assigned", "activated"]:
        users[column] = pd.to_numeric(users[column], errors="raise").astype("int8")

    users["channel_clean"] = users["channel"].str.strip().replace({"missing": "Unknown"})
    users["os_version_clean"] = users["os_version"].str.strip().replace({"missing": "Unknown"})
    users["country_code"] = users["country_code"].str.lower()
    users["platform"] = users["platform"].str.lower()
    return users


def safe_timestamp_array(values: np.ndarray, sentinel: int) -> pd.Series:
    clean = values.copy()
    clean[clean == sentinel] = np.iinfo(np.int64).min
    return pd.Series(pd.to_datetime(clean, unit="ns", errors="coerce"))


def build() -> dict:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    users = prepare_users()
    users.to_parquet(USERS_PARQUET, index=False, compression="zstd")

    user_count = len(users)
    user_position = pd.Series(
        np.arange(user_count, dtype=np.int64),
        index=users["user_id"],
    )
    install_days = users["install_dt"].to_numpy(dtype="datetime64[D]").astype(np.int64)

    total_revenue = np.zeros(user_count, dtype=np.float64)
    total_cashout = np.zeros(user_count, dtype=np.float64)
    total_earnings = np.zeros(user_count, dtype=np.float64)
    cashout_transactions = np.zeros(user_count, dtype=np.int64)
    transaction_count = np.zeros(user_count, dtype=np.int64)
    ad_revenue = np.zeros(user_count, dtype=np.float64)
    offerwall_revenue = np.zeros(user_count, dtype=np.float64)
    first_activity_ns = np.full(user_count, np.iinfo(np.int64).max, dtype=np.int64)
    last_activity_ns = np.full(user_count, np.iinfo(np.int64).min, dtype=np.int64)
    max_activity_day = np.full(user_count, -1, dtype=np.int32)
    exact_activity = {day: np.zeros(user_count, dtype=np.bool_) for day in RETENTION_DAYS}

    temp_revenue = REVENUE_PARQUET.with_suffix(".parquet.tmp")
    if temp_revenue.exists():
        temp_revenue.unlink()
    writer: pq.ParquetWriter | None = None

    raw_rows = 0
    matched_rows = 0
    external_rows = 0
    invalid_created_at = 0
    negative_activity_rows = 0
    observation_end_day: int | None = None
    source_id_min: int | None = None
    source_id_max: int | None = None
    chunk_number = 0

    try:
        for chunk in pd.read_csv(REVENUE_CSV, chunksize=CHUNK_SIZE, low_memory=False):
            chunk_number += 1
            raw_rows += len(chunk)
            chunk["user_id"] = chunk["user_id"].astype("string")
            positions = chunk["user_id"].map(user_position)
            matched_mask = positions.notna()
            external_rows += int((~matched_mask).sum())
            chunk = chunk.loc[matched_mask].copy()
            pos = positions.loc[matched_mask].to_numpy(dtype=np.int64)
            matched_rows += len(chunk)

            chunk.rename(columns={"Unnamed: 0": "source_row_id"}, inplace=True)
            chunk["source_row_id"] = pd.to_numeric(chunk["source_row_id"], errors="raise").astype("int64")
            current_min = int(chunk["source_row_id"].min()) if len(chunk) else None
            current_max = int(chunk["source_row_id"].max()) if len(chunk) else None
            if current_min is not None:
                source_id_min = current_min if source_id_min is None else min(source_id_min, current_min)
                source_id_max = current_max if source_id_max is None else max(source_id_max, current_max)

            chunk["created_at"] = pd.to_datetime(chunk["created_at"], errors="coerce")
            invalid_created_at += int(chunk["created_at"].isna().sum())
            for column in MONEY_COLUMNS:
                chunk[column] = pd.to_numeric(chunk[column], errors="raise").astype("float64")
            chunk["cashout_transactions"] = pd.to_numeric(
                chunk["cashout_transactions"], errors="raise"
            ).astype("int64")
            chunk["ad_unit_format"] = chunk["ad_unit_format"].astype("string")
            chunk["revenue_type"] = chunk["revenue_type"].astype("string")
            chunk["ad_unit_format_clean"] = np.where(
                chunk["revenue_type"].eq("ad"),
                chunk["ad_unit_format"].replace({"missing": "Unknown"}),
                "Not Applicable",
            )
            chunk["ad_unit_format_clean"] = chunk["ad_unit_format_clean"].astype("string")

            np.add.at(total_revenue, pos, chunk["revenue_amount"].to_numpy())
            np.add.at(total_cashout, pos, chunk["cashout_amount"].to_numpy())
            np.add.at(total_earnings, pos, chunk["earning_amount"].to_numpy())
            np.add.at(cashout_transactions, pos, chunk["cashout_transactions"].to_numpy())
            np.add.at(transaction_count, pos, 1)

            ad_values = np.where(
                chunk["revenue_type"].eq("ad").to_numpy(),
                chunk["revenue_amount"].to_numpy(),
                0.0,
            )
            offerwall_values = np.where(
                chunk["revenue_type"].eq("offerwall").to_numpy(),
                chunk["revenue_amount"].to_numpy(),
                0.0,
            )
            np.add.at(ad_revenue, pos, ad_values)
            np.add.at(offerwall_revenue, pos, offerwall_values)

            valid_date_mask = chunk["created_at"].notna().to_numpy()
            if valid_date_mask.any():
                valid_pos = pos[valid_date_mask]
                created = chunk.loc[valid_date_mask, "created_at"]
                created_ns = created.to_numpy(dtype="datetime64[ns]").astype(np.int64)
                created_days = created.to_numpy(dtype="datetime64[D]").astype(np.int64)
                activity_days = created_days - install_days[valid_pos]
                negative_activity_rows += int((activity_days < 0).sum())
                np.minimum.at(first_activity_ns, valid_pos, created_ns)
                np.maximum.at(last_activity_ns, valid_pos, created_ns)
                np.maximum.at(max_activity_day, valid_pos, activity_days.astype(np.int32))
                chunk_end = int(created_days.max())
                observation_end_day = (
                    chunk_end if observation_end_day is None else max(observation_end_day, chunk_end)
                )
                for day in RETENTION_DAYS:
                    day_mask = activity_days == day
                    if day_mask.any():
                        np.maximum.at(exact_activity[day], valid_pos[day_mask], True)

            output_columns = [
                "source_row_id",
                "user_id",
                "created_at",
                "revenue_amount",
                "cashout_amount",
                "earning_amount",
                "cashout_transactions",
                "ad_unit_format",
                "ad_unit_format_clean",
                "revenue_type",
            ]
            table = pa.Table.from_pandas(chunk[output_columns], preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(
                    temp_revenue,
                    table.schema,
                    compression="zstd",
                    use_dictionary=True,
                )
            writer.write_table(table, row_group_size=CHUNK_SIZE)
            print(
                f"chunk={chunk_number} raw_rows={raw_rows:,} matched_rows={matched_rows:,}",
                flush=True,
            )
    finally:
        if writer is not None:
            writer.close()

    if REVENUE_PARQUET.exists():
        REVENUE_PARQUET.unlink()
    temp_revenue.replace(REVENUE_PARQUET)

    if observation_end_day is None:
        raise ValueError("No valid transaction dates were found")

    features = users.copy()
    features["total_revenue"] = total_revenue
    features["total_cashout"] = total_cashout
    features["net_revenue"] = total_revenue - total_cashout
    features["total_earnings"] = total_earnings
    features["cashout_transactions"] = cashout_transactions
    features["transaction_count"] = transaction_count
    features["ad_revenue"] = ad_revenue
    features["offerwall_revenue"] = offerwall_revenue
    features["is_monetized"] = total_revenue > 0
    features["has_cashout"] = total_cashout > 0
    features["first_activity_dt"] = safe_timestamp_array(first_activity_ns, np.iinfo(np.int64).max)
    features["last_activity_dt"] = safe_timestamp_array(last_activity_ns, np.iinfo(np.int64).min)
    features["max_activity_day"] = max_activity_day
    features["days_observed"] = observation_end_day - install_days

    retention_summary: dict[str, dict[str, int | float]] = {}
    for day in RETENTION_DAYS:
        eligible = features["days_observed"].to_numpy() >= day
        exact = exact_activity[day]
        rolling = max_activity_day >= day
        features[f"eligible_d{day}"] = eligible
        features[f"exact_activity_d{day}"] = exact
        features[f"rolling_activity_d{day}_plus"] = rolling
        denominator = int(eligible.sum())
        exact_numerator = int((eligible & exact).sum())
        rolling_numerator = int((eligible & rolling).sum())
        retention_summary[f"d{day}"] = {
            "eligible_users": denominator,
            "exact_active_users": exact_numerator,
            "exact_activity_rate": exact_numerator / denominator if denominator else 0.0,
            "rolling_active_users": rolling_numerator,
            "rolling_activity_rate": rolling_numerator / denominator if denominator else 0.0,
        }

    features.to_parquet(USER_FEATURES_PARQUET, index=False, compression="zstd")

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_rows": raw_rows,
        "matched_rows": matched_rows,
        "external_rows": external_rows,
        "user_rows": user_count,
        "users_with_transactions": int((transaction_count > 0).sum()),
        "users_without_transactions": int((transaction_count == 0).sum()),
        "invalid_created_at": invalid_created_at,
        "negative_activity_rows": negative_activity_rows,
        "observation_end": str(np.datetime64(observation_end_day, "D")),
        "source_row_id_min": source_id_min,
        "source_row_id_max": source_id_max,
        "totals": {
            "gross_revenue": float(total_revenue.sum()),
            "cashout": float(total_cashout.sum()),
            "net_revenue": float((total_revenue - total_cashout).sum()),
            "earnings": float(total_earnings.sum()),
            "cashout_transactions": int(cashout_transactions.sum()),
            "transaction_count": int(transaction_count.sum()),
            "ad_revenue": float(ad_revenue.sum()),
            "offerwall_revenue": float(offerwall_revenue.sum()),
        },
        "retention_summary": retention_summary,
        "outputs": {
            "users_parquet": str(USERS_PARQUET),
            "revenue_experiment_parquet": str(REVENUE_PARQUET),
            "user_features_parquet": str(USER_FEATURES_PARQUET),
        },
        "output_bytes": {
            "users_parquet": USERS_PARQUET.stat().st_size,
            "revenue_experiment_parquet": REVENUE_PARQUET.stat().st_size,
            "user_features_parquet": USER_FEATURES_PARQUET.stat().st_size,
        },
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = build()
    print(json.dumps(result, ensure_ascii=False, indent=2))
