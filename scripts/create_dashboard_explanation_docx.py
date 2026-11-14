"""Create the Arabic dashboard explanation and defense guide as a DOCX."""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "Dashboard_Explanation_AR.docx"

# compact_reference_guide token map
PAGE_WIDTH = 8.5
PAGE_HEIGHT = 11.0
MARGIN = 0.72
CONTENT_WIDTH_DXA = 10165
FONT = "Arial"
NAVY = "183153"
BLUE = "4F61C8"
TEAL = "159B8D"
INK = "172033"
MUTED = "667085"
PALE_BLUE = "EEF0FF"
PALE_TEAL = "EAF8F5"
PALE_GOLD = "FFF6DF"
LINE = "DDE2EA"
WHITE = "FFFFFF"


def rgb(hex_value: str) -> RGBColor:
    return RGBColor.from_string(hex_value)


def set_cell_shading(cell, fill: str) -> None:
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = tc_pr.find(qn("w:shd"))
    if shd is None:
        shd = OxmlElement("w:shd")
        tc_pr.append(shd)
    shd.set(qn("w:fill"), fill)


def set_cell_margins(cell, top=90, start=120, bottom=90, end=120) -> None:
    tc = cell._tc
    tc_pr = tc.get_or_add_tcPr()
    tc_mar = tc_pr.first_child_found_in("w:tcMar")
    if tc_mar is None:
        tc_mar = OxmlElement("w:tcMar")
        tc_pr.append(tc_mar)
    for name, value in (("top", top), ("start", start), ("bottom", bottom), ("end", end)):
        node = tc_mar.find(qn(f"w:{name}"))
        if node is None:
            node = OxmlElement(f"w:{name}")
            tc_mar.append(node)
        node.set(qn("w:w"), str(value))
        node.set(qn("w:type"), "dxa")


def set_repeat_table_header(row) -> None:
    tr_pr = row._tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)


def set_table_geometry(table, widths: list[int]) -> None:
    table.autofit = False
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl_pr = table._tbl.tblPr
    tbl_w = tbl_pr.first_child_found_in("w:tblW")
    if tbl_w is None:
        tbl_w = OxmlElement("w:tblW")
        tbl_pr.append(tbl_w)
    tbl_w.set(qn("w:w"), str(sum(widths)))
    tbl_w.set(qn("w:type"), "dxa")
    tbl_ind = tbl_pr.first_child_found_in("w:tblInd")
    if tbl_ind is None:
        tbl_ind = OxmlElement("w:tblInd")
        tbl_pr.append(tbl_ind)
    tbl_ind.set(qn("w:w"), "120")
    tbl_ind.set(qn("w:type"), "dxa")
    grid = table._tbl.tblGrid
    for child in list(grid):
        grid.remove(child)
    for width in widths:
        col = OxmlElement("w:gridCol")
        col.set(qn("w:w"), str(width))
        grid.append(col)
    for row in table.rows:
        for i, cell in enumerate(row.cells):
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.first_child_found_in("w:tcW")
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(widths[i]))
            tc_w.set(qn("w:type"), "dxa")
            set_cell_margins(cell)


def set_rtl(paragraph, alignment=WD_ALIGN_PARAGRAPH.RIGHT) -> None:
    paragraph.alignment = alignment
    p_pr = paragraph._p.get_or_add_pPr()
    bidi = p_pr.find(qn("w:bidi"))
    if bidi is None:
        bidi = OxmlElement("w:bidi")
        p_pr.append(bidi)
    bidi.set(qn("w:val"), "1")


