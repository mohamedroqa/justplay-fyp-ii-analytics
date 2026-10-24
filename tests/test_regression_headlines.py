"""Regression locks for the verified headline results and business decision."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "marts"


def test_verified_headline_values_have_not_drifted() -> None:
    overall = pd.read_parquet(MARTS / "overall_kpis.parquet").iloc[0]

    assert int(overall["users"]) == 934_270
    assert np.isclose(overall["gross_revenue"], 4_981_893.057763822)
    assert np.isclose(overall["cashout"], 1_583_184.77)
    assert np.isclose(overall["net_revenue"], 3_398_708.287763823)
    assert np.isclose(overall["arpu"], 5.332391126509276)
    assert np.isclose(overall["avg_net_revenue_per_user"], 3.6378223508876677)


def test_expected_mart_shapes_have_not_drifted() -> None:
    expected_rows = {
        "overall_kpis": 1,
        "variation_summary": 5,
        "channel_summary": 19,
        "country_summary": 2,
        "retention_cohorts": 45,
        "ad_format_summary": 4,
        "revenue_type_summary": 3,
        "statistical_tests": 48,
        "variation_descriptive": 10,
        "outlier_sensitivity": 15,
    }
    for name, rows in expected_rows.items():
        assert len(pd.read_parquet(MARTS / f"{name}.parquet")) == rows


def test_business_decision_is_still_supported() -> None:
    tests = pd.read_parquet(MARTS / "statistical_tests.parquet")
    financial_welch = tests.loc[
        tests["test_name"].eq("welch_t_test")
        & tests["metric"].isin(["gross_revenue_per_user", "net_revenue_per_user"])
    ]
    assert len(financial_welch) == 8
    assert not financial_welch["significant_after_holm"].any()

    candidate = tests.loc[
        tests["treatment_variation"].eq("androidndorder")
        & tests["test_name"].eq("two_proportion_z_test")
        & tests["metric"].isin(["monetization_rate", "d1_rolling_activity_rate"])
    ]
    assert len(candidate) == 2
    assert candidate["significant_after_holm"].all()
    assert (candidate["absolute_difference"] > 0).all()
