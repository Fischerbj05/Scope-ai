import os
import re
import base64
from io import BytesIO
from datetime import datetime

import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from openai import OpenAI
import fitz

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.lib import colors

from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    PageBreak,
    NextPageTemplate,
    Table,
    TableStyle,
)

from reportlab.platypus.tableofcontents import TableOfContents


# ==========================================================
# PAGE CONFIG
# ==========================================================

st.set_page_config(
    page_title="Construction Scope AI",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# ==========================================================
# SESSION STATE
# ==========================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


# ==========================================================
# API KEY
# ==========================================================

load_dotenv()

api_key = None

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

if not api_key:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error(
        "OpenAI API key not found. "
        "Add OPENAI_API_KEY to Streamlit Secrets."
    )
    st.stop()

client = OpenAI(api_key=api_key)


# ==========================================================
# THEME VALUES
# ==========================================================

if st.session_state.dark_mode:

    PAGE_BG = "#0F141B"
    CARD_BG = "#151B24"
    CARD_ALT = "#1B2330"
    INPUT_BG = "#111820"
    TEXT_MAIN = "#F3F4F6"
    TEXT_MUTED = "#A5ADBA"
    BORDER = "#2C3542"
    ACCENT = "#5B8DEF"
    ACCENT_DARK = "#4776D0"
    HEADER_BG = "#121820"

else:

    PAGE_BG = "#F4F6F8"
    CARD_BG = "#FFFFFF"
    CARD_ALT = "#F8FAFC"
    INPUT_BG = "#FFFFFF"
    TEXT_MAIN = "#17212B"
    TEXT_MUTED = "#667085"
    BORDER = "#DCE1E7"
    ACCENT = "#2457A7"
    ACCENT_DARK = "#1E4787"
    HEADER_BG = "#FFFFFF"


# ==========================================================
# WEBSITE STYLES
# ==========================================================

st.markdown(
    f"""
    <style>

    /* PAGE */

    [data-testid="stAppViewContainer"] {{
        background: {PAGE_BG};
    }}

    [data-testid="stHeader"] {{
        background: transparent;
    }}

    [data-testid="stToolbar"] {{
        right: 1rem;
    }}

    .block-container {{
        max-width: 1160px;
        padding-top: 1rem;
        padding-bottom: 4rem;
    }}

    html, body, [class*="css"] {{
        font-family:
            -apple-system,
            BlinkMacSystemFont,
            "Segoe UI",
            Roboto,
            Helvetica,
            Arial,
            sans-serif;
    }}


    /* GLOBAL TEXT */

    h1, h2, h3, h4, h5, h6 {{
        color: {TEXT_MAIN} !important;
        letter-spacing: -0.015em;
    }}

    p {{
        color: {TEXT_MUTED};
    }}

    label {{
        color: {TEXT_MAIN} !important;
    }}


    /* HEADER */

    .product-header {{
        background: {HEADER_BG};
        border: 1px solid {BORDER};
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 20px;
    }}

    .brand-row {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .brand-mark {{
        width: 38px;
        height: 38px;
        border-radius: 8px;
        background: {ACCENT};
        color: white;
        font-size: 18px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
    }}

    .brand-title {{
        color: {TEXT_MAIN};
        font-size: 18px;
        font-weight: 700;
        line-height: 1.1;
    }}

    .brand-subtitle {{
        color: {TEXT_MUTED};
        font-size: 11px;
        margin-top: 3px;
    }}


    /* HERO */

    .hero {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 14px;
        padding: 34px 36px;
        margin-bottom: 24px;
    }}

    .hero-kicker {{
        color: {ACCENT};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.09em;
        text-transform: uppercase;
        margin-bottom: 10px;
    }}

    .hero-title {{
        color: {TEXT_MAIN};
        font-size: 34px;
        line-height: 1.12;
        letter-spacing: -0.035em;
        font-weight: 750;
        max-width: 720px;
        margin-bottom: 12px;
    }}

    .hero-text {{
        color: {TEXT_MUTED};
        font-size: 15px;
        line-height: 1.6;
        max-width: 800px;
    }}


    /* SECTION HEADERS */

    .section-number {{
        color: {ACCENT};
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}

    .section-title {{
        color: {TEXT_MAIN};
        font-size: 23px;
        font-weight: 700;
        margin-bottom: 3px;
    }}

    .section-copy {{
        color: {TEXT_MUTED};
        font-size: 13.5px;
        margin-bottom: 16px;
    }}


    /* CONTAINERS */

    div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: {CARD_BG};
        border: 1px solid {BORDER} !important;
        border-radius: 12px !important;
        box-shadow: none !important;
    }}


    /* TEXT INPUT */

    div[data-baseweb="input"] {{
        background: {INPUT_BG} !important;
        border-radius: 8px !important;
    }}

    div[data-testid="stTextInput"] input {{
        background: {INPUT_BG} !important;
        color: {TEXT_MAIN} !important;
        min-height: 44px;
        border-radius: 8px !important;
    }}

    div[data-testid="stTextInput"] input::placeholder {{
        color: {TEXT_MUTED} !important;
        opacity: 0.75;
    }}

    div[data-testid="stNumberInput"] input {{
        background: {INPUT_BG} !important;
        color: {TEXT_MAIN} !important;
    }}


    /* CAPTION */

    [data-testid="stCaptionContainer"] {{
        color: {TEXT_MUTED} !important;
    }}


    /* FILE UPLOADER */

    div[data-testid="stFileUploader"] {{
        background: transparent;
    }}

    div[data-testid="stFileUploaderDropzone"] {{
        background: {CARD_ALT};
        border: 1.5px dashed {BORDER};
        border-radius: 10px;
        padding-top: 18px;
        padding-bottom: 18px;
    }}

    div[data-testid="stFileUploaderDropzone"]:hover {{
        border-color: {ACCENT};
    }}


    /* BUTTONS */

    .stButton > button {{
        min-height: 48px;
        border-radius: 8px;
        font-size: 14px;
        font-weight: 650;
        transition: 0.15s ease;
    }}

    .stButton > button[kind="primary"] {{
        background: {ACCENT};
        color: white;
        border: 1px solid {ACCENT};
    }}

    .stButton > button[kind="primary"]:hover {{
        background: {ACCENT_DARK};
        border-color: {ACCENT_DARK};
    }}

    div[data-testid="stDownloadButton"] button {{
        min-height: 46px;
        border-radius: 8px;
        font-weight: 650;
    }}


    /* METRICS */

    div[data-testid="stMetric"] {{
        background: {CARD_BG};
        border: 1px solid {BORDER};
        border-radius: 10px;
        padding: 15px 17px;
        box-shadow: none;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {TEXT_MUTED} !important;
        font-size: 12px;
        font-weight: 600;
    }}

    div[data-testid="stMetricValue"] {{
        color: {TEXT_MAIN} !important;
        font-size: 23px;
        font-weight: 700;
    }}


    /* TABS */

    button[data-baseweb="tab"] {{
        color: {TEXT_MUTED};
        font-size: 13px;
        font-weight: 600;
    }}

    button[data-baseweb="tab"][aria-selected="true"] {{
        color: {ACCENT};
    }}


    /* ALERTS */

    div[data-testid="stAlert"] {{
        border-radius: 10px;
    }}


    /* DIVIDER */

    hr {{
        border-color: {BORDER} !important;
    }}


    /* FOOTER */

    .footer {{
        margin-top: 42px;
        padding-top: 17px;
        border-top: 1px solid {BORDER};
        text-align: center;
        color: {TEXT_MUTED};
        font-size: 11px;
    }}

    </style>
    """,
    unsafe_allow_html=True
)


# ==========================================================
# REPORT STRUCTURE
# ==========================================================

MAIN_SECTIONS = [
    "EXECUTIVE SUMMARY",
    "PROJECT RISK SUMMARY",
    "CHANGE REGISTER",
    "VISUAL DRAWING COMPARISON",
    "PROJECT AND JURISDICTION INFORMATION",
    "ORIGINAL REQUIREMENT",
    "REVISED REQUIREMENT",
    "DETAILED SCOPE COMPARISON",
    "QUANTITY AND TECHNICAL ANALYSIS",
    "DIRECT COST IMPACT",
    "INDIRECT COST IMPACT",
    "SCHEDULE IMPACT",
    "COORDINATION AND CODE REVIEW",
    "SAFETY IMPACT",
    "CONTRACT AND DOCUMENTATION RISK",
    "DOCUMENT CONFLICTS",
    "MISSING INFORMATION",
    "ASSUMPTIONS",
    "SUPPORTING REFERENCES",
    "RECOMMENDED ACTIONS",
    "RISK FLAGS",
    "FINAL ASSESSMENT",
]

QUICK_REPORT_SECTIONS = [
    "EXECUTIVE SUMMARY",
    "PROJECT RISK SUMMARY",
    "CHANGE REGISTER",
    "RECOMMENDED ACTIONS",
    "RISK FLAGS",
    "FINAL ASSESSMENT",
]

SUBSECTIONS = [
    "TOP CHANGES",
    "AFFECTED TRADES",
    "TOP COST RISKS",
    "TOP SCHEDULE RISKS",
    "TOP REGULATORY RISKS",
    "TOP DOCUMENTATION RISKS",
    "MOST IMPORTANT NEXT ACTION",
    "LABOR",
    "MATERIAL",
    "EQUIPMENT",
    "SUBCONTRACTORS AND VENDORS",
    "JURISDICTION",
    "STRUCTURAL",
    "MECHANICAL",
    "PLUMBING",
    "ELECTRICAL AND LIFE SAFETY",
    "ENVELOPE AND ENERGY",
    "ACCESSIBILITY",
    "REGULATORY REVIEW",
    "RED",
    "YELLOW",
    "GREEN",
]


# ==========================================================
# PDF TEXT EXTRACTION
# ==========================================================

def extract_pdf_text(uploaded_file):

    pdf_bytes = uploaded_file.getvalue()
    reader = PdfReader(BytesIO(pdf_bytes))

    text = ""

    for page_number, page in enumerate(reader.pages, start=1):

        page_text = page.extract_text() or ""

        text += (
            f"\n\n--- DOCUMENT: {uploaded_file.name} "
            f"| PAGE {page_number} ---\n"
        )

        text += page_text

    return text


# ==========================================================
# PDF IMAGE EXTRACTION
# ==========================================================

def pdf_pages_to_images(uploaded_file, max_pages):

    pdf_bytes = uploaded_file.getvalue()

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    images = []

    page_count = min(
        len(document),
        max_pages
    )

    for page_index in range(page_count):

        page = document.load_page(page_index)

        pix = page.get_pixmap(
            matrix=fitz.Matrix(1.7, 1.7),
            alpha=False
        )

        image_bytes = pix.tobytes("png")

        encoded = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        images.append(
            {
                "document": uploaded_file.name,
                "page": page_index + 1,
                "image_url": (
                    f"data:image/png;base64,{encoded}"
                )
            }
        )

    document.close()

    return images


# ==========================================================
# TEXT HELPERS
# ==========================================================

def clean_heading(text):

    text = text.strip()

    text = re.sub(
        r"^#{1,6}\s*",
        "",
        text
    )

    text = text.replace(
        "**",
        ""
    )

    return text.strip()


def format_inline_markdown(text):

    text = text.strip()

    text = (
        text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text
    )

    return text


def split_sections(analysis_text):

    sections = {}
    current_section = None

    for line in analysis_text.splitlines():

        clean = clean_heading(line.strip())
        upper = clean.upper()

        if upper in MAIN_SECTIONS:

            current_section = upper
            sections[current_section] = [upper]
            continue

        if current_section:
            sections[current_section].append(line)

    return sections


def section_text(
    analysis_text,
    section_name
):

    sections = split_sections(
        analysis_text
    )

    lines = sections.get(
        section_name,
        []
    )

    return "\n".join(lines)


def build_quick_report_text(
    analysis_text
):

    sections = split_sections(
        analysis_text
    )

    selected = []

    for section in QUICK_REPORT_SECTIONS:

        if section in sections:

            selected.extend(
                sections[section]
            )

            selected.append("")

    return "\n".join(selected)


def extract_field(
    analysis_text,
    field_name,
    default="UNKNOWN"
):

    pattern = re.compile(
        rf"\*{{0,2}}{re.escape(field_name)}"
        rf":\*{{0,2}}\s*(.+)",
        re.IGNORECASE
    )

    for line in analysis_text.splitlines():

        match = pattern.search(
            line.strip()
        )

        if match:

            return (
                match
                .group(1)
                .replace("**", "")
                .strip()
            )

    return default


def count_change_register_items(
    analysis_text
):

    matches = re.findall(
        r"\bCR-\d+\b",
        analysis_text
    )

    return len(set(matches))


def count_risk_flags(
    analysis_text,
    risk_name
):

    sections = split_sections(
        analysis_text
    )

    risk_lines = sections.get(
        "RISK FLAGS",
        []
    )

    current = None
    count = 0

    for line in risk_lines:

        clean = clean_heading(
            line.strip()
        ).upper()

        if clean in [
            "RED",
            "YELLOW",
            "GREEN"
        ]:

            current = clean
            continue

        if (
            current == risk_name.upper()
            and (
                line.strip().startswith("• ")
                or line.strip().startswith("- ")
            )
        ):

            count += 1

    return count


# ==========================================================
# MARKDOWN TABLE HELPERS
# ==========================================================

def looks_like_table_row(line):

    line = line.strip()

    return (
        line.startswith("|")
        and line.count("|") >= 2
    )


def is_table_separator(line):

    stripped = (
        line
        .replace("|", "")
        .replace("-", "")
        .replace(":", "")
        .replace(" ", "")
    )

    return stripped == ""


def parse_markdown_table(lines):

    rows = []

    for line in lines:

        if is_table_separator(line):
            continue

        cells = [
            cell.strip()
            for cell in
            line.strip("|").split("|")
        ]

        if cells:
            rows.append(cells)

    return rows


# ==========================================================
# PDF DOCUMENT TEMPLATE
# ==========================================================

class ConstructionReportTemplate(BaseDocTemplate):

    def __init__(
        self,
        filename,
        project_name="",
        company_name="",
        **kwargs
    ):

        self.project_name = (
            project_name
            or "Construction Project"
        )

        self.company_name = (
            company_name
            or ""
        )

        BaseDocTemplate.__init__(
            self,
            filename,
            pagesize=letter,
            leftMargin=0.7 * inch,
            rightMargin=0.7 * inch,
            topMargin=0.82 * inch,
            bottomMargin=0.72 * inch,
            **kwargs
        )

        cover_frame = Frame(
            0.8 * inch,
            0.8 * inch,
            letter[0] - 1.6 * inch,
            letter[1] - 1.6 * inch,
            id="cover"
        )

        report_frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="report"
        )

        cover_template = PageTemplate(
            id="cover",
            frames=[cover_frame]
        )

        report_template = PageTemplate(
            id="report",
            frames=[report_frame],
            onPage=self.draw_header_footer
        )

        self.addPageTemplates(
            [
                cover_template,
                report_template
            ]
        )


    def draw_header_footer(
        self,
        canvas,
        doc
    ):

        canvas.saveState()

        canvas.setStrokeColor(
            colors.HexColor("#D0D5DD")
        )

        canvas.setLineWidth(0.5)

        canvas.line(
            self.leftMargin,
            letter[1] - 0.55 * inch,
            letter[0] - self.rightMargin,
            letter[1] - 0.55 * inch
        )

        canvas.setFillColor(
            colors.HexColor("#344054")
        )

        canvas.setFont(
            "Helvetica-Bold",
            8
        )

        canvas.drawString(
            self.leftMargin,
            letter[1] - 0.42 * inch,
            self.project_name[:50]
        )

        canvas.setFont(
            "Helvetica",
            8
        )

        canvas.drawRightString(
            letter[0] - self.rightMargin,
            letter[1] - 0.42 * inch,
            "Construction Scope AI Analysis"
        )

        canvas.setStrokeColor(
            colors.HexColor("#D0D5DD")
        )

        canvas.line(
            self.leftMargin,
            0.52 * inch,
            letter[0] - self.rightMargin,
            0.52 * inch
        )

        canvas.setFillColor(
            colors.HexColor("#667085")
        )

        canvas.setFont(
            "Helvetica",
            8
        )

        if self.company_name:

            canvas.drawString(
                self.leftMargin,
                0.33 * inch,
                self.company_name[:45]
            )

        canvas.drawRightString(
            letter[0] - self.rightMargin,
            0.33 * inch,
            f"Page {doc.page}"
        )

        canvas.restoreState()


    def afterFlowable(
        self,
        flowable
    ):

        if not isinstance(
            flowable,
            Paragraph
        ):
            return

        if (
            flowable.style.name
            != "SectionHeading"
        ):
            return

        text = flowable.getPlainText()

        key = (
            "section_"
            + str(
                abs(
                    hash(
                        text
                        + str(self.page)
                    )
                )
            )
        )

        self.canv.bookmarkPage(
            key
        )

        self.canv.addOutlineEntry(
            text,
            key,
            level=0,
            closed=False
        )

        self.notify(
            "TOCEntry",
            (
                0,
                text,
                self.page,
                key
            )
        )


