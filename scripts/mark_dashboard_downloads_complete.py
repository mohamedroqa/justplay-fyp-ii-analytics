from pathlib import Path


tracker = Path(__file__).resolve().parents[1] / "PROJECT_PROGRESS.md"
text = tracker.read_text(encoding="utf-8")

replacements = {
    "الحالة العامة: **نسخة Dashboard المحلية الأولى مكتملة وتعمل**":
        "الحالة العامة: **Dashboard المحلي مكتمل وظيفياً — الفحص البصري والتقرير هما الخطوة التالية**",
    "| Dashboard | ✅ النسخة المحلية الأولى تعمل | 90% |":
        "| Dashboard | ✅ مكتمل وظيفياً وتم اختباره | 100% |",
    "| 🟡 | الفلاتر والتنزيل | الفلاتر منجزة؛ تنزيل النتائج قيد الإضافة |":
        "| ✅ | الفلاتر والتنزيل | تنزيل CSV آمن من صفحات النتائج الست |",
    "🟡 **إضافة تنزيل النتائج الصغيرة، إجراء فحص بصري نهائي، ثم تجهيز نسخة التشغيل المحلية والتقرير النهائي.**":
        "🟡 **إجراء الفحص البصري النهائي للـDashboard، ثم إضافة صوره ونتائجه إلى تقرير وعرض مشروع التخرج الثاني.**",
}

missing = [old for old in replacements if old not in text]
if missing:
    raise SystemExit("Tracker update aborted; expected entries were not found")
for old, new in replacements.items():
    text = text.replace(old, new, 1)

dashboard_test_anchor = "| 🟡 | اختبارات الداشبورد | الصفحات السبع اجتازت Smoke Test؛ قياس الأداء لاحقاً |"
replacement = (
    "| ✅ | اختبارات الداشبورد الوظيفية | الصفحات السبع اجتازت Smoke Test |\n"
    "| ✅ | اختبارات تنزيل النتائج | صفحات النتائج الست اجتازت اختبار التنزيل الآمن |\n"
    "| ⬜ | قياس أداء الداشبورد | زمن التحميل والذاكرة |"
)
if dashboard_test_anchor in text:
    text = text.replace(dashboard_test_anchor, replacement, 1)

tracker.write_text(text, encoding="utf-8")
print("Dashboard completion recorded successfully")
