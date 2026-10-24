import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
BUILD_REPORT = json.loads(
    (ROOT / "logs" / "processed_build_report.json").read_text(encoding="utf-8")
)
SCOPE_REPORT = json.loads(
    (ROOT / "logs" / "experiment_scope_audit.json").read_text(encoding="utf-8")
)


def test_parquet_row_counts():
    assert pq.ParquetFile(PROCESSED / "users.parquet").metadata.num_rows == 934_270
    assert pq.ParquetFile(PROCESSED / "user_features.parquet").metadata.num_rows == 934_270
    assert (
        pq.ParquetFile(PROCESSED / "revenue_experiment.parquet").metadata.num_rows
        == 11_256_114
    )


def test_build_scope_matches_audit():
    assert BUILD_REPORT["matched_rows"] == SCOPE_REPORT["matched_transaction_rows"]
    assert BUILD_REPORT["external_rows"] == SCOPE_REPORT["external_transaction_rows"]
    assert (
        BUILD_REPORT["users_with_transactions"]
        == SCOPE_REPORT["experiment_users_with_transactions"]
    )
    assert (
        BUILD_REPORT["users_without_transactions"]
        == SCOPE_REPORT["experiment_users_without_transactions"]
    )


def test_user_feature_financial_reconciliation():
    columns = [
        "user_id",
        "total_revenue",
        "total_cashout",
        "net_revenue",
        "total_earnings",
        "cashout_transactions",
        "transaction_count",
        "ad_revenue",
        "offerwall_revenue",
    ]
    frame = pd.read_parquet(PROCESSED / "user_features.parquet", columns=columns)
    assert len(frame) == 934_270
    assert frame["user_id"].nunique() == 934_270
    assert abs(frame["total_revenue"].sum() - 4_981_893.057763822) < 1e-6
    assert abs(frame["total_cashout"].sum() - 1_583_184.77) < 1e-6
    assert abs(frame["net_revenue"].sum() - 3_398_708.287763823) < 1e-6
    assert frame["cashout_transactions"].sum() == 1_640_933
    assert frame["transaction_count"].sum() == 11_256_114
    assert ((frame["total_revenue"] - frame["total_cashout"] - frame["net_revenue"]).abs() < 1e-10).all()
    assert ((frame["ad_revenue"] + frame["offerwall_revenue"] - frame["total_revenue"]).abs() < 1e-10).all()


def test_retention_flags_and_summary_are_consistent():
    columns = []
    for day in (1, 3, 7, 14, 30):
        columns.extend(
            [
                f"eligible_d{day}",
                f"exact_activity_d{day}",
                f"rolling_activity_d{day}_plus",
            ]
        )
    frame = pd.read_parquet(PROCESSED / "user_features.parquet", columns=columns)
    for day in (1, 3, 7, 14, 30):
        eligible = frame[f"eligible_d{day}"]
        exact = frame[f"exact_activity_d{day}"]
        rolling = frame[f"rolling_activity_d{day}_plus"]
        summary = BUILD_REPORT["retention_summary"][f"d{day}"]
        assert int(eligible.sum()) == summary["eligible_users"]
        assert int((eligible & exact).sum()) == summary["exact_active_users"]
        assert int((eligible & rolling).sum()) == summary["rolling_active_users"]
        assert (exact <= rolling).all()
        assert summary["exact_active_users"] <= summary["rolling_active_users"]
        assert summary["rolling_active_users"] <= summary["eligible_users"]


def test_no_invalid_or_preinstall_activity():
    assert BUILD_REPORT["invalid_created_at"] == 0
    assert BUILD_REPORT["negative_activity_rows"] == 0

