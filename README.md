# FYP II — JustPlay Analytics Platform

هذا المجلد مستقل عن مشروع التخرج الأول. الهدف هو معالجة كامل بيانات JustPlay محلياً، بناء طبقة نتائج مجمعة، ثم عرضها في Dashboard تفاعلي دون نشر البيانات الخام.

## قواعد أساسية

- `data/raw` يحتوي نسخاً من المصدر ويعامل كطبقة قراءة فقط.
- لا تُرفع ملفات `raw` أو `processed` إلى GitHub أو أي خدمة سحابية.
- منطق التحليل النهائي يوضع داخل `src` ويغطى باختبارات داخل `tests`.
- `notebooks` للاستكشاف فقط وليست المصدر النهائي للحسابات.
- الداشبورد يقرأ الملفات المجمعة من `data/marts` ولا يقرأ CSV الخام.

## الهيكل

- `docs`: الخطة والتوثيق وتعريفات المؤشرات.
- `data/raw`: نسخ البيانات الأصلية الكاملة.
- `data/processed`: بيانات وسيطة منظفة محلياً.
- `data/marts`: نتائج مجمعة وآمنة للداشبورد.
- `src/pipeline`: التحميل والتدقيق والتنظيف والتحويل.
- `src/analytics`: المؤشرات والاختبارات الإحصائية.
- `app`: تطبيق Streamlit.
- `tests`: اختبارات الحسابات والتكامل والخصوصية.
- `logs`: سجلات وتقارير التشغيل الآلية.

## المرحلة الحالية

المرحلة 1: تدقيق البيانات الكاملة وتثبيت مصدر الحقيقة قبل بدء التحويل إلى Parquet وDuckDB.

تشغيل التدقيق:

```powershell
python src\pipeline\audit_data.py
```

المخرجات:

- `logs/data_audit.json`
- `docs/data_audit_summary.md`

## تشغيل النظام العملي

تشغيل الداشبورد محلياً:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/start_dashboard.ps1
```

فحص الجاهزية قبل الـDemo:

```powershell
python scripts/check_demo_readiness.py
```

تشغيل جميع اختبارات الجودة:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_quality_checks.ps1
```

إعادة بناء التحليلات من الطبقة المعالجة الحالية:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_pipeline.ps1
```

لإعادة معالجة ملفات CSV الخام الكبيرة أيضاً، أضف الخيار `-RebuildProcessed`. هذه الخطوة أبطأ لأنها تعالج أكثر من 12 مليون معاملة.
