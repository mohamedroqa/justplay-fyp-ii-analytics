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

## الحالة الحالية

الجزء البرمجي والتحليلي مكتمل ومختبر، والداشبورد منشورة على Streamlit Cloud:

<https://justplay-fyp-ii-analytics-b6v2mt5vbqpgclwg44zdnm.streamlit.app/>

النتيجة التنفيذية: لم يثبت أي Variation تحسناً في متوسط Gross أو Net Revenue
مقارنةً بـ`default` بعد تصحيح Holm. التوصية هي الإبقاء على `default` حالياً
وإعادة اختبار `androidndorder` في تجربة تحقق مستقلة.

## مسار البيانات

```text
CSV خام
  → تدقيق الجودة ونطاق التجربة
  → Parquet معالجة وجدول واحد لكل مستخدم
  → KPIs وRetention وتحليل إحصائي
  → Data Marts مجمعة وآمنة
  → Streamlit Dashboard
```

محرك المعالجة الفعلي هو Pandas/PyArrow بقراءة دفعية وتخزين Parquet مضغوط.
تشمل المؤشرات المستخدمين بلا معاملات، وتستبعد المعاملات غير المرتبطة بمستخدمي
التجربة. Retention في هذا المشروع مبني على الأحداث المالية المتاحة وليس على
سجل جلسات مستقل.

## تشغيل النظام العملي

تثبيت الاعتماديات:

```powershell
python -m pip install -r requirements.txt
```

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

## أهم الملفات

- `src/pipeline/build_processed_data.py`: تنظيف البيانات وبناء طبقة المستخدم.
- `src/analytics/build_data_marts.py`: حساب المؤشرات والملخصات.
- `src/analytics/run_statistical_analysis.py`: اختبارات A/B.
- `app/streamlit_app.py`: صفحات الداشبورد التسع.
- `docs/Dashboard_Explanation_AR.docx`: دليل الشرح وأسئلة المناقشة.
- `PROJECT_PROGRESS.md`: سجل الإنجاز وما تبقى للتقرير والعرض.
