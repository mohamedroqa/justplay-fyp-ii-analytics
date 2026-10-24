"""Verify that every results page exposes a safe CSV download."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
RESULT_PAGES = [
    "الملخص التنفيذي",
    "مجموعات A/B",
    "Retention & Cohorts",
    "قنوات الاكتساب",
    "الإيراد والإعلانات",
    "الاختبارات الإحصائية",
]


app = AppTest.from_file(str(APP), default_timeout=30).run()
navigation = app.sidebar.radio[0]
for page_number, page in enumerate(RESULT_PAGES, start=1):
    navigation.set_value(page)
    app.run()
    assert not app.exception, f"Page failed: {page}"
    assert len(app.get("download_button")) >= 1, f"No download exists on page: {page}"
    print(f"PASS: safe result download exists on page {page_number}")

print("ALL_DASHBOARD_DOWNLOAD_CHECKS_PASSED")
