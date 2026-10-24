"""Measure dashboard render time and Python peak memory with Streamlit AppTest."""

from __future__ import annotations

import json
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path

from streamlit.testing.v1 import AppTest


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app" / "streamlit_app.py"
REPORT = ROOT / "logs" / "dashboard_performance.json"
PAGES = [
    "الملخص التنفيذي",
    "كيف يعمل النظام؟",
    "مجموعات A/B",
    "Retention & Cohorts",
    "قنوات الاكتساب",
    "الإيراد والإعلانات",
    "الاختبارات الإحصائية",
    "النتائج والتوصيات",
    "المنهجية وجودة البيانات",
]


def main() -> None:
    tracemalloc.start()
    started = time.perf_counter()
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    navigation = app.sidebar.radio[0]
    timings = {}
    for page in PAGES:
        page_started = time.perf_counter()
        navigation.set_value(page)
        app.run()
        assert not app.exception, f"Dashboard page failed: {page}"
        timings[page] = round(time.perf_counter() - page_started, 4)

    total_seconds = round(time.perf_counter() - started, 4)
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "pages": len(PAGES),
        "page_render_seconds": timings,
        "total_seconds": total_seconds,
        "slowest_page_seconds": max(timings.values()),
        "python_peak_memory_mb": round(peak_bytes / 1024 / 1024, 2),
        "mart_files_total_mb": round(
            sum(path.stat().st_size for path in (ROOT / "data" / "marts").glob("*.parquet"))
            / 1024 / 1024,
            2,
        ),
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    assert report["slowest_page_seconds"] < 15
    assert report["total_seconds"] < 60
    print(json.dumps(report, ensure_ascii=True, indent=2))
    print("ALL_DASHBOARD_PERFORMANCE_CHECKS_PASSED")


if __name__ == "__main__":
    main()
