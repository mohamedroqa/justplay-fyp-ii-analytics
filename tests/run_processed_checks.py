"""Dependency-free runner for the processed output assertions."""

from test_processed_outputs import (
    test_build_scope_matches_audit,
    test_no_invalid_or_preinstall_activity,
    test_parquet_row_counts,
    test_retention_flags_and_summary_are_consistent,
    test_user_feature_financial_reconciliation,
)


CHECKS = [
    test_parquet_row_counts,
    test_build_scope_matches_audit,
    test_user_feature_financial_reconciliation,
    test_retention_flags_and_summary_are_consistent,
    test_no_invalid_or_preinstall_activity,
]


if __name__ == "__main__":
    for check in CHECKS:
        check()
        print(f"PASS: {check.__name__}")
    print(f"ALL_CHECKS_PASSED: {len(CHECKS)}")
