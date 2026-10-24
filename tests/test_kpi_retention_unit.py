"""Focused unit tests for KPI and retention aggregation rules."""

import math

import pandas as pd

from src.analytics.build_data_marts import RETENTION_DAYS, summarize_by, summarize_group


def sample_features() -> pd.DataFrame:
    frame = pd.DataFrame(
        {
            "variation": ["default", "default", "treatment"],
            "total_revenue": [10.0, 20.0, 0.0],
            "total_cashout": [0.0, 5.0, 0.0],
            "net_revenue": [10.0, 15.0, 0.0],
            "activated": [1, 1, 0],
            "is_monetized": [True, True, False],
            "has_cashout": [False, True, False],
            "ad_revenue": [8.0, 12.0, 0.0],
            "offerwall_revenue": [2.0, 8.0, 0.0],
            "transaction_count": [1, 2, 0],
        }
    )
    for day in RETENTION_DAYS:
        frame[f"eligible_d{day}"] = [True, True, False]
        frame[f"exact_activity_d{day}"] = [True, False, False]
        frame[f"rolling_activity_d{day}_plus"] = [True, True, False]
    return frame


def test_financial_kpis_include_zero_revenue_users() -> None:
    result = summarize_group(sample_features())

    assert result["users"] == 3
    assert result["gross_revenue"] == 30.0
    assert result["cashout"] == 5.0
    assert result["net_revenue"] == 25.0
    assert math.isclose(result["arpu"], 10.0)
    assert math.isclose(result["avg_net_revenue_per_user"], 25 / 3)
    assert math.isclose(result["monetization_rate"], 2 / 3)


def test_retention_uses_only_eligible_users_as_denominator() -> None:
    result = summarize_group(sample_features())

    for day in RETENTION_DAYS:
        assert result[f"d{day}_eligible_users"] == 2
        assert result[f"d{day}_exact_active_users"] == 1
        assert result[f"d{day}_rolling_active_users"] == 2
        assert result[f"d{day}_exact_activity_rate"] == 0.5
        assert result[f"d{day}_rolling_activity_rate"] == 1.0


def test_group_summary_reconciles_to_overall() -> None:
    frame = sample_features()
    grouped = summarize_by(frame, ["variation"])
    overall = summarize_group(frame)

    assert grouped["users"].sum() == overall["users"]
    assert grouped["gross_revenue"].sum() == overall["gross_revenue"]
    assert grouped["net_revenue"].sum() == overall["net_revenue"]


def test_zero_eligible_users_produces_nan_retention_rate() -> None:
    frame = sample_features().iloc[[2]].copy()
    result = summarize_group(frame)

    for day in RETENTION_DAYS:
        assert result[f"d{day}_eligible_users"] == 0
        assert math.isnan(result[f"d{day}_exact_activity_rate"])
        assert math.isnan(result[f"d{day}_rolling_activity_rate"])
