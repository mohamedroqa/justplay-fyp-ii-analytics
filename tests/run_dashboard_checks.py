"""Run the dashboard smoke test without requiring the pytest executable."""

from test_dashboard_smoke import test_all_dashboard_pages_render


if __name__ == "__main__":
    test_all_dashboard_pages_render()
    print("PASS: all dashboard pages render without exceptions")
    print("ALL_DASHBOARD_CHECKS_PASSED")
