"""Validate dashboard-ready data marts without external test dependencies."""

from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "marts"


def close(left: float, right: float, tolerance: float = 1e-6) -> bool:
    return abs(float(left) - float(right)) < tolerance


def main() -> None:
    overall = pd.read_parquet(MARTS / "overall_kpis.parquet")
    variation = pd.read_parquet(MARTS / "variation_summary.parquet")
    channel = pd.read_parquet(MARTS / "channel_summary.parquet")
    country = pd.read_parquet(MARTS / "country_summary.parquet")
    cohorts = pd.read_parquet(MARTS / "retention_cohorts.parquet")
    ad_formats = pd.read_parquet(MARTS / "ad_format_summary.parquet")
    revenue_types = pd.read_parquet(MARTS / "revenue_type_summary.parquet")

    expected_users = 934_270
    expected_gross = 4_981_893.057763822
    expected_cashout = 1_583_184.77
    expected_net = 3_398_708.287763823

    assert len(overall) == 1
    assert int(overall.loc[0, "users"]) == expected_users
    assert close(overall.loc[0, "gross_revenue"], expected_gross)
    assert close(overall.loc[0, "cashout"], expected_cashout)
    assert close(overall.loc[0, "net_revenue"], expected_net)
    print("PASS: overall KPIs match verified processed totals")

    for name, frame in [
        ("variation", variation),
        ("channel", channel),
        ("country", country),
        ("cohorts", cohorts),
    ]:
        assert int(frame["users"].sum()) == expected_users
        assert close(frame["gross_revenue"].sum(), expected_gross)
        assert close(frame["cashout"].sum(), expected_cashout)
        assert close(frame["net_revenue"].sum(), expected_net)
        print(f"PASS: {name} mart reconciles to overall totals")

    assert close(revenue_types["total_revenue"].sum(), expected_gross)
    assert close(ad_formats["total_revenue"].sum(), overall.loc[0, "ad_revenue"])
    assert close(ad_formats["revenue_share"].sum(), 1.0)
    print("PASS: revenue type and ad format marts reconcile")

    for frame in [overall, variation, channel, country, cohorts]:
        for day in (1, 3, 7, 14, 30):
            exact = frame[f"d{day}_exact_activity_rate"].dropna()
            rolling = frame[f"d{day}_rolling_activity_rate"].dropna()
            assert exact.between(0, 1).all()
            assert rolling.between(0, 1).all()
            assert (
                frame[f"d{day}_exact_active_users"]
                <= frame[f"d{day}_rolling_active_users"]
            ).all()
            assert (
                frame[f"d{day}_rolling_active_users"]
                <= frame[f"d{day}_eligible_users"]
            ).all()
    print("PASS: all retention fields are internally valid")

    for path in MARTS.glob("*.parquet"):
        columns = pd.read_parquet(path).columns
        assert "user_id" not in columns
    print("PASS: no dashboard mart exposes user_id")
    print("ALL_DATA_MART_CHECKS_PASSED: 8")


if __name__ == "__main__":
    main()
