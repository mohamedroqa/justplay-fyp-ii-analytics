# قاموس البيانات المعتمد

تاريخ الاعتماد: **13 أكتوبر 2026**

## 1. جدول المستخدمين `data/processed/users.parquet`

مستوى الصف: مستخدم واحد في تجربة A/B. عدد الصفوف: **934,270**.

| الحقل | النوع | الوصف |
|---|---|---|
| `user_id` | string | معرف المستخدم؛ للاستخدام المحلي فقط ولا يدخل ملفات النشر |
| `variation` | string | مجموعة تجربة A/B |
| `assignment_dt` | datetime | وقت إسناد المستخدم إلى المجموعة |
| `install_dt` | datetime | وقت تثبيت التطبيق |
| `country_code` | string | رمز الدولة بعد التوحيد؛ `us` أو `ca` |
| `platform` | string | منصة الجهاز بعد التوحيد |
| `is_ad_tracking_limited` | boolean | هل تتبع الإعلانات محدود |
| `os_version` | string | إصدار نظام التشغيل كما ورد في المصدر |
| `os_version_clean` | string | إصدار النظام بعد تحويل القيمة المفقودة إلى `Unknown` |
| `channel` | string | قناة الاكتساب الأصلية |
| `channel_clean` | string | قناة الاكتساب بعد تحويل القيمة المفقودة إلى `Unknown` |
| `assigned` | int8 | مؤشر الإسناد كما ورد في المصدر |
| `activated` | int8 | مؤشر التفعيل كما ورد في المصدر |

## 2. معاملات التجربة `data/processed/revenue_experiment.parquet`

مستوى الصف: حدث مالي واحد مرتبط بمستخدم مؤهل. عدد الصفوف: **11,256,114**.

| الحقل | النوع | الوصف |
|---|---|---|
| `source_row_id` | int64 | رقم الصف من المصدر للتتبع المحلي |
| `user_id` | string | مفتاح الربط مع جدول المستخدمين؛ غير مخصص للنشر |
| `created_at` | datetime | وقت الحدث المالي |
| `revenue_amount` | float64 | قيمة الإيراد في الحدث |
| `cashout_amount` | float64 | قيمة الـCashout في الحدث |
| `earning_amount` | float64 | قيمة الأرباح المسجلة في المصدر |
| `cashout_transactions` | int64 | عدد معاملات Cashout المسجلة في الحدث |
| `ad_unit_format` | string | صيغة الإعلان الأصلية |
| `ad_unit_format_clean` | string | صيغة الإعلان المنظفة؛ `Not Applicable` لغير الإعلانات |
| `revenue_type` | string | نوع الإيراد، مثل `ad` أو `offerwall` |

## 3. خصائص المستخدم `data/processed/user_features.parquet`

مستوى الصف: مستخدم واحد مع خصائصه ومجاميعه المالية. عدد الصفوف: **934,270**. يحتوي جميع حقول جدول المستخدمين، إضافة إلى الحقول التالية:

| الحقل | النوع | الوصف |
|---|---|---|
| `total_revenue` | float64 | مجموع إيراد المستخدم |
| `total_cashout` | float64 | مجموع Cashout للمستخدم |
| `net_revenue` | float64 | `total_revenue - total_cashout` |
| `total_earnings` | float64 | مجموع `earning_amount` |
| `cashout_transactions` | int64 | مجموع عدد معاملات Cashout |
| `transaction_count` | int64 | عدد الأحداث المالية للمستخدم |
| `ad_revenue` | float64 | إيراد الإعلانات للمستخدم |
| `offerwall_revenue` | float64 | إيراد Offerwall للمستخدم |
| `is_monetized` | boolean | هل `total_revenue > 0` |
| `has_cashout` | boolean | هل `total_cashout > 0` |
| `first_activity_dt` | datetime | أول حدث مالي مسجل للمستخدم |
| `last_activity_dt` | datetime | آخر حدث مالي مسجل للمستخدم |
| `max_activity_day` | int32 | أبعد يوم نشاط مالي بعد التثبيت؛ `-1` عند عدم وجود نشاط |
| `days_observed` | int64 | الأيام بين التثبيت ونهاية نافذة الرصد |
| `eligible_d{n}` | boolean | هل اكتملت للمستخدم نافذة اليوم n |
| `exact_activity_d{n}` | boolean | هل وُجد حدث في اليوم n تماماً |
| `rolling_activity_d{n}_plus` | boolean | هل وُجد حدث في اليوم n أو بعده |

القيم الممكنة لـ`n`: **1، 3، 7، 14، 30**.

## 4. Data Marts

| الملف | مستوى الصف | يحتوي معرفات فردية؟ |
|---|---|---|
| `overall_kpis.parquet` | ملخص عام واحد | لا |
| `variation_summary.parquet` | Variation واحدة | لا |
| `channel_summary.parquet` | قناة اكتساب واحدة | لا |
| `country_summary.parquet` | دولة واحدة | لا |
| `platform_summary.parquet` | منصة واحدة | لا |
| `os_version_summary.parquet` | إصدار نظام واحد | لا |
| `user_value_segments.parquet` | شريحة قيمة مجمعة | لا |
| `retention_cohorts.parquet` | أسبوع تثبيت × Variation | لا |
| `ad_format_summary.parquet` | صيغة إعلان واحدة | لا |
| `revenue_type_summary.parquet` | نوع إيراد واحد | لا |

### تعريف شرائح قيمة المستخدمين

تعتمد الشرائح على `Net Revenue` لكل مستخدم قبل التجميع، ثم تُحذف جميع المعرفات الفردية من المخرج:

- `negative_value`: صافي الإيراد أقل من صفر.
- `no_revenue`: لا يوجد Gross Revenue، بعد فصل الحالات السالبة.
- `low_value`: صافي الإيراد حتى Median المستخدمين ذوي القيمة الموجبة.
- `medium_value`: أعلى من Median وحتى P90 للمستخدمين ذوي القيمة الموجبة.
- `high_value`: أعلى من P90 للمستخدمين ذوي القيمة الموجبة.

الحدود محسوبة من نافذة البيانات الحالية، ولذلك تستخدم للتحليل التجميعي ولا تمثل حكماً دائماً على مستخدم بعينه.

## ملاحظة القيم المفقودة

القيم النصية `missing` في `channel` و`os_version` تحولت إلى `Unknown` في الحقول المنظفة مع إبقاء الحقول الأصلية للتتبع. لا تُحذف هذه السجلات من التحليل.
