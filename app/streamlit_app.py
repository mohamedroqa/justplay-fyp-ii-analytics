"""Local dashboard for the FYP II JustPlay analysis.

The app reads only aggregated Data Marts; it never reads raw transactions or
publishes user-level identifiers.
"""

from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parents[1]
MARTS = ROOT / "data" / "marts"

st.set_page_config(
    page_title="JustPlay | FYP II Analytics",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&display=swap');
      :root {
        --ink: #172033; --muted: #667085; --primary: #5B5BD6;
        --primary-soft: #EEEEFF; --teal: #18A999; --surface: #FFFFFF;
        --line: #E7EAF0;
      }
      html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: "Cairo", "Segoe UI", sans-serif;
      }
      [data-testid="stAppViewContainer"] {
        background: linear-gradient(180deg, #F7F8FC 0%, #FBFCFE 100%);
        color: var(--ink);
      }
      [data-testid="stHeader"] {background: transparent;}
      .block-container {max-width: 1440px; padding-top: 2.1rem; padding-bottom: 3rem;}
      h1, h2, h3, p, label, [data-testid="stMetricLabel"], .stCaption {
        direction: rtl; text-align: right;
      }
      h1 {font-size: 2rem !important; font-weight: 800 !important; color: var(--ink);}
      h2, h3 {color: var(--ink); font-weight: 700 !important;}
      [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #17172B 0%, #242445 100%);
        border-left: 0;
      }
      [data-testid="stSidebar"] * {color: #F5F6FF !important;}
      [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: .68rem .8rem; margin: .2rem 0; border-radius: .75rem;
        transition: background .18s ease;
      }
      [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: rgba(255,255,255,.08);
      }
      [data-testid="stSidebar"] [data-baseweb="radio"] > div:first-child {
        background-color: #8888FF;
      }
      [data-testid="stMetric"] {
        background: var(--surface); border: 1px solid var(--line);
        border-radius: 1rem; padding: 1rem 1.1rem; min-height: 118px;
        box-shadow: 0 8px 24px rgba(25, 34, 58, .055);
      }
      [data-testid="stMetricLabel"] {color: var(--muted); font-weight: 600;}
      [data-testid="stMetricValue"] {
        direction: ltr; text-align: right; color: var(--ink); font-weight: 800;
        font-size: clamp(1.45rem, 2.2vw, 2.15rem);
      }
      [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--surface); border-color: var(--line) !important;
        border-radius: 1rem; box-shadow: 0 8px 24px rgba(25, 34, 58, .045);
      }
      [data-testid="stDataFrame"] {
        border: 1px solid var(--line); border-radius: .85rem; overflow: hidden;
      }
      .stButton button, .stDownloadButton button {
        border-radius: .7rem; border: 1px solid #D6D8E3; font-weight: 700;
      }
      .stDownloadButton button:hover {border-color: var(--primary); color: var(--primary);}
      .page-head {
        direction: rtl; text-align: right; padding: 1.25rem 1.5rem;
        margin-bottom: 1.35rem; border: 1px solid #E5E4FF; border-radius: 1.15rem;
        background: radial-gradient(circle at 5% 20%, rgba(91,91,214,.13), transparent 28%),
                    linear-gradient(120deg, #FFFFFF 0%, #F5F4FF 100%);
      }
      .page-kicker {
        display: inline-block; padding: .24rem .65rem; margin-bottom: .45rem;
        border-radius: 999px; background: var(--primary-soft); color: #4A49B8;
        font-size: .76rem; font-weight: 800;
      }
      .page-title {font-size: 1.9rem; font-weight: 800; color: var(--ink); line-height: 1.45;}
      .page-subtitle {color: var(--muted); font-size: .96rem; margin-top: .25rem;}
      .section-label {
        direction: rtl; text-align: right; font-size: 1.05rem; font-weight: 800;
        color: var(--ink); margin: .8rem 0 .55rem;
      }
      .method-note, .insight-note {
        direction: rtl; text-align: right; padding: .9rem 1rem;
        border-radius: .8rem; line-height: 1.9;
      }
      .method-note {background: #F2F4FF; border-right: 4px solid var(--primary);}
      .insight-note {background: #ECFAF7; border-right: 4px solid var(--teal);}
      .sidebar-brand {padding: .8rem .35rem 1rem; direction: rtl; text-align: right;}
      .sidebar-brand .logo {font-size: 1.35rem; font-weight: 800;}
      .sidebar-brand .meta {font-size: .76rem; opacity: .68; margin-top: .2rem;}
      .privacy-pill {
        direction: rtl; text-align: center; margin-top: .7rem; padding: .55rem .65rem;
        border: 1px solid rgba(255,255,255,.13); border-radius: .7rem;
        color: rgba(255,255,255,.75); font-size: .72rem;
      }
      .story-grid, .decision-grid {
        display: grid; direction: rtl; gap: .75rem; margin: .6rem 0 1.2rem;
      }
      .story-grid {grid-template-columns: repeat(4, 1fr);}
      .decision-grid {grid-template-columns: repeat(3, 1fr);}
      .story-step, .decision-card {
        background: #FFFFFF; border: 1px solid var(--line); border-radius: .9rem;
        padding: .9rem 1rem; text-align: right;
        box-shadow: 0 5px 16px rgba(25, 34, 58, .035);
      }
      .story-step .number {
        width: 1.7rem; height: 1.7rem; display: inline-flex; align-items: center;
        justify-content: center; border-radius: 50%; background: var(--primary-soft);
        color: var(--primary); font-weight: 800; margin-left: .35rem;
      }
      .story-step strong, .decision-card strong {display: block; color: var(--ink);}
      .story-step span, .decision-card span {color: var(--muted); font-size: .82rem; line-height: 1.7;}
      .decision-card.go {border-top: 4px solid var(--teal);}
      .decision-card.hold {border-top: 4px solid #F59E0B;}
      .decision-card.stop {border-top: 4px solid #EF6A8A;}
      .recommendation-hero {
        direction: rtl; text-align: right; padding: 1.15rem 1.25rem;
        border-radius: 1rem; color: white;
        background: linear-gradient(125deg, #4B4BC4 0%, #6B5CE7 55%, #18A999 140%);
        margin-bottom: 1rem;
      }
      .recommendation-hero .big {font-size: 1.25rem; font-weight: 800; margin-bottom: .3rem;}
      .recommendation-hero .small {opacity: .88; line-height: 1.8;}
      .pipeline-flow {
        display: grid; grid-template-columns: repeat(5, 1fr); gap: .65rem;
        direction: rtl; margin: .7rem 0 1.3rem;
      }
      .pipeline-node {
        position: relative; background: #FFFFFF; border: 1px solid var(--line);
        border-radius: .9rem; padding: 1rem .8rem; text-align: center;
        min-height: 122px;
      }
      .pipeline-node:not(:last-child)::after {
        content: "←"; position: absolute; left: -.62rem; top: 40%; z-index: 2;
        width: 1.2rem; height: 1.2rem; border-radius: 50%; background: #5B5BD6;
        color: white; font-weight: 800; line-height: 1.15rem;
      }
      .pipeline-node .icon {font-size: 1.45rem; display: block; margin-bottom: .25rem;}
      .pipeline-node strong {display: block; color: var(--ink); margin-bottom: .2rem;}
      .pipeline-node span {font-size: .75rem; line-height: 1.55; color: var(--muted);}
      .tech-tag {
        display: inline-block; direction: ltr; padding: .18rem .5rem; margin: .12rem;
        border-radius: .45rem; background: #F0F1F6; color: #475467;
        font-size: .75rem; font-family: Consolas, monospace;
      }
      @media (max-width: 900px) {
        .story-grid, .decision-grid {grid-template-columns: 1fr;}
        .pipeline-flow {grid-template-columns: 1fr;}
        .pipeline-node:not(:last-child)::after {content: "↓"; left: 48%; top: auto; bottom: -.62rem;}
      }
      hr {border-color: var(--line);}
    </style>
    """,
    unsafe_allow_html=True,
)


CHART_COLORS = ["#5B5BD6", "#18A999", "#F59E0B", "#EF6A8A", "#7C3AED"]


def page_header(title: str, subtitle: str, kicker: str) -> None:
    st.markdown(
        f"""
        <div class="page-head">
          <div class="page-kicker">{kicker}</div>
          <div class="page-title">{title}</div>
          <div class="page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str) -> None:
    st.markdown(f'<div class="section-label">{text}</div>', unsafe_allow_html=True)


def polish_chart(chart: alt.Chart) -> alt.Chart:
    return (
        chart.configure_view(strokeOpacity=0)
        .configure_axis(
            gridColor="#EAECF2", domain=False, tickColor="#D8DCE6",
            labelColor="#667085", titleColor="#475467",
            labelFont="Cairo", titleFont="Cairo",
        )
        .configure_legend(labelFont="Cairo", titleFont="Cairo", orient="bottom")
    )


@st.cache_data(show_spinner=False)
def load_mart(name: str) -> pd.DataFrame:
    path = MARTS / f"{name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Missing required Data Mart: {path}")
    return pd.read_parquet(path)


def money(value: float) -> str:
    return f"${value:,.2f}"


def pct(value: float) -> str:
    return f"{value:.2%}"


def download_csv(frame: pd.DataFrame, filename: str, label: str = "تنزيل النتائج CSV") -> None:
    """Offer only aggregated, identifier-free tables for download."""
    if any("user_id" in column.lower() for column in frame.columns):
        raise ValueError("Dashboard downloads must not expose user identifiers")
    st.download_button(
        label=label,
        data=frame.to_csv(index=False).encode("utf-8-sig"),
        file_name=filename,
        mime="text/csv",
        width="content",
    )


def page_overview() -> None:
    overall = load_mart("overall_kpis").iloc[0]
    variations = load_mart("variation_summary")

    page_header(
        "لوحة تحليل أداء JustPlay",
        "من البيانات الخام إلى قرار تجاري واضح: هل حسّنت أي مجموعة التجربة أداء المنتج؟",
        "FYP II · EXECUTIVE DASHBOARD",
    )

    section_label("قصة المشروع في أربع خطوات")
    st.markdown(
        """
        <div class="story-grid">
          <div class="story-step"><span class="number">1</span><strong>المشكلة</strong><span>وجود خمس تجارب يحتاج إلى قرار مبني على دليل، لا على المتوسطات الظاهرية.</span></div>
          <div class="story-step"><span class="number">2</span><strong>التحليل</strong><span>تدقيق البيانات، بناء KPIs، تحليل Cohorts وإجراء 48 اختبارًا إحصائيًا.</span></div>
          <div class="story-step"><span class="number">3</span><strong>النتيجة</strong><span>لا يوجد فائز مالي مثبت، مع إشارات سلوكية صغيرة لبعض المجموعات.</span></div>
          <div class="story-step"><span class="number">4</span><strong>القيمة</strong><span>تجنب إطلاق تغيير غير مثبت وتوجيه التجربة التالية نحو المرشح الأكثر وعدًا.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_label("مؤشرات الأداء الرئيسية")
    primary_cols = st.columns(3, gap="medium")
    primary_cols[0].metric("المستخدمون", f"{int(overall['users']):,}")
    primary_cols[1].metric("Gross Revenue", money(overall["gross_revenue"]))
    primary_cols[2].metric("Net Revenue", money(overall["net_revenue"]))
    secondary_cols = st.columns(3, gap="medium")
    secondary_cols[0].metric("Cashout", money(overall["cashout"]))
    secondary_cols[1].metric("ARPU", money(overall["arpu"]))
    secondary_cols[2].metric("Average Net / User", money(overall["avg_net_revenue_per_user"]))

    section_label("صورة الأداء")
    left, right = st.columns([1.55, 1], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("#### صافي الإيراد حسب المجموعة")
            chart = (
                alt.Chart(variations)
                .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=46)
                .encode(
                    x=alt.X("variation:N", title=None, sort="-y", axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("net_revenue:Q", title="Net Revenue ($)"),
                    color=alt.condition(
                        alt.datum.variation == "default",
                        alt.value("#5B5BD6"),
                        alt.value("#AAA9EE"),
                    ),
                    tooltip=[
                        alt.Tooltip("variation:N", title="المجموعة"),
                        alt.Tooltip("users:Q", title="المستخدمون", format=","),
                        alt.Tooltip("net_revenue:Q", title="صافي الإيراد", format="$,.2f"),
                    ],
                )
            )
            st.altair_chart(polish_chart(chart), width="stretch")
    with right:
        with st.container(border=True):
            st.markdown("#### جودة قاعدة المستخدمين")
            st.metric("Activation Rate", pct(overall["activation_rate"]))
            st.metric("Monetization Rate", pct(overall["monetization_rate"]))
        st.markdown(
            '<div class="insight-note"><strong>ملاحظة منهجية:</strong> المؤشرات تشمل المستخدمين '
            "بلا معاملات في المقام، وتستبعد معاملات المستخدمين خارج تجربة A/B.</div>",
            unsafe_allow_html=True,
        )
    st.write("")
    download_csv(variations, "variation_summary.csv", "تنزيل ملخص المجموعات")


def page_system_flow() -> None:
    page_header(
        "كيف يعمل النظام؟",
        "مسار عملي قابل لإعادة التشغيل يحوّل ملايين السجلات إلى قرار منتج واضح وآمن.",
        "SYSTEM WORKFLOW",
    )

    section_label("تدفق البيانات من المصدر إلى القرار")
    st.markdown(
        """
        <div class="pipeline-flow">
          <div class="pipeline-node"><span class="icon">🗂️</span><strong>البيانات الخام</strong><span>934,270 مستخدمًا<br>12,985,983 معاملة</span></div>
          <div class="pipeline-node"><span class="icon">🔍</span><strong>التدقيق والنطاق</strong><span>فحص الجودة وربط معاملات مستخدمي تجربة A/B فقط</span></div>
          <div class="pipeline-node"><span class="icon">⚙️</span><strong>المعالجة</strong><span>Parquet منظم وجدول خصائص واحد لكل مستخدم</span></div>
          <div class="pipeline-node"><span class="icon">📊</span><strong>التحليل</strong><span>KPIs وCohorts و48 اختبارًا إحصائيًا</span></div>
          <div class="pipeline-node"><span class="icon">🎯</span><strong>القرار</strong><span>Data Marts آمنة وDashboard وتوصية قابلة للتنفيذ</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    code_col, value_col = st.columns(2, gap="large")
    with code_col:
        with st.container(border=True):
            st.markdown("#### مكوّنات النظام")
            st.markdown(
                """
                - `src/pipeline`: التدقيق والتنظيف والتحويل.
                - `src/analytics`: المؤشرات والاختبارات الإحصائية.
                - `data/marts`: النتائج الصغيرة التي تقرأها الواجهة.
                - `app`: تطبيق Streamlit التفاعلي.
                - `tests`: اختبارات الوحدة والتكامل والثبات والجودة.
                """
            )
            st.markdown(
                '<span class="tech-tag">Python</span><span class="tech-tag">Pandas</span>'
                '<span class="tech-tag">PyArrow</span><span class="tech-tag">SciPy</span>'
                '<span class="tech-tag">Streamlit</span><span class="tech-tag">Altair</span>',
                unsafe_allow_html=True,
            )
    with value_col:
        with st.container(border=True):
            st.markdown("#### لماذا هذه المعمارية؟")
            st.markdown(
                """
                - معالجة الملف الكبير مرة واحدة بدل تحميله داخل الداشبورد.
                - فصل البيانات الخام عن طبقة العرض لحماية الخصوصية.
                - إمكانية إعادة تشغيل الحسابات والتحقق منها آليًا.
                - تحميل سريع لأن الواجهة تقرأ ملفات مجمعة بحجم صغير.
                - فصل الدلالة الإحصائية عن القرار التجاري.
                """
            )

    section_label("معاني المؤشرات التي ستشرحها")
    definitions = pd.DataFrame(
        [
            ["Gross Revenue", "إجمالي الإيراد قبل خصم Cashout", "قياس حجم الإيراد"],
            ["Net Revenue", "Gross Revenue − Cashout", "المؤشر المالي الأقرب للقيمة الفعلية"],
            ["ARPU", "Gross Revenue ÷ جميع المستخدمين المؤهلين", "مقارنة العائد بين المجموعات"],
            ["Monetization Rate", "نسبة المستخدمين الذين حققوا إيرادًا", "قياس التحويل إلى مستخدم مدر للدخل"],
            ["Exact-day Activity", "نشاط المستخدم في اليوم المحدد بالضبط", "قياس العودة في D1 أو D7 أو D30"],
            ["Rolling Activity", "وجود نشاط في اليوم المحدد أو بعده", "قياس الاستمرارية طويلة المدى"],
        ],
        columns=["المؤشر", "التعريف", "الفائدة"],
    )
    st.dataframe(definitions, width="stretch", hide_index=True)

    st.markdown(
        '<div class="insight-note"><strong>الخلاصة التي تقولها:</strong> النظام لا يعرض الأرقام '
        "فقط؛ بل يتأكد من جودة البيانات، يحسب المؤشرات بنفس التعريف لكل مجموعة، يختبر إن كانت "
        "الفروق حقيقية، ثم يحول النتيجة إلى قرار تجاري منخفض المخاطر.</div>",
        unsafe_allow_html=True,
    )


def page_variations() -> None:
    data = load_mart("variation_summary").copy()
    tests = load_mart("statistical_tests")
    page_header(
        "مقارنة مجموعات A/B",
        "استكشف الفروقات الوصفية والمالية بين المجموعة الضابطة والمجموعات التجريبية.",
        "EXPERIMENT PERFORMANCE",
    )
    filter_col, note_col = st.columns([1, 2], gap="large")
    with filter_col:
        metric_label = st.selectbox(
            "المؤشر المعروض",
            ["ARPU", "Average Net Revenue per User", "Monetization Rate", "D30 Rolling Activity"],
        )
    with note_col:
        st.markdown(
            '<div class="method-note"><strong>المجموعة المرجعية:</strong> default. '
            "تُعرض الفروقات الوصفية هنا، بينما قرار الدلالة يعتمد على التصحيح الإحصائي.</div>",
            unsafe_allow_html=True,
        )
    mapping = {
        "ARPU": ("arpu", "قيمة المؤشر", ".3f"),
        "Average Net Revenue per User": ("avg_net_revenue_per_user", "قيمة المؤشر", ".3f"),
        "Monetization Rate": ("monetization_rate", "النسبة", ".2%"),
        "D30 Rolling Activity": ("d30_rolling_activity_rate", "النسبة", ".2%"),
    }
    column, axis_title, fmt = mapping[metric_label]
    chart = (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=52)
        .encode(
            x=alt.X("variation:N", title=None, sort="-y", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{column}:Q", title=axis_title, axis=alt.Axis(format=fmt)),
            color=alt.condition(alt.datum.variation == "default", alt.value("#5B5BD6"), alt.value("#AAA9EE")),
            tooltip=["variation", alt.Tooltip(f"{column}:Q", format=fmt)],
        )
    )
    with st.container(border=True):
        st.altair_chart(polish_chart(chart), width="stretch")

    section_label("الخلاصة الإحصائية")
    st.markdown(
        '<div class="insight-note"><strong>النتيجة:</strong> بعد تصحيح Holm، لم يظهر أي Variation '
        "تحسنًا دالًا في متوسط Gross أو Net Revenue باستخدام Welch t-test. الفروق الوصفية وحدها "
        "لا تعني وجود فائز مالي.</div>",
        unsafe_allow_html=True,
    )
    financial = tests.loc[
        tests["test_name"].eq("welch_t_test"),
        ["metric", "treatment_variation", "control_value", "treatment_value",
         "relative_lift", "ci_95_low", "ci_95_high", "p_value_holm", "significant_after_holm"],
    ]
    st.dataframe(
        financial,
        width="stretch",
        hide_index=True,
        column_config={
            "relative_lift": st.column_config.NumberColumn("Relative Lift", format="%.2f%%"),
            "p_value_holm": st.column_config.NumberColumn("Holm p-value", format="%.4f"),
            "significant_after_holm": st.column_config.CheckboxColumn("دال إحصائيًا"),
        },
    )
    download_csv(data, "variation_summary.csv")


def page_retention() -> None:
    cohorts = load_mart("retention_cohorts").copy()
    cohorts["install_week"] = pd.to_datetime(cohorts["install_week"])
    page_header(
        "النشاط الزمني وتحليل Cohorts",
        "تتبّع سلوك مجموعات التثبيت عبر الزمن مع معالجة Right Censoring.",
        "RETENTION & COHORTS",
    )
    mode_col, day_col = st.columns(2, gap="large")
    with mode_col:
        mode = st.radio("تعريف النشاط", ["Exact-day Activity", "Rolling Activity Dn+"], horizontal=True)
    with day_col:
        day = st.select_slider("نافذة القياس", options=[1, 3, 7, 14, 30], value=7)
    rate_column = f"d{day}_exact_activity_rate" if mode.startswith("Exact") else f"d{day}_rolling_activity_rate"
    chart = (
        alt.Chart(cohorts)
        .mark_line(point=True)
        .encode(
            x=alt.X("install_week:T", title="أسبوع التثبيت"),
            y=alt.Y(f"{rate_column}:Q", title="معدل النشاط", axis=alt.Axis(format=".1%")),
            color=alt.Color(
                "variation:N", title="Variation",
                scale=alt.Scale(range=CHART_COLORS),
            ),
            tooltip=[alt.Tooltip("install_week:T", title="Week"), "variation",
                     alt.Tooltip(f"{rate_column}:Q", format=".2%")],
        )
    )
    with st.container(border=True):
        st.markdown(f"#### تطور معدل النشاط — D{day}")
        st.altair_chart(polish_chart(chart), width="stretch")
    st.markdown(
        '<div class="method-note"><strong>طريقة القراءة:</strong> هذه المؤشرات مبنية على الأحداث '
        "المسجلة في جدول الإيرادات وليست Session Retention. المستخدمون غير مكتملي نافذة الرصد "
        "مستبعدون من المقام.</div>",
        unsafe_allow_html=True,
    )
    download_csv(cohorts, "retention_cohorts.csv")


def page_channels() -> None:
    data = load_mart("channel_summary").copy()
    page_header(
        "أداء قنوات الاكتساب",
        "رتّب القنوات حسب الحجم أو القيمة أو كفاءة تحقيق الإيراد.",
        "ACQUISITION CHANNELS",
    )
    filter_a, filter_b = st.columns(2, gap="large")
    with filter_a:
        top_n = st.slider("عدد القنوات المعروضة", 5, min(19, len(data)), min(10, len(data)))
    with filter_b:
        metric = st.selectbox(
            "ترتيب القنوات حسب",
            ["net_revenue", "users", "arpu", "monetization_rate"],
            format_func={
                "net_revenue": "صافي الإيراد",
                "users": "عدد المستخدمين",
                "arpu": "ARPU",
                "monetization_rate": "معدل تحقيق الإيراد",
            }.get,
        )
    shown = data.nlargest(top_n, metric)
    chart = (
        alt.Chart(shown)
        .mark_bar()
        .encode(
            y=alt.Y("channel_clean:N", title="Channel", sort="-x"),
            x=alt.X(f"{metric}:Q", title=metric),
            color=alt.Color(f"{metric}:Q", scale=alt.Scale(range=["#DADAFE", "#5B5BD6"]), legend=None),
            tooltip=["channel_clean", alt.Tooltip("users:Q", format=","),
                     alt.Tooltip("net_revenue:Q", format=",.2f"),
                     alt.Tooltip("arpu:Q", format=".3f")],
        )
    )
    chart_col, table_col = st.columns([1.2, 1], gap="large")
    with chart_col:
        with st.container(border=True):
            st.altair_chart(polish_chart(chart), width="stretch")
    with table_col:
        st.dataframe(shown, width="stretch", hide_index=True, height=430)
    download_csv(shown, "channel_summary_filtered.csv")


def page_revenue() -> None:
    types = load_mart("revenue_type_summary")
    formats = load_mart("ad_format_summary")
    page_header(
        "مصادر الإيراد وصيغ الإعلانات",
        "توزيع الإيراد حسب المصدر وتحليل مساهمة كل صيغة إعلانية.",
        "REVENUE MIX",
    )
    left, right = st.columns(2, gap="large")
    with left:
        with st.container(border=True):
            st.markdown("#### الإيراد حسب النوع")
            revenue_chart = alt.Chart(types).mark_arc(innerRadius=68, outerRadius=125).encode(
                theta=alt.Theta("total_revenue:Q"),
                color=alt.Color("revenue_type:N", scale=alt.Scale(range=CHART_COLORS), title=None),
                tooltip=["revenue_type", alt.Tooltip("total_revenue:Q", format="$,.2f")],
            )
            st.altair_chart(polish_chart(revenue_chart), width="stretch")
    with right:
        with st.container(border=True):
            st.markdown("#### الإيراد حسب Ad Format")
            format_chart = alt.Chart(formats).mark_bar(cornerRadiusEnd=7).encode(
                y=alt.Y("ad_unit_format_clean:N", sort="-x", title="Ad Format"),
                x=alt.X("total_revenue:Q", title="Revenue ($)"),
                color=alt.value("#18A999"),
                tooltip=["ad_unit_format_clean", alt.Tooltip("total_revenue:Q", format=",.2f"),
                         alt.Tooltip("revenue_share:Q", format=".2%")],
            )
            st.altair_chart(polish_chart(format_chart), width="stretch")
    downloads = st.columns(2)
    with downloads[0]:
        download_csv(types, "revenue_type_summary.csv", "تنزيل أنواع الإيراد")
    with downloads[1]:
        download_csv(formats, "ad_format_summary.csv", "تنزيل صيغ الإعلانات")


def page_statistics() -> None:
    tests = load_mart("statistical_tests").copy()
    page_header(
        "الاختبارات الإحصائية",
        "افحص الدلالة، حجم الأثر وفواصل الثقة بدل الاعتماد على المتوسطات وحدها.",
        "STATISTICAL EVIDENCE",
    )
    metric_col, test_col = st.columns(2, gap="large")
    with metric_col:
        metric = st.selectbox("المؤشر", sorted(tests["metric"].unique()))
    subset = tests.loc[tests["metric"].eq(metric)].copy()
    with test_col:
        test_name = st.selectbox("نوع الاختبار", sorted(subset["test_name"].unique()))
    subset = subset.loc[subset["test_name"].eq(test_name)]
    subset["decision"] = subset["significant_after_holm"].map({True: "دال بعد Holm", False: "غير دال"})
    with st.container(border=True):
        st.dataframe(
            subset[["treatment_variation", "control_value", "treatment_value", "absolute_difference",
                    "relative_lift", "ci_95_low", "ci_95_high", "p_value_holm", "effect_size", "decision"]],
            width="stretch", hide_index=True,
            column_config={
                "p_value_holm": st.column_config.NumberColumn("Holm p-value", format="%.4f"),
                "decision": st.column_config.TextColumn("القرار"),
            },
        )
    download_csv(subset, "statistical_tests_filtered.csv")
    st.markdown(
        '<div class="method-note">الدلالة الإحصائية لا تكفي وحدها. يجب قراءة حجم الأثر وفاصل الثقة '
        "والأهمية التجارية معاً. التصحيح المستخدم: Holm داخل كل مؤشر وعائلة اختبار.</div>",
        unsafe_allow_html=True,
    )


def page_methodology() -> None:
    page_header(
        "جودة البيانات والمنهجية",
        "شفافية كاملة حول نطاق الدراسة، المعالجة، الخصوصية وحدود الاستنتاج.",
        "DATA QUALITY",
    )
    quality_cols = st.columns(4)
    quality_cols[0].metric("مستخدمو التجربة", "934,270")
    quality_cols[1].metric("المعاملات المؤهلة", "11,256,114")
    quality_cols[2].metric("معاملات مستبعدة", "1,729,869")
    quality_cols[3].metric("Gross Revenue", "$4,981,893.06")

    process_col, privacy_col = st.columns(2, gap="large")
    with process_col:
        with st.container(border=True):
            st.markdown("#### قواعد المعالجة")
            st.markdown(
                """
                - تحليل جميع مجموعات التجربة الخمس.
                - إدراج المستخدمين بلا معاملات في مقام المؤشرات.
                - استبعاد المعاملات غير المرتبطة بمستخدمي التجربة.
                - تطبيق Right Censoring على نوافذ النشاط الزمني.
                """
            )
    with privacy_col:
        with st.container(border=True):
            st.markdown("#### الخصوصية والأمان")
            st.markdown(
                """
                - اللوحة تقرأ Data Marts مجمعة فقط.
                - لا تحتوي ملفات العرض على `user_id`.
                - البيانات الخام محفوظة محليًا.
                - ملفات التنزيل مجمعة وآمنة للمشاركة.
                """
            )
    section_label("التعريف المالي")
    st.code("Net Revenue = Gross Revenue - Cashout", language=None)
    st.markdown(
        '<div class="method-note"><strong>حدود الدراسة:</strong> النشاط الزمني مستنتج من الأحداث '
        "المالية المتاحة، لا من سجل جلسات مستقل. النتائج خاصة بنافذة البيانات الحالية ولا تثبت "
        "استمرارية الأثر مستقبلًا.</div>",
        unsafe_allow_html=True,
    )


def page_recommendations() -> None:
    page_header(
        "النتائج والتوصيات",
        "تحويل نتائج التحليل إلى قرار عملي قابل للشرح والتنفيذ.",
        "DECISION & NEXT ACTION",
    )
    st.markdown(
        """
        <div class="recommendation-hero">
          <div class="big">القرار المقترح: الإبقاء على المجموعة default حاليًا</div>
          <div class="small">لا يوجد تحسن مالي دال يبرر الإطلاق العام. أفضل خطوة هي تجربة تحقق جديدة ومحددة للمجموعة androidndorder.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    section_label("ماذا نفعل بكل مجموعة؟")
    st.markdown(
        """
        <div class="decision-grid">
          <div class="decision-card go"><strong>اختبار متابعة</strong><span><b>androidndorder</b><br>أفضل إشارة قصيرة المدى: تحسن صغير في Monetization وD1 Rolling، لكن دون إثبات مالي بعد.</span></div>
          <div class="decision-card hold"><strong>مراقبة فقط</strong><span><b>androidnd1order</b><br>إشارة إيجابية صغيرة في D30 Rolling، مع غياب تحسن مثبت في متوسط الإيراد.</span></div>
          <div class="decision-card stop"><strong>عدم التوسّع</strong><span><b>androidnd7order وandroidnd30order</b><br>إشارات سلبية صغيرة ومتسقة في التحويل أو النشاط المبكر.</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    action_col, value_col = st.columns(2, gap="large")
    with action_col:
        with st.container(border=True):
            st.markdown("#### خطة التنفيذ المقترحة")
            st.markdown(
                """
                1. الإبقاء على `default` كخيار الإنتاج الحالي.
                2. إعادة اختبار `androidndorder` بعينة وفترة محددتين مسبقًا.
                3. اعتماد Net Revenue per User كمؤشر أساسي للقرار.
                4. مراقبة Monetization وD1/D7/D30 كمؤشرات مساندة.
                5. تحديد حد أدنى للأثر التجاري قبل بدء التجربة الجديدة.
                """
            )
    with value_col:
        with st.container(border=True):
            st.markdown("#### فائدة المشروع للشركة")
            st.markdown(
                """
                - يمنع إطلاق تغييرات بناءً على فروقات ظاهرية مضللة.
                - يربط قرار المنتج بالإيراد وسلوك المستخدم معًا.
                - يكشف الإشارات السلبية قبل تعميمها على المستخدمين.
                - يوفر Pipeline قابلة لإعادة التشغيل لأي تجربة جديدة.
                - يقدم لوحة آمنة وسريعة دون نشر بيانات المستخدمين الخام.
                """
            )

    st.markdown(
        '<div class="method-note"><strong>صياغة مناسبة للمناقشة:</strong> المشروع لا يختار '
        "أعلى عمود في الرسم؛ بل يختبر إن كان الفرق حقيقيًا ومهمًا تجاريًا، ثم يحوله إلى قرار "
        "منتج منخفض المخاطر.</div>",
        unsafe_allow_html=True,
    )


PAGES = {
    "الملخص التنفيذي": page_overview,
    "كيف يعمل النظام؟": page_system_flow,
    "مجموعات A/B": page_variations,
    "Retention & Cohorts": page_retention,
    "قنوات الاكتساب": page_channels,
    "الإيراد والإعلانات": page_revenue,
    "الاختبارات الإحصائية": page_statistics,
    "النتائج والتوصيات": page_recommendations,
    "المنهجية وجودة البيانات": page_methodology,
}

with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
          <div class="logo">◈ JustPlay Analytics</div>
          <div class="meta">لوحة مشروع التخرج الثاني</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    selected_page = st.radio("التنقل بين الصفحات", list(PAGES), label_visibility="collapsed")
    st.divider()
    st.markdown(
        '<div class="privacy-pill">🔒 بيانات مجمعة · تشغيل محلي · بلا معرّفات شخصية</div>',
        unsafe_allow_html=True,
    )
    st.caption("FYP II · Full-data analysis")

PAGES[selected_page]()

