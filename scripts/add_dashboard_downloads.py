from pathlib import Path


app = Path(__file__).resolve().parents[1] / "app" / "streamlit_app.py"
text = app.read_text(encoding="utf-8")

if "def download_csv(" in text:
    print("Dashboard downloads already exist")
    raise SystemExit(0)

helper_anchor = '''def pct(value: float) -> str:
    return f"{value:.2%}"
'''
helper = helper_anchor + '''

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
'''

replacements = {
    helper_anchor: helper,
    '''            unsafe_allow_html=True,
        )


def page_variations() -> None:
''': '''            unsafe_allow_html=True,
        )
    download_csv(variations, "variation_summary.csv", "تنزيل ملخص الـVariations")


def page_variations() -> None:
''',
    '''    st.dataframe(financial, width="stretch", hide_index=True)


def page_retention() -> None:
''': '''    st.dataframe(financial, width="stretch", hide_index=True)
    download_csv(data, "variation_summary.csv")


def page_retention() -> None:
''',
    '''        "والمستخدمون غير مكتملي نافذة الرصد مستبعدون من المقام."
    )


def page_channels() -> None:
''': '''        "والمستخدمون غير مكتملي نافذة الرصد مستبعدون من المقام."
    )
    download_csv(cohorts, "retention_cohorts.csv")


def page_channels() -> None:
''',
    '''    st.dataframe(shown, width="stretch", hide_index=True)


def page_revenue() -> None:
''': '''    st.dataframe(shown, width="stretch", hide_index=True)
    download_csv(shown, "channel_summary_filtered.csv")


def page_revenue() -> None:
''',
    '''            ), width="stretch",
        )


def page_statistics() -> None:
''': '''            ), width="stretch",
        )
    downloads = st.columns(2)
    with downloads[0]:
        download_csv(types, "revenue_type_summary.csv", "تنزيل أنواع الإيراد")
    with downloads[1]:
        download_csv(formats, "ad_format_summary.csv", "تنزيل صيغ الإعلانات")


def page_statistics() -> None:
''',
    '''        hide_index=True,
    )
    st.markdown(
''': '''        hide_index=True,
    )
    download_csv(subset, "statistical_tests_filtered.csv")
    st.markdown(
''',
}

missing = [old for old in replacements if old not in text]
if missing:
    raise SystemExit(f"Dashboard update aborted; {len(missing)} expected anchors were not found")
for old, new in replacements.items():
    text = text.replace(old, new, 1)

app.write_text(text, encoding="utf-8")
print("Dashboard downloads added successfully")
