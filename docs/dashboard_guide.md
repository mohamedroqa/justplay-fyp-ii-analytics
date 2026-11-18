# دليل تشغيل Dashboard

## النسخة المنشورة

الرابط الرسمي:

<https://justplay-fyp-ii-analytics-b6v2mt5vbqpgclwg44zdnm.streamlit.app/>

## التشغيل المحلي

افتح PowerShell داخل مجلد `FYP_II` ثم نفّذ:

```powershell
streamlit run app\streamlit_app.py
```

سيفتح Streamlit رابطاً محلياً، غالباً `http://localhost:8501`.

## الصفحات المتاحة

1. الملخص التنفيذي.
2. كيف يعمل النظام؟
3. مقارنة مجموعات A/B.
4. Retention & Cohorts.
5. قنوات الاكتساب.
6. الإيراد وصيغ الإعلانات.
7. الاختبارات الإحصائية.
8. النتائج والتوصيات.
9. المنهجية وجودة البيانات.

## حماية البيانات

التطبيق يقرأ حصراً من `data/marts/*.parquet`. لا يقرأ ملفات `data/raw` أو معاملات المستخدمين، ولا تحتوي الملفات المعروضة على `user_id`.

## اختبار التشغيل

```powershell
powershell -ExecutionPolicy Bypass -File scripts\run_quality_checks.ps1
```

يفتح اختبار Smoke الصفحات التسع باستخدام أداة الاختبار الرسمية المدمجة في Streamlit ويتأكد من عدم ظهور استثناءات. قد يظهر تحذير `ScriptRunContext` عند التشغيل في وضع الاختبار المجرد؛ لا يؤثر في التطبيق الفعلي.
