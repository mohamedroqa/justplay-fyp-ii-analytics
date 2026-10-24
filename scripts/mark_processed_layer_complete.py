"""Apply the verified processed-layer completion marks to PROJECT_PROGRESS.md."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "PROJECT_PROGRESS.md"

REPLACEMENTS = {
    "| بناء طبقة البيانات المعالجة | 🟡 قيد البدء | 10% |":
        "| بناء طبقة البيانات المعالجة | ✅ منجزة كأساس قابل للتحليل | 90% |",
    "| ⬜ | تحويل ملف المستخدمين إلى Parquet | `data/processed/users.parquet` |":
        "| ✅ | تحويل ملف المستخدمين إلى Parquet | `data/processed/users.parquet` — 934,270 صفاً |",
    "| ⬜ | تصفية معاملات مستخدمي التجربة وتحويلها إلى Parquet | `data/processed/revenue_experiment.parquet` |":
        "| ✅ | تصفية معاملات مستخدمي التجربة وتحويلها إلى Parquet | `data/processed/revenue_experiment.parquet` — 11,256,114 صفاً |",
    "| ⬜ | توحيد أنواع التواريخ والأرقام والقيم المفقودة | تقرير تحويل وسجل استبعادات |":
        "| ✅ | توحيد أنواع التواريخ والأرقام والقيم المفقودة | `logs/processed_build_report.json` |",
    "| ⬜ | بناء جدول تحليلي واحد لكل مستخدم | `data/processed/user_features.parquet` |":
        "| ✅ | بناء جدول تحليلي واحد لكل مستخدم | `data/processed/user_features.parquet` — 934,270 صفاً |",
    "| ⬜ | اختبارات مطابقة المجاميع بعد التحويل | تقرير reconciliation ناجح |":
        "| ✅ | اختبارات مطابقة المجاميع بعد التحويل | 5 اختبارات نجحت عبر `tests/run_processed_checks.py` |",
    "🟡 **إنشاء طبقة Parquet للبيانات المؤهلة للتجربة، ثم بناء جدول user-level features مع اختبارات مطابقة للمجاميع.**":
        "🟡 **إنشاء Data Marts الأولى للمؤشرات العامة والـVariations والقنوات وRetention اعتماداً على جدول user-level features المعتمد.**",
}


def main() -> None:
    text = TRACKER.read_text(encoding="utf-8")
    for old, new in REPLACEMENTS.items():
        count = text.count(old)
        if count == 1:
            text = text.replace(old, new)
        elif count == 0 and new in text:
            continue
        else:
            raise ValueError(f"Expected one tracker match, found {count}: {old}")
    TRACKER.write_text(text, encoding="utf-8")
    print("PROJECT_PROGRESS.md updated")


if __name__ == "__main__":
    main()