def style_run(run, size=10.5, bold=False, color=INK, italic=False) -> None:
    run.font.name = FONT
    run._element.get_or_add_rPr().rFonts.set(qn("w:ascii"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:hAnsi"), FONT)
    run._element.get_or_add_rPr().rFonts.set(qn("w:cs"), FONT)
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = rgb(color)
    run._element.get_or_add_rPr().append(OxmlElement("w:rtl"))


def add_para(doc, text: str, *, bold=False, color=INK, size=10.5, after=5,
             before=0, align=WD_ALIGN_PARAGRAPH.RIGHT, keep=False):
    p = doc.add_paragraph()
    set_rtl(p, align)
    p.paragraph_format.space_before = Pt(before)
    p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.line_spacing = 1.22
    p.paragraph_format.keep_with_next = keep
    r = p.add_run(text)
    style_run(r, size=size, bold=bold, color=color)
    return p


def add_bullet(doc, text: str, level=0):
    p = doc.add_paragraph(style="List Bullet" if level == 0 else "List Bullet 2")
    set_rtl(p)
    p.paragraph_format.space_after = Pt(2.5)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    style_run(r, size=10.2)
    return p


def add_number(doc, text: str):
    p = doc.add_paragraph(style="List Number")
    set_rtl(p)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.15
    r = p.add_run(text)
    style_run(r, size=10.2)
    return p


def add_heading(doc, text: str, level=1):
    p = doc.add_paragraph(style=f"Heading {level}")
    set_rtl(p)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    return p


def add_callout(doc, label: str, text: str, fill=PALE_BLUE, accent=BLUE):
    table = doc.add_table(rows=1, cols=1)
    set_table_geometry(table, [CONTENT_WIDTH_DXA])
    cell = table.cell(0, 0)
    set_cell_shading(cell, fill)
    cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    p = cell.paragraphs[0]
    set_rtl(p)
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(f"{label}: ")
    style_run(r, size=10.2, bold=True, color=accent)
    r = p.add_run(text)
    style_run(r, size=10.2, color=INK)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_table(doc, headers: list[str], rows: list[list[str]], widths: list[int]):
    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    hdr = table.rows[0]
    set_repeat_table_header(hdr)
    for i, text in enumerate(headers):
        cell = hdr.cells[i]
        set_cell_shading(cell, NAVY)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        p = cell.paragraphs[0]
        set_rtl(p, WD_ALIGN_PARAGRAPH.CENTER)
        r = p.add_run(str(text))
        style_run(r, size=9.2, bold=True, color=WHITE)
    for row_idx, values in enumerate(rows):
        cells = table.add_row().cells
        for i, value in enumerate(values):
            if row_idx % 2:
                set_cell_shading(cells[i], "F7F8FB")
            cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = cells[i].paragraphs[0]
            set_rtl(p, WD_ALIGN_PARAGRAPH.CENTER)
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(value))
            style_run(r, size=9.1)
    set_table_geometry(table, widths)
    doc.add_paragraph().paragraph_format.space_after = Pt(1)
    return table


def add_page_title(doc, number: str, title: str, subtitle: str):
    p = doc.add_paragraph()
    set_rtl(p)
    p.paragraph_format.space_before = Pt(2)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    badge = p.add_run(number)
    style_run(badge, size=11, bold=True, color=TEAL)
    p.add_run("   ")
    r = p.add_run(title)
    style_run(r, size=20, bold=True, color=NAVY)
    add_para(doc, subtitle, color=MUTED, size=10.5, after=10, keep=True)


def add_page_number(paragraph) -> None:
    set_rtl(paragraph, WD_ALIGN_PARAGRAPH.CENTER)
    run = paragraph.add_run("صفحة ")
    style_run(run, size=8.5, color=MUTED)
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = " PAGE "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = "1"
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.extend([begin, instr, separate, text, end])


def configure_document(doc: Document) -> None:
    section = doc.sections[0]
    section.page_width = Inches(PAGE_WIDTH)
    section.page_height = Inches(PAGE_HEIGHT)
    section.top_margin = Inches(MARGIN)
    section.bottom_margin = Inches(MARGIN)
    section.left_margin = Inches(MARGIN)
    section.right_margin = Inches(MARGIN)
    section.header_distance = Inches(0.3)
    section.footer_distance = Inches(0.3)

    styles = doc.styles
    normal = styles["Normal"]
    normal.font.name = FONT
    normal._element.rPr.rFonts.set(qn("w:ascii"), FONT)
    normal._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
    normal._element.rPr.rFonts.set(qn("w:cs"), FONT)
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = rgb(INK)
    normal.paragraph_format.space_after = Pt(5)
    normal.paragraph_format.line_spacing = 1.22

    tokens = {
        "Heading 1": (17, NAVY, 13, 6),
        "Heading 2": (13, BLUE, 9, 4),
        "Heading 3": (11, TEAL, 6, 3),
    }
    for name, (size, color, before, after) in tokens.items():
        style = styles[name]
        style.font.name = FONT
        style._element.rPr.rFonts.set(qn("w:ascii"), FONT)
        style._element.rPr.rFonts.set(qn("w:hAnsi"), FONT)
        style._element.rPr.rFonts.set(qn("w:cs"), FONT)
        style.font.size = Pt(size)
        style.font.bold = True
        style.font.color.rgb = rgb(color)
        style.paragraph_format.space_before = Pt(before)
        style.paragraph_format.space_after = Pt(after)
        style.paragraph_format.keep_with_next = True

    header = section.header
    hp = header.paragraphs[0]
    set_rtl(hp)
    hr = hp.add_run("JustPlay Analytics  |  دليل شرح Dashboard")
    style_run(hr, size=8.5, bold=True, color=MUTED)
    add_page_number(section.footer.paragraphs[0])


def add_cover(doc: Document) -> None:
    for _ in range(5):
        add_para(doc, "", after=7)
    add_para(doc, "FYP II  •  JUSTPLAY ANALYTICS", bold=True, color=TEAL, size=11,
             align=WD_ALIGN_PARAGRAPH.CENTER, after=16)
    add_para(doc, "الدليل الكامل لشرح لوحة التحليل", bold=True, color=NAVY, size=27,
             align=WD_ALIGN_PARAGRAPH.CENTER, after=8)
    add_para(doc, "من البيانات الخام إلى القرار التجاري", bold=True, color=BLUE, size=16,
             align=WD_ALIGN_PARAGRAPH.CENTER, after=24)
    add_callout(
        doc,
        "هدف الدليل",
        "شرح الصفحات التسع، الأرقام والرسوم، طريقة تفسير النتائج، وما يمكن قوله أمام لجنة المناقشة.",
        fill=PALE_TEAL,
        accent=TEAL,
    )
    for _ in range(4):
        add_para(doc, "", after=7)
    add_para(doc, "تحليل كامل للبيانات • A/B Testing • KPIs • Retention • Statistical Evidence",
             color=MUTED, size=10, align=WD_ALIGN_PARAGRAPH.CENTER, after=5)
    add_para(doc, "إعداد للمراجعة والعرض العملي", bold=True, color=NAVY, size=11,
             align=WD_ALIGN_PARAGRAPH.CENTER)
    doc.add_page_break()


def add_opening(doc: Document) -> None:
    add_heading(doc, "كيف تبدأ العرض؟", 1)
    add_callout(
        doc,
        "افتتاحية مقترحة",
        "مشروعي يحلل تجربة A/B لشركة ألعاب اسمها JustPlay. الهدف ليس فقط مقارنة أرقام خمس مجموعات، بل بناء Pipeline كاملة تبدأ من تدقيق قرابة 13 مليون معاملة، ثم تنظيف البيانات وحساب KPIs وRetention، وإجراء اختبارات إحصائية، وأخيرًا تحويل النتائج إلى قرار منتج واضح داخل Dashboard تفاعلية.",
    )
    add_heading(doc, "السؤال الذي يجيب عنه المشروع", 2)
    add_para(doc, "هل حسّن أي Variation سلوك المستخدمين أو الإيرادات مقارنة بالمجموعة الأصلية default؟ وهل الفرق حقيقي ومهم تجاريًا، أم مجرد فرق عشوائي؟")
    add_heading(doc, "مسار المشروع", 2)
    for step in [
        "بيانات CSV خام: ملف مستخدمين وملف معاملات مالية.",
        "تدقيق الجودة وتحديد مستخدمي ومعاملات تجربة A/B المؤهلين.",
        "تنظيف البيانات وتحويلها إلى Parquet مضغوط بـZSTD.",
        "بناء جدول خصائص واحد لكل مستخدم.",
        "حساب KPIs وRetention وCohorts.",
        "إجراء 48 اختبارًا إحصائيًا مع تصحيح Holm.",
        "إنشاء Data Marts صغيرة وآمنة للعرض.",
        "عرض النتائج في Dashboard وتحويلها إلى توصية تنفيذية.",
    ]:
        add_number(doc, step)
    add_heading(doc, "الخلاصة قبل التفاصيل", 2)
    add_callout(doc, "القرار", "لا يوجد Variation حقق تحسنًا ماليًا مثبتًا مقارنة بـdefault. نُبقي default حاليًا، ونقترح تجربة تحقق جديدة لـandroidndorder لأنه أظهر أفضل إشارة سلوكية قصيرة المدى.", fill=PALE_GOLD, accent="A66A00")
    doc.add_page_break()


def page_overview(doc: Document) -> None:
    add_page_title(doc, "01", "الملخص التنفيذي", "صورة المشروع العامة وأهم مؤشرات الأداء والقرار الأولي.")
    add_heading(doc, "ماذا تعرض الصفحة؟", 2)
    add_bullet(doc, "المشكلة: خمس مجموعات تحتاج إلى قرار مبني على دليل لا على المتوسطات الظاهرية.")
    add_bullet(doc, "التحليل: تدقيق البيانات، حساب المؤشرات، Cohorts، و48 اختبارًا إحصائيًا.")
    add_bullet(doc, "النتيجة: لا يوجد فائز مالي مثبت، مع إشارات سلوكية صغيرة.")
    add_bullet(doc, "القيمة: منع إطلاق تغيير غير مثبت وتوجيه التجربة التالية.")
    add_heading(doc, "المؤشرات العامة", 2)
    add_table(doc, ["المؤشر", "القيمة"], [
        ["المستخدمون", "934,270"], ["Gross Revenue", "$4,981,893.06"],
        ["Cashout", "$1,583,184.77"], ["Net Revenue", "$3,398,708.29"],
        ["ARPU", "$5.3324"], ["Average Net Revenue/User", "$3.6378"],
        ["Activation Rate", "97.80%"], ["Monetization Rate", "67.37%"],
    ], [6100, 4065])
    add_heading(doc, "صافي الإيراد حسب المجموعة", 2)
    add_table(doc, ["Variation", "Net Revenue"], [
        ["default", "$687,974.51"], ["androidnd1order", "$687,306.84"],
        ["androidndorder", "$686,101.34"], ["androidnd30order", "$670,693.68"],
        ["androidnd7order", "$666,631.92"],
    ], [6100, 4065])
    add_callout(doc, "ما تقوله", "هذه مجاميع وصفية وتتأثر بعدد المستخدمين. لذلك لا أختار أعلى عمود مباشرة؛ بل أنتقل إلى مؤشرات لكل مستخدم وإلى الاختبارات الإحصائية.", fill=PALE_TEAL, accent=TEAL)
    add_heading(doc, "تعريفات سريعة", 3)
    add_bullet(doc, "Gross Revenue: مجموع الإيرادات قبل خصم المبالغ المدفوعة للمستخدمين.")
    add_bullet(doc, "Net Revenue = Gross Revenue - Cashout.")
    add_bullet(doc, "ARPU = Gross Revenue ÷ جميع المستخدمين المؤهلين، بما فيهم من لم يحقق إيرادًا.")
    doc.add_page_break()


def page_system(doc: Document) -> None:
    add_page_title(doc, "02", "كيف يعمل النظام؟", "المعمارية التي تحوّل ملايين السجلات إلى نتائج سريعة وآمنة.")
    add_heading(doc, "البيانات والنطاق", 2)
    add_table(doc, ["البند", "العدد"], [
        ["مستخدمو التجربة", "934,270"], ["المعاملات الخام", "12,985,983"],
        ["المعاملات المؤهلة", "11,256,114"], ["المعاملات الخارجية المستبعدة", "1,729,869"],
        ["مستخدمون خارجيون لديهم معاملات", "102,146"], ["مستخدمو التجربة بلا معاملات", "138,957"],
    ], [6500, 3665])
    add_callout(doc, "قاعدة النطاق", "تدخل في تحليل A/B فقط معاملات المستخدمين الموجودين في ملف التجربة. المعاملات الخارجية محفوظة للتدقيق، لكنها لا تدخل في KPIs أو الاختبارات.")
    add_heading(doc, "خطوات المعالجة", 2)
    for item in [
        "قراءة ملف المعاملات على دفعات بحجم 250 ألف صف لتقليل استهلاك الذاكرة.",
        "التحقق من فريدة user_id، وتحويل التواريخ والقيم المالية إلى أنواع صحيحة.",
        "توحيد country وplatform وتحويل missing النصية إلى Unknown.",
        "مطابقة المعاملات مع مستخدمي التجربة واستبعاد الصفوف الخارجية من التحليل.",
        "حفظ البيانات المعالجة بصيغة Parquet مع ضغط ZSTD لتسريع القراءة وتقليل الحجم.",
        "إنشاء user_features: صف واحد لكل مستخدم مع الإيراد، Cashout، النشاط والـRetention.",
        "إنشاء Data Marts مجمعة تقرأها الواجهة دون الرجوع إلى البيانات الخام.",
    ]:
        add_number(doc, item)
    add_heading(doc, "لماذا Parquet وZSTD؟", 2)
    add_para(doc, "Parquet صيغة عمودية تحفظ أنواع البيانات وتسمح بقراءة الأعمدة المطلوبة فقط. ZSTD خوارزمية ضغط تقلل حجم الملف دون فقد البيانات. النتيجة: قراءة أسرع، تخزين أقل، واستهلاك ذاكرة أخف من CSV.")
    add_heading(doc, "مكوّنات المشروع", 2)
    add_bullet(doc, "src/pipeline: التدقيق والتنظيف والتحويل.")
    add_bullet(doc, "src/analytics: KPIs وData Marts والاختبارات الإحصائية.")
    add_bullet(doc, "data/marts: نتائج صغيرة مجمعة وآمنة.")
    add_bullet(doc, "app: تطبيق Streamlit التفاعلي.")
    add_bullet(doc, "tests: اختبارات الوحدة والتكامل والثبات والخصوصية.")
    add_callout(doc, "ما تقوله", "النظام لا يعرض الأرقام فقط؛ بل يتأكد من جودة البيانات، يوحّد تعريف المؤشرات، يختبر إن كانت الفروق حقيقية، ثم يحوّل النتيجة إلى قرار منخفض المخاطر.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def page_variations(doc: Document) -> None:
    add_page_title(doc, "03", "مقارنة مجموعات A/B", "الفروق الوصفية والمالية بين default والمجموعات التجريبية.")
    add_heading(doc, "المجموعة المرجعية", 2)
    add_para(doc, "المجموعة default هي Control. كل واحدة من المجموعات الأربع الأخرى قورنت بها بصورة مستقلة.")
    add_heading(doc, "ARPU وصافي الإيراد لكل مستخدم", 2)
    add_table(doc, ["Variation", "ARPU", "Net/User"], [
        ["androidnd1order", "$5.394", "$3.6866"], ["default", "$5.388", "$3.6711"],
        ["androidndorder", "$5.389", "$3.6656"], ["androidnd30order", "$5.265", "$3.5888"],
        ["androidnd7order", "$5.226", "$3.5769"],
    ], [4500, 2830, 2835])
    add_callout(doc, "التفسير", "androidnd1order أعلى وصفيًا في ARPU بفارق يقارب 0.007 دولار فقط عن default. لم يكن الفرق دالًا في Welch t-test بعد Holm، لذلك لا نعتبره فائزًا ماليًا.")
    add_heading(doc, "Monetization وD30 Rolling", 2)
    add_table(doc, ["Variation", "Monetization", "D30 Rolling"], [
        ["androidndorder", "67.89%", "12.18%"], ["androidnd1order", "67.50%", "12.31%"],
        ["default", "67.44%", "11.87%"], ["androidnd30order", "67.06%", "11.78%"],
        ["androidnd7order", "66.98%", "11.69%"],
    ], [4500, 2830, 2835])
    add_bullet(doc, "androidndorder: Monetization أعلى من default بنحو 0.450 نقطة مئوية.")
    add_bullet(doc, "androidnd1order: D30 Rolling أعلى من default بنحو 0.440 نقطة مئوية.")
    add_heading(doc, "الخلاصة التي تقولها", 2)
    add_callout(doc, "النص المقترح", "الرسوم تعرض فروقًا وصفية صغيرة، لكن بعد تصحيح Holm لم يظهر أي Variation تحسنًا دالًا في متوسط Gross أو Net Revenue. لذلك لا يوجد فائز مالي مثبت.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def page_retention(doc: Document) -> None:
    add_page_title(doc, "04", "Retention & Cohorts", "النشاط الزمني حسب أسبوع التثبيت مع معالجة Right Censoring.")
    add_heading(doc, "تعريف المؤشرات", 2)
    add_bullet(doc, "Exact-day Activity Dn: وجود معاملة في اليوم n بالضبط بعد التثبيت.")
    add_bullet(doc, "Rolling Activity Dn+: وجود معاملة في اليوم n أو أي يوم بعده.")
    add_bullet(doc, "النوافذ المتاحة: D1 وD3 وD7 وD14 وD30.")
    add_callout(doc, "تنبيه منهجي", "البيانات لا تحتوي Sessions مستقلة؛ لذلك نقيس نشاطًا ماليًا مسجلًا، ولا ندّعي أنه Session Retention تقليدي.", fill=PALE_GOLD, accent="A66A00")
    add_heading(doc, "Right Censoring", 2)
    add_para(doc, "إذا ثبت مستخدم التطبيق قبل نهاية البيانات بثلاثة أيام، لا ندخله في مقام D30؛ لأنه لم تتح له فرصة كاملة للوصول إلى اليوم الثلاثين. يدخل المستخدم في المقام فقط إذا اكتملت له نافذة القياس.")
    add_heading(doc, "أبرز معدلات Rolling", 2)
    add_table(doc, ["Variation", "D1", "D7", "D30"], [
        ["androidndorder", "53.65%", "27.87%", "12.18%"],
        ["androidnd1order", "53.47%", "27.73%", "12.31%"],
        ["default", "53.25%", "27.53%", "11.87%"],
        ["androidnd30order", "52.82%", "27.27%", "11.78%"],
        ["androidnd7order", "52.83%", "27.08%", "11.69%"],
    ], [4100, 2020, 2020, 2025])
    add_heading(doc, "كيف تشرح الرسم؟", 2)
    add_bullet(doc, "كل خط يمثل Variation، والمحور الأفقي يمثل أسبوع التثبيت.")
    add_bullet(doc, "الأفضل مقارنة Variations داخل الأسبوع نفسه لأن الظروف قد تختلف عبر الزمن.")
    add_bullet(doc, "Rolling أعلى من Exact لأنه تعريف أوسع.")
    add_bullet(doc, "انخفاض النشاط من D1 إلى D30 سلوك متوقع، والمهم هو الفرق بين المجموعات.")
    add_callout(doc, "النتيجة", "androidndorder أعطى أفضل إشارة قصيرة المدى في D1 Rolling، بينما androidnd1order أعطى أفضل إشارة متأخرة في D30 Rolling. الأحجام صغيرة ولا تثبت تحسنًا ماليًا.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def page_channels(doc: Document) -> None:
    add_page_title(doc, "05", "قنوات الاكتساب", "مقارنة الحجم والقيمة وكفاءة تحقيق الإيراد حسب القناة.")
    add_heading(doc, "أكبر القنوات حسب صافي الإيراد", 2)
    add_table(doc, ["القناة", "المستخدمون", "Net Revenue", "ARPU", "Monetization"], [
        ["Google Ads ACI", "345,016", "$1.31M", "$5.44", "72.77%"],
        ["Unknown", "217,163", "$610.9K", "$4.48", "53.03%"],
        ["Organic", "127,977", "$540.5K", "$6.22", "67.11%"],
        ["AppLovin", "93,600", "$467.0K", "$7.33", "78.71%"],
        ["Mintegral", "78,114", "$244.3K", "$4.22", "69.91%"],
    ], [2700, 1830, 2100, 1535, 2000])
    add_heading(doc, "كيف تفسّر النتائج؟", 2)
    add_bullet(doc, "Google Ads ACI يحقق أعلى صافي إيراد إجمالي لأن حجمه الأكبر.")
    add_bullet(doc, "AppLovin تبدو الأقوى كفاءة بين القنوات الكبيرة: ARPU نحو 7.33 دولار وMonetization نحو 78.7%.")
    add_bullet(doc, "Organic جيد في ARPU عند نحو 6.22 دولار.")
    add_bullet(doc, "Unknown تضم 217 ألف مستخدم وكفاءتها أقل؛ وقد تشير إلى نقص في Attribution.")
    add_heading(doc, "خطأ يجب تجنبه", 2)
    add_callout(doc, "تحذير", "قد تظهر قناة صغيرة مثل aura بـARPU مرتفع جدًا، لكنها تحتوي 15 مستخدمًا فقط. لا نعتمد على النسبة دون النظر إلى حجم العينة.", fill=PALE_GOLD, accent="A66A00")
    add_para(doc, "كذلك لا نستطيع إعلان أفضل قناة تسويقيًا بصورة نهائية؛ لأن البيانات لا تشمل تكلفة الاستحواذ CAC أو ROAS. يمكننا وصف الإيراد والكفاءة داخل البيانات فقط.")
    add_callout(doc, "ما تقوله", "Google Ads يقود القيمة الإجمالية، وAppLovin تبدو قوية في العائد والتحويل بين القنوات الكبيرة، لكن قرار الإنفاق التسويقي يحتاج إضافة تكلفة الاستحواذ.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def page_revenue(doc: Document) -> None:
    add_page_title(doc, "06", "مصادر الإيراد وصيغ الإعلانات", "توزيع Gross Revenue والمساهمة النسبية لصيغ الإعلانات.")
    add_heading(doc, "الإيراد حسب النوع", 2)
    add_table(doc, ["النوع", "المعاملات", "المستخدمون", "الإيراد", "الحصة"], [
        ["Ads", "9,793,590", "795,020", "$3.508M", "70.4%"],
        ["Offerwall", "469,377", "154,705", "$1.474M", "29.6%"],
        ["Cashout", "993,147", "271,635", "$0 كإيراد", "—"],
    ], [2200, 2100, 2000, 2200, 1665])
    add_para(doc, "Cashout ليس مصدر إيراد؛ لذلك قيمة revenue_amount له صفر، بينما يُحفظ مبلغ Cashout في عمود مستقل ويُخصم عند حساب Net Revenue.")
    add_heading(doc, "الإيراد حسب Ad Format", 2)
    add_table(doc, ["الصيغة", "الإيراد", "الحصة من إيراد الإعلانات"], [
        ["Interstitial", "$2.389M", "68.10%"],
        ["Rewarded", "$836.8K", "23.85%"],
        ["Banner", "$282.4K", "8.05%"],
    ], [4000, 3000, 3165])
    add_heading(doc, "التفسير", 2)
    add_bullet(doc, "الإعلانات تمثل نحو 70.4% من Gross Revenue، وOfferwall نحو 29.6%.")
    add_bullet(doc, "Interstitial هو أكبر مساهم داخل إيراد الإعلانات بنسبة 68.1%.")
    add_bullet(doc, "Rewarded يساهم بنحو 23.85%، وBanner بنحو 8.05%.")
    add_callout(doc, "ما تقوله", "Interstitial هو المصدر الأكبر داخل الإعلانات، لكن لا أوصي بزيادته اعتمادًا على الإيراد وحده؛ يجب قياس أثره على تجربة المستخدم والRetention.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def page_statistics(doc: Document) -> None:
    add_page_title(doc, "07", "الاختبارات الإحصائية", "قراءة الدلالة، حجم الأثر وفاصل الثقة بدل الاعتماد على المتوسطات فقط.")
    add_heading(doc, "كيف تقرأ أعمدة الجدول؟", 2)
    add_table(doc, ["الحقل", "المعنى"], [
        ["control_value", "قيمة المجموعة default"], ["treatment_value", "قيمة Variation التجريبية"],
        ["absolute_difference", "الفرق المباشر بين القيمتين"], ["relative_lift", "الفرق كنسبة من قيمة default"],
        ["ci_95_low / high", "فاصل الثقة 95% للفرق"], ["p_value_holm", "الدلالة بعد تصحيح المقارنات"],
        ["effect_size", "حجم الفرق عمليًا"], ["decision", "هل بقي الفرق دالًا بعد Holm؟"],
    ], [3600, 6565])
    add_heading(doc, "الاختبارات المستخدمة", 2)
    add_bullet(doc, "Welch t-test: مقارنة متوسط Gross وNet Revenue دون افتراض تساوي التباين.")
    add_bullet(doc, "Mann-Whitney U: تحليل حساسية للتوزيع المنحرف وكثرة القيم الصفرية.")
    add_bullet(doc, "Two-proportion z-test: مقارنة نسب Activation وMonetization وActivity.")
    add_bullet(doc, "Holm correction: تقليل النتائج الإيجابية الكاذبة الناتجة عن كثرة المقارنات.")
    add_heading(doc, "النتائج الأساسية", 2)
    add_bullet(doc, "تم تنفيذ 48 اختبارًا، وبقي 19 اختبارًا دالًا بعد Holm.")
    add_bullet(doc, "صفر من أربع مقارنات Gross Revenue كان دالًا باستخدام Welch.")
    add_bullet(doc, "صفر من أربع مقارنات Net Revenue كان دالًا باستخدام Welch.")
    add_bullet(doc, "لا يوجد فرق دال في Activation Rate لأي Variation.")
    add_bullet(doc, "Mann-Whitney وجد فروقًا توزيعية، لكن Rank-biserial كان أقل من 0.007 بالقيمة المطلقة.")
    add_callout(doc, "قاعدة القرار", "الدلالة الإحصائية لا تعني أهمية تجارية. مع عينة تقارب المليون مستخدم، قد يصبح فرق صغير جدًا دالًا، ولذلك نقرأ p-value وحجم الأثر وفاصل الثقة معًا.", fill=PALE_GOLD, accent="A66A00")
    add_heading(doc, "مثالان تشرحهما", 2)
    add_bullet(doc, "androidndorder: Monetization زاد 0.450 نقطة مئوية وD1 Rolling زاد 0.395 نقطة؛ فروق دالة لكنها صغيرة.")
    add_bullet(doc, "androidnd1order: D30 Rolling زاد 0.440 نقطة مئوية، Holm p=0.0097؛ إشارة سلوكية لا تحسن مالي مثبت.")
    add_callout(doc, "الجملة الذهبية", "Statistical significance لا تساوي Business significance، خصوصًا عندما يكون حجم العينة كبيرًا.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def page_recommendations(doc: Document) -> None:
    add_page_title(doc, "08", "النتائج والتوصيات", "تحويل التحليل إلى قرار منتج واضح ومنخفض المخاطر.")
    add_callout(doc, "القرار النهائي", "الإبقاء على default حاليًا؛ لا يوجد تحسن مالي دال يبرر الإطلاق العام.", fill=PALE_GOLD, accent="A66A00")
    add_heading(doc, "القرار لكل مجموعة", 2)
    add_table(doc, ["Variation", "الإجراء", "السبب"], [
        ["androidndorder", "اختبار متابعة", "أفضل إشارة قصيرة المدى في Monetization وD1 Rolling دون إثبات مالي"],
        ["androidnd1order", "مراقبة/اختبار لاحق", "إشارة صغيرة في D30 Rolling دون تحسن في متوسط الإيراد"],
        ["androidnd7order", "عدم التوسع", "إشارات سلبية متسقة في Monetization وD1 وD7"],
        ["androidnd30order", "عدم التوسع حاليًا", "انخفاض صغير في التحويل والنشاط المبكر"],
        ["default", "الإبقاء في الإنتاج", "لا يوجد بديل أثبت تفوقًا ماليًا"],
    ], [2600, 2400, 5165])
    add_heading(doc, "خطة التجربة التالية", 2)
    for item in [
        "إبقاء default كخيار الإنتاج الحالي.",
        "إعادة اختبار androidndorder بعينة وفترة محددتين مسبقًا.",
        "اعتماد Net Revenue per User كمؤشر القرار الأساسي.",
        "استخدام Monetization وD1/D7/D30 كمؤشرات مساندة.",
        "تحديد حد أدنى للأثر التجاري قبل بدء التجربة الجديدة.",
        "عدم الإطلاق العام قبل نجاح تجربة تحقق مستقلة.",
    ]:
        add_number(doc, item)
    add_heading(doc, "قيمة المشروع للشركة", 2)
    add_bullet(doc, "يمنع اتخاذ قرار بناءً على أعلى عمود فقط.")
    add_bullet(doc, "يربط قرار المنتج بالإيراد وسلوك المستخدم معًا.")
    add_bullet(doc, "يكشف الإشارات السلبية قبل تعميمها.")
    add_bullet(doc, "يوفر Pipeline قابلة لإعادة التشغيل لأي تجربة جديدة.")
    add_callout(doc, "صياغة المناقشة", "المشروع لا يختار أعلى عمود في الرسم؛ بل يختبر هل الفرق حقيقي ومهم تجاريًا، ثم يحوله إلى قرار منتج منخفض المخاطر.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def page_methodology(doc: Document) -> None:
    add_page_title(doc, "09", "المنهجية وجودة البيانات", "شفافية نطاق الدراسة، التنظيف، الخصوصية وحدود الاستنتاج.")
    add_heading(doc, "أرقام الجودة", 2)
    add_table(doc, ["البند", "القيمة"], [
        ["مستخدمو التجربة", "934,270"], ["المعاملات المؤهلة", "11,256,114"],
        ["المعاملات المستبعدة", "1,729,869"], ["معاملات مكررة دقيقة", "0"],
        ["Gross Revenue المؤهل", "$4,981,893.06"], ["اختبارات المشروع الحالية", "14/14 ناجحة"],
    ], [6200, 3965])
    add_heading(doc, "قواعد المعالجة", 2)
    add_bullet(doc, "تحليل جميع مجموعات التجربة الخمس.")
    add_bullet(doc, "إدخال المستخدمين بلا معاملات في مقام مؤشرات المستخدم.")
    add_bullet(doc, "استبعاد المعاملات غير المرتبطة بمستخدمي التجربة.")
    add_bullet(doc, "تطبيق Right Censoring على نوافذ D1/D3/D7/D14/D30.")
    add_bullet(doc, "عدم حذف القيم المتطرفة دون دليل أنها أخطاء.")
    add_bullet(doc, "إجراء Winsorization وTrimming عند P99 كتحليل حساسية منفصل.")
    add_heading(doc, "القيم المتطرفة", 2)
    add_para(doc, "يوجد 9,343 مستخدمًا فوق P99 ويمثلون نحو 27.08% من Gross Revenue. لم تُحذف قيمهم من التحليل الأساسي؛ لأن ارتفاع الإيراد لا يثبت وجود خطأ.")
    add_heading(doc, "الخصوصية", 2)
    add_bullet(doc, "البيانات الخام تبقى محليًا.")
    add_bullet(doc, "الواجهة تقرأ Data Marts مجمعة فقط.")
    add_bullet(doc, "لا يوجد user_id في ملفات Data Marts.")
    add_bullet(doc, "ملفات CSV القابلة للتنزيل مجمعة وآمنة.")
    add_heading(doc, "حدود الدراسة", 2)
    add_bullet(doc, "النشاط الزمني مستنتج من الأحداث المالية لا من Sessions.")
    add_bullet(doc, "النتائج تخص نافذة البيانات الحالية ولا تثبت استمرار الأثر مستقبلًا.")
    add_bullet(doc, "تحليل القنوات لا يتضمن CAC أو ROAS.")
    add_bullet(doc, "نحتاج تجربة تحقق جديدة قبل نشر أي Variation.")
    add_callout(doc, "ما تقوله", "ذكر حدود الدراسة لا يضعف المشروع؛ بل يوضح أن القرار مبني على ما تسمح به البيانات دون ادعاءات أكبر من الدليل.", fill=PALE_TEAL, accent=TEAL)
    doc.add_page_break()


def add_qa(doc: Document) -> None:
    add_heading(doc, "أسئلة متوقعة من الدكتور وإجاباتها", 1)
    qa = [
        ("لماذا لم تختر أعلى ARPU؟", "لأن الفرق الوصفي قد ينتج عن التذبذب أو القيم المتطرفة. اختبرنا فرق المتوسط وفاصل الثقة وحجم الأثر، ولم يظهر فائز مالي مثبت."),
        ("لماذا شملت المستخدمين بلا معاملات؟", "لأن ARPU وMonetization يجب أن يقيسا جميع من دخلوا التجربة، لا المستخدمين الذين حققوا إيرادًا فقط؛ وإلا نرفع النتائج بصورة متحيزة."),
        ("لماذا استبعدت 1.73 مليون معاملة؟", "لأنها تخص مستخدمين غير موجودين في ملف تجربة A/B، وبالتالي لم يتم توزيعهم على المجموعات الخمس بصورة قابلة للمقارنة."),
        ("لماذا استخدمت Welch؟", "لأنه يقارن المتوسطات دون افتراض تساوي التباين، وهو أنسب للإيرادات التي تختلف في التشتت بين المجموعات."),
        ("لماذا استخدمت Mann-Whitney أيضًا؟", "كتحليل حساسية لتوزيع الإيرادات المنحرف وكثرة الأصفار والقيم المرتفعة."),
        ("لماذا صححت باستخدام Holm؟", "لأن تنفيذ 48 اختبارًا يرفع احتمال ظهور نتائج دالة بالصدفة. Holm يضبط هذا الخطر."),
        ("لماذا لم تحذف القيم المتطرفة؟", "لأنها قد تمثل مستخدمين حقيقيين مرتفعي الإيراد. حافظنا عليها، ثم نفذنا تحليل حساسية عند P99."),
        ("هل هذا Retention حقيقي؟", "هو Activity Retention مبني على الأحداث المالية، وليس Session Retention؛ وذكرنا هذا الحد بوضوح."),
        ("ما الفائدة إذا لم نجد فائزًا؟", "منع إطلاق تغيير غير مثبت قيمة عملية؛ كما حددنا androidndorder كمرشح أكثر وعدًا لتجربة تحقق جديدة."),
        ("هل يمكن نشر الداشبورد بأمان؟", "نعم من ناحية البيانات المعروضة؛ لأنها تقرأ Data Marts مجمعة بلا user_id، بينما تبقى البيانات الخام محليًا."),
    ]
    for question, answer in qa:
        add_heading(doc, question, 3)
        add_para(doc, answer, after=6)
    doc.add_page_break()


def add_final_script(doc: Document) -> None:
    add_heading(doc, "نص ختامي جاهز للمناقشة", 1)
    add_callout(
        doc,
        "الخاتمة",
        "بدأ المشروع بقرابة 934 ألف مستخدم ونحو 13 مليون معاملة. دققنا البيانات وحددنا 11.25 مليون معاملة مؤهلة، ثم بنينا جدولًا واحدًا لكل مستخدم وحسبنا المؤشرات المالية والسلوكية وRetention مع Right Censoring. قارنا أربع Variations مع default باستخدام Welch وMann-Whitney واختبارات النسب مع تصحيح Holm. ظهرت إشارات سلوكية صغيرة، لكن لم يثبت أي تحسن في متوسط الإيراد؛ لذلك أوصينا بالإبقاء على default وإعادة اختبار androidndorder. أخيرًا، عرضنا النتائج في Data Marts آمنة وDashboard سريعة دون نشر بيانات المستخدمين الخام.",
        fill=PALE_TEAL,
        accent=TEAL,
    )
    add_heading(doc, "أهم خمس رسائل تتذكرها", 2)
    for item in [
        "النطاق الصحيح: تحليل مستخدمي تجربة A/B فقط.",
        "وحدة التحليل: مستخدم واحد، وليس معاملة واحدة.",
        "أعلى عمود لا يعني فائزًا دون اختبار إحصائي وحجم أثر.",
        "لا يوجد Variation أثبت تحسنًا ماليًا؛ androidndorder مرشح لإعادة الاختبار فقط.",
        "المشروع يحوّل بيانات ضخمة إلى قرار قابل للتفسير وإعادة التشغيل وآمن للعرض.",
    ]:
        add_number(doc, item)
    add_heading(doc, "التحقق الحالي", 2)
    add_bullet(doc, "فحص الجاهزية: DEMO_READY.")
    add_bullet(doc, "14 من 14 اختبارًا ناجحًا.")
    add_bullet(doc, "الصفحات التسع تعمل بلا استثناءات.")
    add_bullet(doc, "تنزيل النتائج المجمعة يعمل، وفحص الخصوصية ناجح.")
    add_para(doc, "نهاية الدليل", bold=True, color=NAVY, size=12, align=WD_ALIGN_PARAGRAPH.CENTER, before=18)


def build() -> Path:
    doc = Document()
    configure_document(doc)
    add_cover(doc)
    add_opening(doc)
    page_overview(doc)
    page_system(doc)
    page_variations(doc)
    page_retention(doc)
    page_channels(doc)
    page_revenue(doc)
    page_statistics(doc)
    page_recommendations(doc)
    page_methodology(doc)
    add_qa(doc)
    add_final_script(doc)
    doc.core_properties.title = "الدليل الكامل لشرح لوحة تحليل JustPlay"
    doc.core_properties.subject = "FYP II Dashboard Explanation and Defense Guide"
    doc.core_properties.keywords = "JustPlay, FYP II, Dashboard, A/B Testing, Analytics"
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUTPUT)
    return OUTPUT


if __name__ == "__main__":
    print(build())
