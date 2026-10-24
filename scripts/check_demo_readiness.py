"""Fast pre-demo health check for dependencies, outputs, privacy and local server."""

from __future__ import annotations

import importlib.metadata
import json
import py_compile
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "marts"
APP = ROOT / "app" / "streamlit_app.py"
REPORT = ROOT / "logs" / "demo_readiness.json"
REQUIRED_PACKAGES = ["pandas", "pyarrow", "numpy", "scipy", "statsmodels", "streamlit", "altair", "pytest"]
REQUIRED_MARTS = [
    "overall_kpis",
    "variation_summary",
    "channel_summary",
    "country_summary",
    "retention_cohorts",
    "ad_format_summary",
    "revenue_type_summary",
    "statistical_tests",
]


def main() -> None:
    checks: dict[str, object] = {}
    checks["packages"] = {name: importlib.metadata.version(name) for name in REQUIRED_PACKAGES}

    py_compile.compile(str(APP), doraise=True)
    checks["app_syntax"] = "pass"

    mart_rows = {}
    privacy_pass = True
    for name in REQUIRED_MARTS:
        path = MARTS / f"{name}.parquet"
        if not path.exists():
            raise FileNotFoundError(f"Missing required Data Mart: {path}")
        frame = pd.read_parquet(path)
        mart_rows[name] = len(frame)
        privacy_pass &= not any("user_id" in column.lower() for column in frame.columns)
    if not privacy_pass:
        raise AssertionError("A dashboard Data Mart exposes user_id")
    checks["mart_rows"] = mart_rows
    checks["privacy"] = "pass"

    overall = pd.read_parquet(MARTS / "overall_kpis.parquet").iloc[0]
    if int(overall["users"]) != 934_270:
        raise AssertionError("Headline user count has drifted")
    checks["headline_users"] = int(overall["users"])

    try:
        with urlopen("http://localhost:8501", timeout=2) as response:
            checks["local_server"] = f"running ({response.status})"
    except (URLError, TimeoutError):
        checks["local_server"] = "not running — use scripts/start_dashboard.ps1"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "READY",
        "checks": checks,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DEMO_READY")
    print(f"Pages data sources: {len(REQUIRED_MARTS)} marts verified")
    print(f"Privacy: {checks['privacy']}")
    print(f"Local server: {checks['local_server']}")


if __name__ == "__main__":
    main()
