"""Create small, dashboard-ready data marts from verified processed data."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
PROCESSED = ROOT / "data" / "processed"
MARTS = ROOT / "data" / "marts"
LOGS = ROOT / "logs"
FEATURES_PATH = PROCESSED / "user_features.parquet"
REVENUE_PATH = PROCESSED / "revenue_experiment.parquet"
RETENTION_DAYS = (1, 3, 7, 14, 30)
VALUE_SEGMENT_ORDER = {
    "no_revenue": 1,
    "negative_value": 2,
    "low_value": 3,
    "medium_value": 4,
    "high_value": 5,
}


def summarize_group(frame: pd.DataFrame) -> dict:
    users = len(frame)
    gross = float(frame["total_revenue"].sum())
    cashout = float(frame["total_cashout"].sum())
    net = float(frame["net_revenue"].sum())
    row = {
        "users": users,
        "activated_users": int(frame["activated"].sum()),
        "monetized_users": int(frame["is_monetized"].sum()),
        "cashout_users": int(frame["has_cashout"].sum()),
        "gross_revenue": gross,
        "cashout": cashout,
        "net_revenue": net,
        "ad_revenue": float(frame["ad_revenue"].sum()),
        "offerwall_revenue": float(frame["offerwall_revenue"].sum()),
        "transaction_count": int(frame["transaction_count"].sum()),
        "activation_rate": float(frame["activated"].mean()) if users else 0.0,
        "monetization_rate": float(frame["is_monetized"].mean()) if users else 0.0,
        "cashout_user_rate": float(frame["has_cashout"].mean()) if users else 0.0,
        "arpu": gross / users if users else 0.0,
        "avg_net_revenue_per_user": net / users if users else 0.0,
        "avg_cashout_per_user": cashout / users if users else 0.0,
        "median_revenue": float(frame["total_revenue"].median()) if users else 0.0,
        "median_net_revenue": float(frame["net_revenue"].median()) if users else 0.0,
    }
    for day in RETENTION_DAYS:
        eligible = frame[f"eligible_d{day}"].astype(bool)
        exact = frame[f"exact_activity_d{day}"].astype(bool)
        rolling = frame[f"rolling_activity_d{day}_plus"].astype(bool)
        denominator = int(eligible.sum())
        exact_users = int((eligible & exact).sum())
        rolling_users = int((eligible & rolling).sum())
        row[f"d{day}_eligible_users"] = denominator
        row[f"d{day}_exact_active_users"] = exact_users
        row[f"d{day}_exact_activity_rate"] = exact_users / denominator if denominator else np.nan
        row[f"d{day}_rolling_active_users"] = rolling_users
        row[f"d{day}_rolling_activity_rate"] = rolling_users / denominator if denominator else np.nan
    return row


def summarize_by(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    records = []
    grouper = group_columns[0] if len(group_columns) == 1 else group_columns
    for keys, group in frame.groupby(grouper, dropna=False, observed=True, sort=True):
        if len(group_columns) == 1:
            keys = (keys,)
        record = dict(zip(group_columns, keys))
        record.update(summarize_group(group))
        records.append(record)
    return pd.DataFrame(records)


def add_user_value_segments(features: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Classify users by observed net contribution without exposing user rows."""
    positive_net = features.loc[features["net_revenue"].gt(0), "net_revenue"]
    if positive_net.empty:
        raise ValueError("Cannot build value segments without positive net revenue")

    low_upper = float(positive_net.quantile(0.50))
    medium_upper = float(positive_net.quantile(0.90))
    segmented = features.copy()
    segmented["value_segment"] = np.select(
        [
            segmented["net_revenue"].lt(0),
            segmented["total_revenue"].le(0),
            segmented["net_revenue"].le(low_upper),
            segmented["net_revenue"].le(medium_upper),
        ],
        ["negative_value", "no_revenue", "low_value", "medium_value"],
        default="high_value",
    )
    return segmented, {
        "positive_net_median": low_upper,
        "positive_net_p90": medium_upper,
    }