# ==========================================================
# TABLE WIDTHS
# ==========================================================

def table_width_ratios(header_row):

    normalized = [
        cell.lower().strip()
        for cell in header_row
    ]

    # CHANGE REGISTER
    if (
        len(normalized) == 7
        and normalized[0] == "id"
    ):

        return [
            0.08,
            0.30,
            0.18,
            0.10,
            0.11,
            0.11,
            0.12,
        ]

    # DETAILED SCOPE COMPARISON
    if (
        len(normalized) == 5
        and "scope area" in normalized[0]
    ):

        return [
            0.15,
            0.21,
            0.21,
            0.30,
            0.13,
        ]

    # QUANTITY TABLE
    if (
        len(normalized) == 4
        and normalized[0] == "item"
    ):

        return [
            0.34,
            0.22,
            0.22,
            0.22,
        ]

    # REFERENCES TABLE
    if (
        len(normalized) == 4
        and normalized[0] == "document"
    ):

        return [
            0.24,
            0.15,
            0.31,
            0.30,
        ]

    return None


# ==========================================================
# CREATE REPORT TABLE
# ==========================================================

def create_report_table(
    rows,
    available_width,
    cell_style
):

    if not rows:
        return None

    max_columns = max(
        len(row)
        for row in rows
    )

    normalized_rows = []

    for row in rows:

        padded = (
            row
            + [""] * (
                max_columns
                - len(row)
            )
        )

        normalized_rows.append(
            padded
        )

    formatted_rows = []

    for row in normalized_rows:

        formatted_rows.append(
            [
                Paragraph(
                    format_inline_markdown(
                        cell
                    ),
                    cell_style
                )
                for cell in row
            ]
        )

    ratios = table_width_ratios(
        normalized_rows[0]
    )

    if ratios:

        col_widths = [
            available_width * ratio
            for ratio in ratios
        ]

    else:

        col_widths = [
            available_width
            / max_columns
        ] * max_columns

    table = Table(
        formatted_rows,
        colWidths=col_widths,
        repeatRows=1,
        hAlign="LEFT"
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#344054")
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#D0D5DD")
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    5
                ),

                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [
                        colors.white,
                        colors.HexColor("#F9FAFB")
                    ]
                ),
            ]
        )
    )

    return table


