from pathlib import Path


tracker = Path(__file__).resolve().parents[1] / "PROJECT_PROGRESS.md"
text = tracker.read_text(encoding="utf-8")

replacements = {
    "| بناء طبقة البيانات المعالجة | ✅ منجزة كأساس قابل للتحليل | 90% |":
        "| بناء طبقة البيانات المعالجة | ✅ منجزة وتم إغلاق التنظيف | 100% |",
    "| ⬜ | فحص التكرار الكامل لصفوف المعاملات | عدد التكرارات وقاعدة التعامل معها |":
        "| ✅ | فحص التكرار الكامل لصفوف المعاملات | فُحص 11,256,114 صفاً — صفر تكرار |",
}

missing = [old for old in replacements if old not in text]
if missing:
    raise SystemExit("Tracker update aborted; expected entries were not found")
for old, new in replacements.items():
    text = text.replace(old, new, 1)

processed_anchor = "| ✅ | اختبارات مطابقة المجاميع بعد التحويل | 5 اختبارات نجحت عبر `tests/run_processed_checks.py` |"
processed_extra = (
    "\n| ✅ | تحليل القيم المتطرفة دون حذفها | `docs/data_cleaning_final_report.md` |"
    "\n| ✅ | تحليل حساسية P99 حسب Variation | `data/marts/outlier_sensitivity.parquet` — 15 صفاً |"
    "\n| ✅ | اختبارات إغلاق التنظيف | `tests/run_cleaning_final_checks.py` — جميعها نجحت |"
)
if "اختبارات إغلاق التنظيف" not in text:
    text = text.replace(processed_anchor, processed_anchor + processed_extra, 1)

marts_anchor = "| ✅ | نتائج أنواع الإيراد | `data/marts/revenue_type_summary.parquet` — 3 صفوف |"
if "نتائج تحليل حساسية القيم المتطرفة" not in text:
    text = text.replace(
        marts_anchor,
        marts_anchor + "\n| ✅ | نتائج تحليل حساسية القيم المتطرفة | `data/marts/outlier_sensitivity.parquet` — 15 صفاً |",
        1,
    )

tracker.write_text(text, encoding="utf-8")
print("Cleaning completion recorded successfully")
