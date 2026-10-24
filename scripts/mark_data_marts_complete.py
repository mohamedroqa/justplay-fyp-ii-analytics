from pathlib import Path


tracker = Path(__file__).resolve().parents[1] / "PROJECT_PROGRESS.md"
text = tracker.read_text(encoding="utf-8")

replacements = {
    "الحالة العامة: **المرحلة الأولى مكتملة — بدء تجهيز طبقة البيانات المعالجة**":
        "الحالة العامة: **طبقة Data Marts الأساسية مكتملة — التحليل الإحصائي هو الخطوة التالية**",
    "| تعريف وحساب KPIs | ⬜ لم تبدأ | 0% |":
        "| تعريف وحساب KPIs | 🟡 الحسابات الأساسية منجزة والتوثيق جارٍ | 65% |",
    "| Retention وCohorts | ⬜ لم تبدأ | 0% |":
        "| Retention وCohorts | ✅ الحسابات والجداول الأساسية منجزة | 85% |",
    "| Data Marts | ⬜ لم تبدأ | 0% |":
        "| Data Marts | ✅ الأساسية منجزة ومتحقق منها | 90% |",
    "| ⬜ | حساب ARPU على جميع المستخدمين المؤهلين | اختبار وحقل موثق |":
        "| ✅ | حساب ARPU على جميع المستخدمين المؤهلين | `overall_kpis.parquet` — $5.3324 |",
    "| ⬜ | حساب Average Net Revenue per User | اختبار وحقل موثق |":
        "| ✅ | حساب Average Net Revenue per User | `overall_kpis.parquet` — $3.6378 |",
    "| ⬜ | حساب Activation Rate | اختبار وحقل موثق |":
        "| ✅ | حساب Activation Rate | محسوب في ملفات المؤشرات المجمعة |",
    "| ⬜ | حساب Monetization Rate | اختبار وحقل موثق |":
        "| ✅ | حساب Monetization Rate | محسوب في ملفات المؤشرات المجمعة |",
    "| ⬜ | تحديد eligible population لكل نافذة زمنية | قواعد D1/D3/D7/D14/D30 |":
        "| ✅ | تحديد eligible population لكل نافذة زمنية | مطبق على D1/D3/D7/D14/D30 مع Right Censoring |",
    "| ⬜ | حساب Exact-day activity retention | نتائج D1/D3/D7/D14/D30 |":
        "| ✅ | حساب Exact-day activity retention | نتائج D1/D3/D7/D14/D30 محفوظة |",
    "| ⬜ | حساب Rolling activity Dn+ بشكل منفصل | نتائج موثقة دون تسميتها Exact Retention |":
        "| ✅ | حساب Rolling activity Dn+ بشكل منفصل | نتائج D1/D3/D7/D14/D30 محفوظة منفصلة |",
    "| ⬜ | معالجة Right Censoring | استبعاد غير مكتملي نافذة الرصد من مقام Dn |":
        "| ✅ | معالجة Right Censoring | استبعاد غير مكتملي نافذة الرصد من مقام Dn |",
    "| ⬜ | إنشاء Cohorts حسب أسبوع التثبيت | جداول ومنحنيات Cohort |":
        "| ✅ | إنشاء Cohorts حسب أسبوع التثبيت | `data/marts/retention_cohorts.parquet` — 45 صفاً |",
    "| ⬜ | مقارنة Retention حسب Variation والقناة والدولة | Data Mart موحد |":
        "| 🟡 | مقارنة Retention حسب Variation والقناة والدولة | Variation/Cohort منجز؛ توسعة القناة والدولة لاحقاً |",
    "| ⬜ | الملخص العام | `data/marts/overall_kpis.parquet` |":
        "| ✅ | الملخص العام | `data/marts/overall_kpis.parquet` — صف واحد |",
    "| ⬜ | نتائج الـVariations | `data/marts/variation_summary.parquet` |":
        "| ✅ | نتائج الـVariations | `data/marts/variation_summary.parquet` — 5 صفوف |",
    "| ⬜ | نتائج القنوات | `data/marts/channel_summary.parquet` |":
        "| ✅ | نتائج القنوات | `data/marts/channel_summary.parquet` — 19 صفاً |",
    "| ⬜ | نتائج Retention وCohorts | `data/marts/retention_cohorts.parquet` |":
        "| ✅ | نتائج Retention وCohorts | `data/marts/retention_cohorts.parquet` — 45 صفاً |",
    "| ⬜ | نتائج Ad Formats | `data/marts/ad_format_summary.parquet` |":
        "| ✅ | نتائج Ad Formats | `data/marts/ad_format_summary.parquet` — 4 صفوف |",
    "| ⬜ | فحص الخصوصية | التأكد من عدم وجود user_id في ملفات النشر |":
        "| ✅ | فحص الخصوصية | لا يوجد `user_id` في أي Data Mart |",
    "🟡 **إنشاء Data Marts الأولى للمؤشرات العامة والـVariations والقنوات وRetention اعتماداً على جدول user-level features المعتمد.**":
        "🟡 **تثبيت قاموس البيانات وتعريفات KPIs، ثم تنفيذ التحليل الإحصائي للـVariations وإنشاء `statistical_tests.parquet`.**",
}

missing = [old for old in replacements if old not in text]
if missing:
    raise SystemExit("Tracker update aborted; missing expected text:\n" + "\n".join(missing))

for old, new in replacements.items():
    text = text.replace(old, new, 1)

anchor = "| ⬜ | نتائج الاختبارات | `data/marts/statistical_tests.parquet` |"
extra = (
    "| ✅ | نتائج الدول | `data/marts/country_summary.parquet` — صفان |\n"
    "| ✅ | نتائج أنواع الإيراد | `data/marts/revenue_type_summary.parquet` — 3 صفوف |\n"
)
text = text.replace(anchor, extra + anchor, 1)

privacy_anchor = "| ⬜ | اختبارات الخصوصية وغياب المعرفات الفردية |"
text = text.replace(
    privacy_anchor,
    "| ✅ | اختبارات الخصوصية وغياب المعرفات الفردية في Data Marts |",
    1,
)

tracker.write_text(text, encoding="utf-8")
print(f"Updated {tracker}")