# ==========================================================
# PDF EXECUTIVE DASHBOARD
# ==========================================================

def build_dashboard(
    analysis_text,
    document_width,
    label_style,
    value_style
):

    scope_change = extract_field(
        analysis_text,
        "POTENTIAL SCOPE CHANGE"
    )

    confidence = extract_field(
        analysis_text,
        "CONFIDENCE"
    )

    severity = extract_field(
        analysis_text,
        "SEVERITY"
    )

    review = extract_field(
        analysis_text,
        "REVIEW BEFORE PROCEEDING"
    )

    change_count = count_change_register_items(
        analysis_text
    )

    red_count = count_risk_flags(
        analysis_text,
        "RED"
    )

    yellow_count = count_risk_flags(
        analysis_text,
        "YELLOW"
    )

    data = [
        [
            Paragraph(
                "Potential Scope Change",
                label_style
            ),
            Paragraph(
                scope_change,
                value_style
            ),
            Paragraph(
                "Overall Severity",
                label_style
            ),
            Paragraph(
                severity,
                value_style
            ),
        ],
        [
            Paragraph(
                "Confidence",
                label_style
            ),
            Paragraph(
                confidence,
                value_style
            ),
            Paragraph(
                "Review Before Proceeding",
                label_style
            ),
            Paragraph(
                review,
                value_style
            ),
        ],
        [
            Paragraph(
                "Changes Identified",
                label_style
            ),
            Paragraph(
                str(change_count),
                value_style
            ),
            Paragraph(
                "Red / Yellow Flags",
                label_style
            ),
            Paragraph(
                f"{red_count} / {yellow_count}",
                value_style
            ),
        ],
    ]

    dashboard = Table(
        data,
        colWidths=[
            document_width * 0.28,
            document_width * 0.22,
            document_width * 0.28,
            document_width * 0.22,
        ]
    )

    dashboard.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#F9FAFB")
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#D0D5DD")
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8
                ),
            ]
        )
    )

    return dashboard


