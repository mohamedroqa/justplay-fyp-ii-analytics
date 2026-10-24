"""Dependency-light validation checks for statistical analysis outputs."""

from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "marts"
FEATURES = ROOT / "data" / "processed" / "user_features.parquet"


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


results = pd.read_parquet(MARTS / "statistical_tests.parquet")
descriptive = pd.read_parquet(MARTS / "variation_descriptive.parquet")
features = pd.read_parquet(
    FEATURES,
    columns=["variation", "total_revenue", "net_revenue", "activated", "is_monetized"],
)

check(len(results) == 48, "expected 48 planned hypothesis-test rows exist")
check(len(descriptive) == 10, "descriptive output has five variations by two metrics")
check(
    set(results["treatment_variation"]) == {
        "androidnd1order", "androidnd30order", "androidnd7order", "androidndorder"
    },
    "all four treatments are compared with default",
)
check((results["control_variation"] == "default").all(), "default is the control in every test")
check(
    results[["p_value", "p_value_holm"]].ge(0).all().all()
    and results[["p_value", "p_value_holm"]].le(1).all().all(),
    "raw and adjusted p-values stay within [0, 1]",
)
check(
    (results["p_value_holm"] + 1e-15 >= results["p_value"]).all(),
    "Holm-adjusted p-values are never below raw p-values",
)
check(
    (results["ci_95_low"] <= results["absolute_difference"]).all()
    and (results["absolute_difference"] <= results["ci_95_high"]).all(),
    "every reported difference lies inside its confidence interval",
)
check(
    not any("user_id" in column.lower() for column in results.columns)
    and not any("user_id" in column.lower() for column in descriptive.columns),
    "statistical marts expose no user identifier",
)

variation_means = features.groupby("variation", observed=True)[
    ["total_revenue", "net_revenue"]
].mean()
welch = results.loc[results["test_name"].eq("welch_t_test")]
for row in welch.itertuples(index=False):
    source_column = "total_revenue" if row.metric == "gross_revenue_per_user" else "net_revenue"
    check(
        np.isclose(row.control_value, variation_means.loc["default", source_column])
        and np.isclose(row.treatment_value, variation_means.loc[row.treatment_variation, source_column]),
        f"{row.metric}/{row.treatment_variation} means reconcile to user features",
    )

print("ALL_STATISTICAL_CHECKS_PASSED")
