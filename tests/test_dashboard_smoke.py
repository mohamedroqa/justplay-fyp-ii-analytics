"""Smoke tests for every dashboard page using Streamlit's AppTest."""

from pathlib import Path

from streamlit.testing.v1 import AppTest


APP = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
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


def test_all_dashboard_pages_render() -> None:
    app = AppTest.from_file(str(APP), default_timeout=30).run()
    assert not app.exception
    navigation = app.sidebar.radio[0]
    for page in PAGES:
        navigation.set_value(page)
        app.run()
        assert not app.exception, f"Dashboard page failed: {page}"
