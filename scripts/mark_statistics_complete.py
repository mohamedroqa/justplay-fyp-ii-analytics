from pathlib import Path


tracker = Path(__file__).resolve().parents[1] / "PROJECT_PROGRESS.md"
text = tracker.read_text(encoding="utf-8")

replacements = {
    "الحالة العامة: **طبقة Data Marts الأساسية مكتملة — التحليل الإحصائي هو الخطوة التالية**":
        "الحالة العامة: **التحليل الإحصائي مكتمل — بدء بناء الداشبورد**",
    "| تعريف وحساب KPIs | 🟡 الحسابات الأساسية منجزة والتوثيق جارٍ | 65% |":
        "| تعريف وحساب KPIs | ✅ منجزة وموثقة | 100% |",
    "| التحليل الإحصائي | ⬜ لم يبدأ | 0% |":
        "| التحليل الإحصائي | ✅ منجز وتم التحقق منه | 100% |",
    "| Data Marts | ✅ الأساسية منجزة ومتحقق منها | 90% |":
        "| Data Marts | ✅ منجزة ومتحقق منها | 100% |",
    "| الاختبارات والنشر | ⬜ لم تبدأ | 0% |":
        "| الاختبارات والنشر | 🟡 اختبارات البيانات منجزة | 35% |",
    "| ⬜ | تثبيت قاموس البيانات | `docs/data_dictionary.md` |":
        "| ✅ | تثبيت قاموس البيانات | `docs/data_dictionary.md` |",
    "| ⬜ | تثبيت تعريفات Gross Revenue وCashout وNet Revenue | `docs/kpi_definitions.md` |":
        "| ✅ | تثبيت تعريفات Gross Revenue وCashout وNet Revenue | `docs/kpi_definitions.md` |",
    "| ⬜ | إحصاءات وصفية كاملة لكل Variation | متوسط، وسيط، انحراف، فواصل ربعية |":
        "| ✅ | إحصاءات وصفية كاملة لكل Variation | `variation_descriptive.parquet` |",
    "| ⬜ | Welch t-test | كل Variation مقابل default والمقارنات الثانوية |":
        "| ✅ | Welch t-test | كل Variation مقابل `default` |",
    "| ⬜ | Mann–Whitney U | تحليل حساسية لتوزيع الإيراد المنحرف |":
        "| ✅ | Mann–Whitney U | تحليل حساسية لتوزيع الإيراد المنحرف |",
    "| ⬜ | Effect Sizes | Cohen’s d أو المقياس الأنسب |":
        "| ✅ | Effect Sizes | Cohen’s d وRank-biserial وRisk Difference |",
    "| ⬜ | Confidence Intervals | فواصل ثقة للفروقات والمؤشرات |":
        "| ✅ | Confidence Intervals | فواصل ثقة 95% للفروق |",
    "| ⬜ | Multiple Comparison Correction | Holm أو Benjamini–Hochberg |":
        "| ✅ | Multiple Comparison Correction | Holm داخل كل مؤشر وعائلة اختبار |",
    "| ⬜ | صياغة الاستنتاجات | وصفي، دال إحصائياً، وذو أثر عملي |":
        "| ✅ | صياغة الاستنتاجات | `docs/statistical_analysis_summary.md` |",
    "| ⬜ | نتائج الاختبارات | `data/marts/statistical_tests.parquet` |":
        "| ✅ | نتائج الاختبارات | `data/marts/statistical_tests.parquet` — 48 اختباراً |",
    "🟡 **تثبيت قاموس البيانات وتعريفات KPIs، ثم تنفيذ التحليل الإحصائي للـVariations وإنشاء `statistical_tests.parquet`.**":
        "🟡 **إنشاء Dashboard محلي يقرأ ملفات Data Marts الصغيرة فقط، بدءاً من Executive Overview وA/B Variations.**",
}

missing = [old for old in replacements if old not in text]
if missing:
    raise SystemExit("Tracker update aborted; expected entries were not found")
for old, new in replacements.items():
    text = text.replace(old, new, 1)

tracker.write_text(text, encoding="utf-8")
print("Tracker updated successfully")