def build() -> dict:
    MARTS.mkdir(parents=True, exist_ok=True)
    LOGS.mkdir(parents=True, exist_ok=True)

    features = pd.read_parquet(FEATURES_PATH)
    features["install_week"] = (
        features["install_dt"].dt.to_period("W-SUN").dt.start_time
    )

    overall = pd.DataFrame([summarize_group(features)])
    overall["observation_start"] = features["install_dt"].min()
    overall["observation_end"] = features["last_activity_dt"].max()

    variation = summarize_by(features, ["variation"])
    channel = summarize_by(features, ["channel_clean"])
    country = summarize_by(features, ["country_code"])
    platform = summarize_by(features, ["platform"])
    os_version = summarize_by(features, ["os_version_clean"])
    cohorts = summarize_by(features, ["install_week", "variation"])

    segmented, value_thresholds = add_user_value_segments(features)
    value_segments = summarize_by(segmented, ["value_segment"])
    value_segments["segment_order"] = value_segments["value_segment"].map(VALUE_SEGMENT_ORDER)
    value_segments["user_share"] = value_segments["users"] / len(segmented)
    total_net = float(segmented["net_revenue"].sum())
    value_segments["net_revenue_share"] = (
        value_segments["net_revenue"] / total_net if total_net else np.nan
    )
    value_segments["positive_net_median"] = value_thresholds["positive_net_median"]
    value_segments["positive_net_p90"] = value_thresholds["positive_net_p90"]
    value_segments = value_segments.sort_values("segment_order").reset_index(drop=True)

    revenue = pd.read_parquet(
        REVENUE_PATH,
        columns=["revenue_type", "ad_unit_format_clean", "revenue_amount", "user_id"],
    )
    ad_rows = revenue.loc[revenue["revenue_type"].eq("ad")].copy()
    ad_formats = (
        ad_rows.groupby("ad_unit_format_clean", dropna=False, observed=True)
        .agg(
            transactions=("user_id", "size"),
            users=("user_id", "nunique"),
            total_revenue=("revenue_amount", "sum"),
            average_revenue_per_event=("revenue_amount", "mean"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )
    ad_total = float(ad_formats["total_revenue"].sum())
    ad_formats["revenue_share"] = (
        ad_formats["total_revenue"] / ad_total if ad_total else 0.0
    )

    revenue_types = (
        revenue.groupby("revenue_type", dropna=False, observed=True)
        .agg(
            transactions=("user_id", "size"),
            users=("user_id", "nunique"),
            total_revenue=("revenue_amount", "sum"),
        )
        .reset_index()
        .sort_values("total_revenue", ascending=False)
    )

    outputs = {
        "overall_kpis": overall,
        "variation_summary": variation,
        "channel_summary": channel,
        "country_summary": country,
        "platform_summary": platform,
        "os_version_summary": os_version,
        "user_value_segments": value_segments,
        "retention_cohorts": cohorts,
        "ad_format_summary": ad_formats,
        "revenue_type_summary": revenue_types,
    }

    manifest = {}
    for name, frame in outputs.items():
        path = MARTS / f"{name}.parquet"
        frame.to_parquet(path, index=False, compression="zstd")
        manifest[name] = {
            "path": str(path),
            "rows": len(frame),
            "columns": len(frame.columns),
            "bytes": path.stat().st_size,
        }

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": str(FEATURES_PATH),
        "manifest": manifest,
        "headline": {
            "users": int(overall.loc[0, "users"]),
            "gross_revenue": float(overall.loc[0, "gross_revenue"]),
            "cashout": float(overall.loc[0, "cashout"]),
            "net_revenue": float(overall.loc[0, "net_revenue"]),
            "arpu": float(overall.loc[0, "arpu"]),
            "avg_net_revenue_per_user": float(overall.loc[0, "avg_net_revenue_per_user"]),
        },
    }
    report_path = LOGS / "data_marts_build_report.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return report


if __name__ == "__main__":
    build()
