"""Validate the final duplicate and outlier audit outputs."""

import json
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "logs" / "duplicates_outliers_audit.json").read_text(encoding="utf-8"))
sensitivity = pd.read_parquet(ROOT / "data" / "marts" / "outlier_sensitivity.parquet")
variation = pd.read_parquet(ROOT / "data" / "marts" / "variation_summary.parquet")


def check(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
    print(f"PASS: {message}")


duplicates = report["duplicates"]
check(duplicates["rows"] == 11_256_114, "all eligible transaction rows were duplicate-checked")
check(duplicates["exact_duplicate_groups"] == 0, "no exact business-event duplicate groups exist")
check(duplicates["exact_duplicate_rows_beyond_first"] == 0, "no duplicate transaction rows require removal")
check(duplicates["duplicate_source_row_ids"] == 0, "source row identifiers are unique")

check(len(sensitivity) == 15, "outlier sensitivity contains five variations by three methods")
check(set(sensitivity["method"]) == {"original", "winsorized_global_p99", "trimmed_global_p99"},
      "all planned sensitivity methods exist")
check(not any("user_id" in column.lower() for column in sensitivity.columns),
      "outlier sensitivity mart exposes no user identifier")

original = sensitivity.loc[sensitivity["method"].eq("original")].set_index("variation")
expected = variation.set_index("variation")
check(np.allclose(original.loc[expected.index, "gross_revenue_per_user"], expected["arpu"]),
      "original sensitivity gross means reconcile to variation mart")
check(np.allclose(original.loc[expected.index, "net_revenue_per_user"], expected["avg_net_revenue_per_user"]),
      "original sensitivity net means reconcile to variation mart")

share = report["outliers"]["user_level"]["top_1_percent_gross_share"]
check(0 < share < 1, "top-one-percent revenue share is valid")
check((ROOT / "docs" / "data_cleaning_final_report.md").exists(), "final cleaning report exists")
print("ALL_FINAL_CLEANING_CHECKS_PASSED")
