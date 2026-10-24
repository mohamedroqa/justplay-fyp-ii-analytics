from pathlib import Path


tracker = Path(__file__).resolve().parents[1] / "PROJECT_PROGRESS.md"
text = tracker.read_text(encoding="utf-8")

replacements = {
    "الحالة العامة: **التحليل الإحصائي مكتمل — بدء بناء الداشبورد**":
        "الحالة العامة: **نسخة Dashboard المحلية الأولى مكتملة وتعمل**",
    "| Dashboard | ⬜ لم يبدأ | 0% |":
        "| Dashboard | ✅ النسخة المحلية الأولى تعمل | 90% |",
    "| الاختبارات والنشر | 🟡 اختبارات البيانات منجزة | 35% |":
        "| الاختبارات والنشر | 🟡 اختبارات البيانات والواجهة منجزة | 50% |",
    "| ⬜ | إنشاء الهيكل الأساسي لتطبيق Streamlit |":
        "| ✅ | إنشاء الهيكل الأساسي لتطبيق Streamlit |",
    "| ⬜ | صفحة Executive Overview |":
        "| ✅ | صفحة Executive Overview |",
    "| ⬜ | صفحة A/B Variations |":
        "| ✅ | صفحة A/B Variations |",
    "| ⬜ | صفحة Retention & Cohorts |":
        "| ✅ | صفحة Retention & Cohorts |",
    "| ⬜ | صفحة Acquisition Channels |":
        "| ✅ | صفحة Acquisition Channels |",
    "| ⬜ | صفحة Revenue & Ad Formats |":
        "| ✅ | صفحة Revenue & Ad Formats |",
    "| ⬜ | صفحة Statistical Testing |":
        "| ✅ | صفحة Statistical Testing |",
    "| ⬜ | صفحة Data Quality & Methodology |":
        "| ✅ | صفحة Data Quality & Methodology |",
    "| ⬜ | الفلاتر المشتركة والتنزيل |":
        "| 🟡 | الفلاتر والتنزيل | الفلاتر منجزة؛ تنزيل النتائج قيد الإضافة |",
    "| ⬜ | تحسين الأداء والـCaching |":
        "| ✅ | تحسين الأداء والـCaching | تحميل Data Marts عبر `st.cache_data` |",
    "| ⬜ | اختبارات أداء الداشبورد |":
        "| 🟡 | اختبارات الداشبورد | الصفحات السبع اجتازت Smoke Test؛ قياس الأداء لاحقاً |",
    "🟡 **إنشاء Dashboard محلي يقرأ ملفات Data Marts الصغيرة فقط، بدءاً من Executive Overview وA/B Variations.**":
        "🟡 **إضافة تنزيل النتائج الصغيرة، إجراء فحص بصري نهائي، ثم تجهيز نسخة التشغيل المحلية والتقرير النهائي.**",
}

missing = [old for old in replacements if old not in text]
if missing:
    raise SystemExit("Tracker update aborted; expected entries were not found")
for old, new in replacements.items():
    text = text.replace(old, new, 1)

tracker.write_text(text, encoding="utf-8")

ignore = tracker.parent / ".gitignore"
ignore_text = ignore.read_text(encoding="utf-8")
if ".test_tmp/" not in ignore_text:
    ignore.write_text(ignore_text.rstrip() + "\n.test_tmp/\n", encoding="utf-8")

print("Tracker and ignore rules updated successfully")