# ==========================================================
# CREATE PDF REPORT
# ==========================================================

def create_pdf_report(
    project_name,
    project_location,
    company_name,
    analysis_text,
    quick_mode=False
):

    report_text = (
        build_quick_report_text(
            analysis_text
        )
        if quick_mode
        else analysis_text
    )

    buffer = BytesIO()

    document = ConstructionReportTemplate(
        buffer,
        project_name=project_name,
        company_name=company_name
    )

    styles = getSampleStyleSheet()


    # ======================================================
    # PDF STYLES
    # ======================================================

    cover_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=31,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#101828"),
        spaceAfter=20
    )

    cover_project = ParagraphStyle(
        "CoverProject",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=21,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#344054"),
        spaceAfter=8
    )

    cover_detail = ParagraphStyle(
        "CoverDetail",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#667085"),
        spaceAfter=5
    )

    toc_title = ParagraphStyle(
        "TOCTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=19,
        leading=23,
        textColor=colors.HexColor("#101828"),
        spaceAfter=16
    )

    dashboard_title = ParagraphStyle(
        "DashboardTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=17,
        leading=21,
        textColor=colors.HexColor("#101828"),
        spaceAfter=12
    )

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#101828"),
        spaceBefore=20,
        spaceAfter=9,
        keepWithNext=True
    )

    subsection_style = ParagraphStyle(
        "SubsectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#344054"),
        spaceBefore=12,
        spaceAfter=5,
        keepWithNext=True
    )

    change_style = ParagraphStyle(
        "ChangeHeading",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#175CD3"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.4,
        leading=13.4,
        textColor=colors.HexColor("#344054"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-8,
        spaceAfter=4
    )

    numbered_style = ParagraphStyle(
        "NumberedText",
        parent=body_style,
        leftIndent=18,
        firstLineIndent=-13,
        spaceAfter=5
    )

    key_value_style = ParagraphStyle(
        "KeyValue",
        parent=body_style,
        spaceAfter=5
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=body_style,
        fontSize=7.5,
        leading=9.5,
        spaceAfter=0
    )

    dashboard_label = ParagraphStyle(
        "DashboardLabel",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=8.3,
        leading=11,
        textColor=colors.HexColor("#667085"),
        spaceAfter=0
    )

    dashboard_value = ParagraphStyle(
        "DashboardValue",
        parent=body_style,
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#101828"),
        spaceAfter=0
    )

    note_style = ParagraphStyle(
        "ReportNote",
        parent=body_style,
        fontSize=8.4,
        leading=11.5,
        textColor=colors.HexColor("#667085")
    )


    story = []


    # ======================================================
    # COVER
    # ======================================================

    story.append(
        Spacer(
            1,
            1.2 * inch
        )
    )

    story.append(
        Paragraph(
            (
                "Construction Scope AI Quick Report"
                if quick_mode
                else "Construction Scope AI Analysis"
            ),
            cover_title
        )
    )

    story.append(
        Paragraph(
            project_name
            or "Construction Project",
            cover_project
        )
    )

    if project_location:

        story.append(
            Paragraph(
                project_location,
                cover_detail
            )
        )

    if company_name:

        story.append(
            Paragraph(
                company_name,
                cover_detail
            )
        )

    story.append(
        Spacer(
            1,
            0.45 * inch
        )
    )

    story.append(
        Paragraph(
            "Scope Change • Cost Risk • Schedule Risk • "
            "Coordination • Documentation • Code Review",
            cover_detail
        )
    )

    story.append(
        Spacer(
            1,
            1.3 * inch
        )
    )

    story.append(
        Paragraph(
            "Preliminary Construction-Management Review",
            cover_detail
        )
    )

    story.append(
        Paragraph(
            datetime.now().strftime(
                "%B %d, %Y"
            ),
            cover_detail
        )
    )

    story.append(
        NextPageTemplate(
            "report"
        )
    )

    story.append(
        PageBreak()
    )


    # ======================================================
    # EXECUTIVE DASHBOARD
    # ======================================================

    story.append(
        Paragraph(
            "Executive Dashboard",
            dashboard_title
        )
    )

    story.append(
        build_dashboard(
            analysis_text,
            document.width,
            dashboard_label,
            dashboard_value
        )
    )

    story.append(
        Spacer(
            1,
            12
        )
    )


    # ======================================================
    # TABLE OF CONTENTS
    # ======================================================

    if not quick_mode:

        story.append(
            PageBreak()
        )

        story.append(
            Paragraph(
                "Table of Contents",
                toc_title
            )
        )

        toc = TableOfContents()

        toc.levelStyles = [
            ParagraphStyle(
                "TOCLevel1",
                fontName="Helvetica",
                fontSize=9.5,
                leading=14,
                leftIndent=0,
                rightIndent=8,
                textColor=colors.HexColor("#344054"),
                spaceBefore=3
            )
        ]

        story.append(toc)

        story.append(
            PageBreak()
        )


    # ======================================================
    # BODY
    # ======================================================

    lines = report_text.splitlines()

    index = 0

    while index < len(lines):

        clean = lines[index].strip()

        if not clean:

            story.append(
                Spacer(
                    1,
                    3
                )
            )

            index += 1
            continue

        if (
            clean.startswith("====")
            or clean in [
                "---",
                "***",
                "___"
            ]
        ):

            index += 1
            continue


        # TABLE
        if looks_like_table_row(
            clean
        ):

            table_lines = []

            while (
                index < len(lines)
                and looks_like_table_row(
                    lines[index].strip()
                )
            ):

                table_lines.append(
                    lines[index].strip()
                )

                index += 1

            rows = parse_markdown_table(
                table_lines
            )

            table = create_report_table(
                rows,
                document.width,
                table_cell_style
            )

            if table:

                story.append(
                    Spacer(
                        1,
                        5
                    )
                )

                story.append(
                    table
                )

                story.append(
                    Spacer(
                        1,
                        8
                    )
                )

            continue


        heading_text = clean_heading(
            clean
        )

        heading_upper = heading_text.upper()


        # MAIN SECTION
        if heading_upper in MAIN_SECTIONS:

            story.append(
                Paragraph(
                    heading_upper,
                    section_style
                )
            )

            index += 1
            continue


        # SUBSECTION
        if heading_upper in SUBSECTIONS:

            story.append(
                Paragraph(
                    heading_text.title(),
                    subsection_style
                )
            )

            index += 1
            continue


        # CHANGE HEADING
        if re.match(
            r"(?i)^change\s+\d+",
            heading_text
        ):

            story.append(
                Paragraph(
                    format_inline_markdown(
                        heading_text
                    ),
                    change_style
                )
            )

            index += 1
            continue


        # MARKDOWN SUBHEADING
        if (
            clean.startswith("## ")
            or clean.startswith("### ")
        ):

            story.append(
                Paragraph(
                    format_inline_markdown(
                        heading_text
                    ),
                    subsection_style
                )
            )

            index += 1
            continue


        # BULLET
        if (
            clean.startswith("• ")
            or clean.startswith("- ")
        ):

            story.append(
                Paragraph(
                    "• "
                    + format_inline_markdown(
                        clean[2:].strip()
                    ),
                    bullet_style
                )
            )

            index += 1
            continue


        # NUMBERED LIST
        number_match = re.match(
            r"^(\d+)\.\s+(.*)",
            clean
        )

        if number_match:

            story.append(
                Paragraph(
                    f"<b>{number_match.group(1)}.</b> "
                    + format_inline_markdown(
                        number_match.group(2)
                    ),
                    numbered_style
                )
            )

            index += 1
            continue


        # KEY VALUE
        label_match = re.match(
            r"^\*{0,2}"
            r"([A-Za-z0-9 /&()'’\-]+)"
            r":\*{0,2}\s*(.*)$",
            clean
        )

        if label_match:

            label = (
                label_match
                .group(1)
                .strip()
            )

            value = (
                label_match
                .group(2)
                .strip()
            )

            formatted = (
                "<b>"
                + format_inline_markdown(
                    label
                )
                + ":</b>"
            )

            if value:

                formatted += (
                    " "
                    + format_inline_markdown(
                        value
                    )
                )

            story.append(
                Paragraph(
                    formatted,
                    key_value_style
                )
            )

            index += 1
            continue


        # NORMAL TEXT
        story.append(
            Paragraph(
                format_inline_markdown(
                    clean
                ),
                body_style
            )
        )

        index += 1


    # ======================================================
    # DISCLAIMER
    # ======================================================

    story.append(
        Spacer(
            1,
            18
        )
    )

    story.append(
        Paragraph(
            "<b>Report limitation:</b> "
            "This analysis is a preliminary construction-management "
            "review. Findings should be verified against the executed "
            "contract, current issued-for-construction documents, "
            "project specifications, design-professional direction, "
            "field conditions, and requirements of the applicable "
            "Authority Having Jurisdiction.",
            note_style
        )
    )

    document.multiBuild(
        story
    )

    buffer.seek(0)

    return buffer.getvalue()


# ==========================================================
# AI ANALYSIS INSTRUCTIONS
# ==========================================================

ANALYSIS_INSTRUCTIONS = """
You are an advanced construction change-management and
document-analysis assistant.

Compare original construction documents against new or revised
construction documents and explain meaningful construction consequences.

Focus on helping project managers, estimators, superintendents,
general contractors, and subcontractors understand:

- what changed
- where it changed
- affected trades
- potential scope impact
- cost exposure
- schedule exposure
- coordination requirements
- documentation risk
- code or jurisdiction concerns
- recommended next action

Do not provide legal advice.

Do not make final contractual entitlement determinations.

Do not say payment is definitely owed.

Do not invent:
- contract language
- quantities
- dimensions
- prices
- dates
- delay durations
- code sections
- local amendments
- owner requirements
- company policies
- field conditions

Clearly distinguish confirmed facts, assumptions,
missing information, and items requiring verification.

Use document names, drawing sheets, and page numbers
whenever reasonably identifiable.

Do not repeat the same detailed explanation in multiple sections.

Keep summaries concise.

==================================================
EXECUTIVE SUMMARY
==================================================

POTENTIAL SCOPE CHANGE:
YES / NO / UNCERTAIN

CONFIDENCE:
HIGH / MEDIUM / LOW

SEVERITY:
HIGH / MEDIUM / LOW

CHANGE CATEGORY:

REVIEW BEFORE PROCEEDING:
YES / NO

SUMMARY:

Use no more than two short paragraphs.

==================================================
PROJECT RISK SUMMARY
==================================================

OVERALL PROJECT RISK:
HIGH / MEDIUM / LOW

TOP CHANGES

List no more than five.

AFFECTED TRADES

List only affected construction trades.

TOP COST RISKS

List no more than five.

TOP SCHEDULE RISKS

List no more than five.

TOP REGULATORY RISKS

List no more than five.

TOP DOCUMENTATION RISKS

List no more than five.

MOST IMPORTANT NEXT ACTION

Give one clear action.

==================================================
CHANGE REGISTER
==================================================

Use exactly this markdown table:

| ID | Change | Primary Trade | Cost Risk | Schedule Risk | Confidence | Source |

Use CR-01, CR-02, CR-03 and so on.

Keep wording concise.

==================================================
VISUAL DRAWING COMPARISON
==================================================

For each meaningful change use:

CHANGE 1 — Short Title

CHANGE:
Brief description.

PRIMARY TRADE:
Affected trade.

ORIGINAL SOURCE:
Drawing / sheet / page.

REVISED SOURCE:
Drawing / sheet / page.

ORIGINAL CONDITION:
Original condition.

REVISED CONDITION:
Revised condition.

COST RISK:
HIGH / MEDIUM / LOW / UNKNOWN

SCHEDULE RISK:
HIGH / MEDIUM / LOW / UNKNOWN

POTENTIAL IMPACT:
Practical construction consequence.

RECOMMENDED ACTION:
Next action.

CONFIDENCE:
HIGH / MEDIUM / LOW

==================================================
PROJECT AND JURISDICTION INFORMATION
==================================================

PROJECT NAME:

PROJECT LOCATION:

CITY:

COUNTY:

STATE:

COUNTRY:

OWNER:

GENERAL CONTRACTOR:

SUBCONTRACTOR:

DESIGN PROFESSIONAL:

AUTHORITY HAVING JURISDICTION:

PROJECT TYPE:

APPLICABLE CODE INFORMATION:

PROJECT-SPECIFIC STANDARDS:

==================================================
ORIGINAL REQUIREMENT
==================================================

Describe the baseline requirement.

Do not call drawing scope confirmed contractual scope
unless an executed contract or subcontract was supplied.

==================================================
REVISED REQUIREMENT
==================================================

Describe meaningful additions, deletions,
relocations, quantity changes, material changes,
equipment changes, and dimensional changes.

==================================================
DETAILED SCOPE COMPARISON
==================================================

Use:

| Scope Area | Original | Revised | Potential Impact | Source |

Keep entries concise.

==================================================
QUANTITY AND TECHNICAL ANALYSIS
==================================================

When quantities are confirmed use:

| Item | Original | Revised | Net Change |

Do not invent missing quantities.

==================================================
DIRECT COST IMPACT
==================================================

LABOR

MATERIAL

EQUIPMENT

SUBCONTRACTORS AND VENDORS

Only list relevant impacts.

Do not invent prices.

==================================================
INDIRECT COST IMPACT
==================================================

Include only relevant project-management,
engineering, permitting, inspection, disruption,
remobilization, productivity, documentation,
storage, cancellation, or general-condition exposure.

==================================================
SCHEDULE IMPACT
==================================================

POTENTIAL SCHEDULE IMPACT:
HIGH / MEDIUM / LOW / UNKNOWN

Explain major sequencing, procurement,
approval, inspection, and rework risks.

Do not invent delay days.

==================================================
COORDINATION AND CODE REVIEW
==================================================

JURISDICTION

STRUCTURAL

MECHANICAL

PLUMBING

ELECTRICAL AND LIFE SAFETY

ENVELOPE AND ENERGY

ACCESSIBILITY

REGULATORY REVIEW

Do not invent code sections.

==================================================
SAFETY IMPACT
==================================================

Include only safety concerns directly related
to identified changes.

==================================================
CONTRACT AND DOCUMENTATION RISK
==================================================

Address relevant revision control,
transmittals, RFIs, written direction,
authorization, notices, photographs,
daily reports, labor records, purchase orders,
delivery tickets, and vendor records.

Do not provide legal advice.

==================================================
DOCUMENT CONFLICTS
==================================================

List meaningful conflicts only.

==================================================
MISSING INFORMATION
==================================================

List only information that materially affects
the analysis or next action.

==================================================
ASSUMPTIONS
==================================================

List material assumptions only.

==================================================
SUPPORTING REFERENCES
==================================================

Use:

| Document | Page / Sheet | Requirement or Change | Why It Matters |

==================================================
RECOMMENDED ACTIONS
==================================================

Provide a prioritized numbered list.

==================================================
RISK FLAGS
==================================================

RED

Serious issues requiring immediate review.

YELLOW

Issues requiring clarification or monitoring.

GREEN

Important reviewed areas where no material
change was identified.

==================================================
FINAL ASSESSMENT
==================================================

Use no more than three concise paragraphs.

Summarize the scope conclusion, major cost risk,
major schedule risk, major coordination risk,
regulatory concern, documentation concern,
and recommended next action.
"""


# ==========================================================
# HEADER
# ==========================================================

header_left, header_right = st.columns(
    [5, 1]
)

with header_left:

    st.markdown(
        """
        <div class="product-header">
            <div class="brand-row">
                <div class="brand-mark">C</div>
                <div>
                    <div class="brand-title">
                        Construction Scope AI
                    </div>
                    <div class="brand-subtitle">
                        Construction change and scope review
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with header_right:

    new_dark_mode = st.toggle(
        "Dark mode",
        value=st.session_state.dark_mode
    )

    if new_dark_mode != st.session_state.dark_mode:

        st.session_state.dark_mode = new_dark_mode
        st.rerun()


# ==========================================================
# HERO
# ==========================================================

st.markdown(
    """
    <div class="hero">

        <div class="hero-kicker">
            Construction Document Review
        </div>

        <div class="hero-title">
            Understand what changed before it affects the job.
        </div>

        <div class="hero-text">
            Compare original and revised construction documents
            to identify meaningful scope changes, affected trades,
            potential cost and schedule exposure, coordination issues,
            and recommended next actions.
        </div>

    </div>
    """,
    unsafe_allow_html=True
)


# ==========================================================
# STEP 1 — PROJECT SETUP
# ==========================================================

st.markdown(
    """
    <div class="section-number">Step 1</div>
    <div class="section-title">Project setup</div>
    <div class="section-copy">
        Enter the project information that should appear in the analysis
        and generated reports.
    </div>
    """,
    unsafe_allow_html=True
)

with st.container(border=True):

    left, right = st.columns(2)

    with left:

        st.markdown("#### Project name")
        st.caption(
            "The name used to identify this job."
        )

        project_name = st.text_input(
            "Project name input",
            placeholder="Building A Renovation",
            label_visibility="collapsed"
        )

        st.markdown("#### Contractor / company")
        st.caption(
            "The company reviewing or managing the project."
        )

        company_name = st.text_input(
            "Company input",
            placeholder="ABC Construction",
            label_visibility="collapsed"
        )

    with right:

        st.markdown("#### Project location")
        st.caption(
            "City and state where the work is located."
        )

        project_location = st.text_input(
            "Project location input",
            placeholder="Johnson City, Tennessee",
            label_visibility="collapsed"
        )

        st.markdown("#### Project number")
        st.caption(
            "Optional internal job number or reference."
        )

        project_reference = st.text_input(
            "Project reference input",
            placeholder="26-1047",
            label_visibility="collapsed"
        )


st.write("")


# ==========================================================
# STEP 2 — DOCUMENTS
# ==========================================================

st.markdown(
    """
    <div class="section-number">Step 2</div>
    <div class="section-title">Project documents</div>
    <div class="section-copy">
        Upload the baseline documents and the documents you want
        compared against them.
    </div>
    """,
    unsafe_allow_html=True
)

upload_left, upload_right = st.columns(2)

with upload_left:

    with st.container(border=True):

        st.markdown("### Original / baseline")

        st.caption(
            "Original drawings, contract documents, scope exhibits, "
            "specifications, or other baseline information."
        )

        original_files = st.file_uploader(
            "Original documents",
            type=["pdf"],
            accept_multiple_files=True,
            key="original_documents",
            label_visibility="collapsed"
        )

        if original_files:

            st.success(
                f"{len(original_files)} document(s) ready"
            )

with upload_right:

    with st.container(border=True):

        st.markdown("### New / revised")

        st.caption(
            "Revised drawings, bulletins, RFIs, directives, "
            "or newly issued project documents."
        )

        revised_files = st.file_uploader(
            "Revised documents",
            type=["pdf"],
            accept_multiple_files=True,
            key="revised_documents",
            label_visibility="collapsed"
        )

        if revised_files:

            st.success(
                f"{len(revised_files)} document(s) ready"
            )


st.write("")


# ==========================================================
# STEP 3 — SETTINGS
# ==========================================================

st.markdown(
    """
    <div class="section-number">Step 3</div>
    <div class="section-title">Analysis settings</div>
    <div class="section-copy">
        Configure the drawing review and start the comparison.
    </div>
    """,
    unsafe_allow_html=True
)

with st.container(border=True):

    setting_left, setting_right = st.columns(
        [1.4, 1]
    )

    with setting_left:

        st.markdown(
            "#### Visual drawing analysis"
        )

        visual_analysis = st.checkbox(
            "Review drawing pages visually",
            value=True
        )

        st.caption(
            "Recommended for architectural, structural, "
            "mechanical, electrical, and other graphical plans."
        )

    with setting_right:

        st.markdown(
            "#### Visual page limit"
        )

        max_pages = st.number_input(
            "Maximum pages",
            min_value=1,
            max_value=20,
            value=6,
            label_visibility="collapsed"
        )

        st.caption(
            "For early testing, 3–6 pages per PDF is a good range."
        )

    st.write("")

    analyze_clicked = st.button(
        "Analyze project",
        type="primary",
        use_container_width=True
    )


# ==========================================================
# RUN ANALYSIS
# ==========================================================

if analyze_clicked:

    if not original_files:

        st.error(
            "Upload at least one original or baseline document."
        )

    elif not revised_files:

        st.error(
            "Upload at least one new or revised document."
        )

    else:

        with st.spinner(
            "Reviewing project documents and comparing revisions..."
        ):

            try:

                original_text = ""
                revised_text = ""

                original_images = []
                revised_images = []


                # ORIGINAL FILES
                for file in original_files:

                    original_text += (
                        extract_pdf_text(
                            file
                        )
                    )

                    if visual_analysis:

                        original_images.extend(
                            pdf_pages_to_images(
                                file,
                                int(max_pages)
                            )
                        )


                # REVISED FILES
                for file in revised_files:

                    revised_text += (
                        extract_pdf_text(
                            file
                        )
                    )

                    if visual_analysis:

                        revised_images.extend(
                            pdf_pages_to_images(
                                file,
                                int(max_pages)
                            )
                        )


                prompt_text = f"""
PROJECT INFORMATION PROVIDED BY USER

Project Name:
{project_name}

Project Number / Reference:
{project_reference}

Project Location:
{project_location}

Contractor / Company:
{company_name}


==================================================
ORIGINAL / BASELINE DOCUMENT TEXT
==================================================

{original_text}


==================================================
NEW / REVISED DOCUMENT TEXT
==================================================

{revised_text}


Compare these documents using the required report structure.

Use supplied documents as the primary evidence.

If user-entered information conflicts with the project documents,
report the conflict rather than silently resolving it.

Prioritize meaningful construction changes over cosmetic
or drafting differences.
"""


                content = [
                    {
                        "type": "input_text",
                        "text": prompt_text
                    }
                ]


                # ORIGINAL IMAGES
                for image in original_images:

                    content.append(
                        {
                            "type": "input_text",
                            "text": (
                                "ORIGINAL DRAWING IMAGE\n"
                                f"DOCUMENT: {image['document']}\n"
                                f"PAGE: {image['page']}"
                            )
                        }
                    )

                    content.append(
                        {
                            "type": "input_image",
                            "image_url": image["image_url"],
                            "detail": "high"
                        }
                    )


                # REVISED IMAGES
                for image in revised_images:

                    content.append(
                        {
                            "type": "input_text",
                            "text": (
                                "REVISED DRAWING IMAGE\n"
                                f"DOCUMENT: {image['document']}\n"
                                f"PAGE: {image['page']}"
                            )
                        }
                    )

                    content.append(
                        {
                            "type": "input_image",
                            "image_url": image["image_url"],
                            "detail": "high"
                        }
                    )


                response = client.responses.create(
                    model="gpt-5.6",
                    reasoning={
                        "effort": "medium"
                    },
                    instructions=ANALYSIS_INSTRUCTIONS,
                    input=[
                        {
                            "role": "user",
                            "content": content
                        }
                    ]
                )


                analysis = response.output_text


                st.session_state["analysis"] = analysis

                st.session_state[
                    "project_name"
                ] = project_name

                st.session_state[
                    "project_location"
                ] = project_location

                st.session_state[
                    "company_name"
                ] = company_name

                st.session_state[
                    "project_reference"
                ] = project_reference


                st.success(
                    "Analysis complete."
                )

            except Exception as error:

                st.error(
                    "The analysis could not be completed."
                )

                st.code(
                    str(error)
                )


# ==========================================================
# RESULTS
# ==========================================================

if "analysis" in st.session_state:

    analysis = st.session_state[
        "analysis"
    ]

    st.write("")
    st.write("")

    st.markdown(
        """
        <div class="section-number">Results</div>
        <div class="section-title">Project review</div>
        <div class="section-copy">
            Review the highest-priority findings first, then open the
            detailed sections as needed.
        </div>
        """,
        unsafe_allow_html=True
    )


    # ======================================================
    # METRICS
    # ======================================================

    scope_change = extract_field(
        analysis,
        "POTENTIAL SCOPE CHANGE"
    )

    severity = extract_field(
        analysis,
        "SEVERITY"
    )

    confidence = extract_field(
        analysis,
        "CONFIDENCE"
    )

    review_status = extract_field(
        analysis,
        "REVIEW BEFORE PROCEEDING"
    )

    changes_found = (
        count_change_register_items(
            analysis
        )
    )

    red_flags = count_risk_flags(
        analysis,
        "RED"
    )

    metric1, metric2, metric3, metric4 = st.columns(
        4
    )

    with metric1:

        st.metric(
            "Scope change",
            scope_change
        )

    with metric2:

        st.metric(
            "Severity",
            severity
        )

    with metric3:

        st.metric(
            "Changes identified",
            changes_found
        )

    with metric4:

        st.metric(
            "Red flags",
            red_flags
        )


    st.write("")


    # ======================================================
    # REVIEW STATUS
    # ======================================================

    with st.container(border=True):

        status1, status2, status3 = st.columns(
            3
        )

        with status1:

            st.markdown(
                "**Analysis confidence**"
            )

            st.write(
                confidence
            )

        with status2:

            st.markdown(
                "**Review before proceeding**"
            )

            st.write(
                review_status
            )

        with status3:

            st.markdown(
                "**Project**"
            )

            st.write(
                st.session_state.get(
                    "project_name",
                    "Not provided"
                )
                or "Not provided"
            )


    st.write("")


    # ======================================================
    # RESULT TABS
    # ======================================================

    summary_tab, change_tab, full_tab = st.tabs(
        [
            "Executive summary",
            "Change register",
            "Full analysis"
        ]
    )


    with summary_tab:

        st.markdown(
            section_text(
                analysis,
                "EXECUTIVE SUMMARY"
            )
        )

        st.divider()

        st.markdown(
            section_text(
                analysis,
                "PROJECT RISK SUMMARY"
            )
        )


    with change_tab:

        st.markdown(
            section_text(
                analysis,
                "CHANGE REGISTER"
            )
        )

        st.divider()

        st.markdown(
            section_text(
                analysis,
                "RECOMMENDED ACTIONS"
            )
        )


    with full_tab:

        st.markdown(
            analysis
        )


    # ======================================================
    # CREATE PDF REPORTS
    # ======================================================

    quick_pdf = create_pdf_report(

        st.session_state.get(
            "project_name",
            ""
        ),

        st.session_state.get(
            "project_location",
            ""
        ),

        st.session_state.get(
            "company_name",
            ""
        ),

        analysis,

        quick_mode=True
    )


    full_pdf = create_pdf_report(

        st.session_state.get(
            "project_name",
            ""
        ),

        st.session_state.get(
            "project_location",
            ""
        ),

        st.session_state.get(
            "company_name",
            ""
        ),

        analysis,

        quick_mode=False
    )


    safe_name = (
        st.session_state
        .get(
            "project_name",
            "Project"
        )
        .strip()
        .replace(
            " ",
            "_"
        )
    )

    if not safe_name:
        safe_name = "Project"


    # ======================================================
    # EXPORT
    # ======================================================

    st.write("")
    st.write("")

    st.markdown(
        """
        <div class="section-number">Export</div>
        <div class="section-title">Project reports</div>
        <div class="section-copy">
            Download a short management report or the complete
            supporting analysis.
        </div>
        """,
        unsafe_allow_html=True
    )

    export_left, export_right = st.columns(
        2
    )


    with export_left:

        with st.container(border=True):

            st.markdown(
                "### Quick report"
            )

            st.caption(
                "Executive summary, major project risks, "
                "change register, risk flags, and recommended actions."
            )

            st.download_button(
                "Download quick report",
                data=quick_pdf,
                file_name=(
                    f"{safe_name}_Quick_Report.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )


    with export_right:

        with st.container(border=True):

            st.markdown(
                "### Full analysis"
            )

            st.caption(
                "Detailed scope comparison, cost and schedule review, "
                "coordination issues, document risk, and references."
            )

            st.download_button(
                "Download full report",
                data=full_pdf,
                file_name=(
                    f"{safe_name}_Full_Scope_Analysis.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )


# ==========================================================
# FOOTER
# ==========================================================

st.markdown(
    """
    <div class="footer">
        Construction Scope AI · Preliminary construction-management
        analysis · Verify findings against current project documents
        and qualified project personnel.
    </div>
    """,
    unsafe_allow_html=True
)
