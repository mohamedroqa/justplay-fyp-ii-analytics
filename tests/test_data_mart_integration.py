"""Integration test for the processed-features to Data Mart pipeline."""

from pathlib import Path

import pandas as pd

from src.analytics import build_data_marts


def synthetic_features() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "user_id": [f"u{i}" for i in range(6)],
            "variation": ["default"] * 3 + ["treatment"] * 3,
            "channel_clean": ["organic", "ads", "organic", "ads", "organic", "ads"],
            "country_code": ["us", "us", "ca", "us", "ca", "ca"],
            "install_dt": pd.to_datetime(["2025-01-01"] * 6),
            "last_activity_dt": pd.to_datetime(["2025-01-10"] * 6),
            "total_revenue": [10.0, 20.0, 0.0, 5.0, 15.0, 25.0],
            "total_cashout": [0.0, 2.0, 0.0, 0.0, 3.0, 5.0],
            "net_revenue": [10.0, 18.0, 0.0, 5.0, 12.0, 20.0],
            "activated": [1, 1, 0, 1, 1, 1],
            "is_monetized": [True, True, False, True, True, True],
            "has_cashout": [False, True, False, False, True, True],
            "ad_revenue": [8.0, 15.0, 0.0, 4.0, 10.0, 20.0],
            "offerwall_revenue": [2.0, 5.0, 0.0, 1.0, 5.0, 5.0],
            "transaction_count": [1, 2, 0, 1, 2, 2],
        }
    )
    for day in build_data_marts.RETENTION_DAYS:
        eligible = day <= 7
        frame[f"eligible_d{day}"] = eligible
        frame[f"exact_activity_d{day}"] = [eligible, False, False, eligible, False, eligible]
        frame[f"rolling_activity_d{day}_plus"] = [eligible, eligible, False, eligible, eligible, eligible]
    return frame


def test_data_mart_build_end_to_end(tmp_path: Path, monkeypatch) -> None:
    processed = tmp_path / "processed"
    marts = tmp_path / "marts"
    logs = tmp_path / "logs"
    processed.mkdir()

    features_path = processed / "user_features.parquet"
    revenue_path = processed / "revenue_experiment.parquet"
    synthetic_features().to_parquet(features_path, index=False)
    pd.DataFrame(
        {
            "user_id": ["u0", "u1", "u3", "u4", "u5"],
            "revenue_type": ["ad", "offerwall", "ad", "ad", "offerwall"],
            "ad_unit_format_clean": ["banner", "Not Applicable", "rewarded", "banner", "Not Applicable"],
            "revenue_amount": [10.0, 20.0, 5.0, 15.0, 25.0],
        }
    ).to_parquet(revenue_path, index=False)

    monkeypatch.setattr(build_data_marts, "FEATURES_PATH", features_path)
    monkeypatch.setattr(build_data_marts, "REVENUE_PATH", revenue_path)
    monkeypatch.setattr(build_data_marts, "MARTS", marts)
    monkeypatch.setattr(build_data_marts, "LOGS", logs)

    report = build_data_marts.build()
    overall = pd.read_parquet(marts / "overall_kpis.parquet").iloc[0]
    variations = pd.read_parquet(marts / "variation_summary.parquet")

    assert report["headline"]["users"] == 6
    assert overall["gross_revenue"] == 75.0
    assert overall["net_revenue"] == 65.0
    assert variations["users"].sum() == 6
    assert variations["gross_revenue"].sum() == 75.0
    assert (logs / "data_marts_build_report.json").exists()
    for path in marts.glob("*.parquet"):
        assert "user_id" not in pd.read_parquet(path).columns
