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
# WEBSITE STYLING
# ==========================================================

st.markdown(
    """
    <style>

    /* =====================================================
       GLOBAL
    ===================================================== */

    [data-testid="stAppViewContainer"] {
        background: #f5f7fa;
    }

    [data-testid="stHeader"] {
        background: rgba(255,255,255,0);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 1.2rem;
        padding-bottom: 4rem;
    }

    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                     Roboto, Helvetica, Arial, sans-serif;
    }

    h1, h2, h3 {
        color: #101828;
        letter-spacing: -0.02em;
    }


    /* =====================================================
       TOP NAV
    ===================================================== */

    .top-nav {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        padding: 14px 20px;
        margin-bottom: 18px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 1px 3px rgba(16,24,40,0.04);
    }

    .brand-wrap {
        display: flex;
        align-items: center;
        gap: 12px;
    }

    .brand-icon {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: #175cd3;
        color: white;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
    }

    .brand-name {
        font-size: 18px;
        font-weight: 700;
        color: #101828;
        margin: 0;
    }

    .brand-sub {
        font-size: 11px;
        color: #667085;
        margin-top: 1px;
    }

    .nav-badge {
        background: #eff4ff;
        color: #175cd3;
        border: 1px solid #d1e0ff;
        border-radius: 999px;
        padding: 6px 12px;
        font-size: 12px;
        font-weight: 600;
    }


    /* =====================================================
       HERO
    ===================================================== */

    .hero {
        background:
            linear-gradient(135deg, #101828 0%, #1d2939 60%, #344054 100%);
        border-radius: 20px;
        padding: 42px 44px;
        margin-bottom: 22px;
        box-shadow: 0 12px 32px rgba(16,24,40,0.12);
    }

    .hero-eyebrow {
        display: inline-block;
        background: rgba(255,255,255,0.09);
        border: 1px solid rgba(255,255,255,0.13);
        border-radius: 999px;
        padding: 6px 11px;
        font-size: 12px;
        font-weight: 600;
        color: #d1e9ff;
        margin-bottom: 16px;
    }

    .hero h1 {
        color: #ffffff !important;
        font-size: 38px;
        line-height: 1.1;
        margin: 0 0 14px 0;
        max-width: 760px;
    }

    .hero p {
        color: #d0d5dd;
        font-size: 17px;
        line-height: 1.6;
        max-width: 820px;
        margin: 0;
    }

    .hero-highlight {
        color: #84adff;
        font-weight: 600;
    }


    /* =====================================================
       FEATURE CARDS
    ===================================================== */

    .feature-card {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 14px;
        padding: 18px;
        min-height: 135px;
        box-shadow: 0 1px 3px rgba(16,24,40,0.04);
    }

    .feature-icon {
        font-size: 22px;
        margin-bottom: 8px;
    }

    .feature-title {
        font-size: 14px;
        font-weight: 700;
        color: #101828;
        margin-bottom: 5px;
    }

    .feature-text {
        font-size: 12.5px;
        color: #667085;
        line-height: 1.45;
    }


    /* =====================================================
       SECTION LABEL
    ===================================================== */

    .section-label {
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #175cd3;
        margin-bottom: 5px;
    }

    .section-title {
        font-size: 23px;
        font-weight: 700;
        color: #101828;
        margin-bottom: 4px;
    }

    .section-description {
        font-size: 14px;
        color: #667085;
        margin-bottom: 18px;
    }


    /* =====================================================
       NATIVE STREAMLIT CONTAINERS
    ===================================================== */

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff;
        border: 1px solid #e4e7ec !important;
        border-radius: 14px !important;
        box-shadow: 0 1px 3px rgba(16,24,40,0.04);
    }


    /* =====================================================
       INPUTS
    ===================================================== */

    div[data-baseweb="input"] {
        border-radius: 9px;
    }

    div[data-testid="stTextInput"] input {
        border-radius: 9px;
        min-height: 44px;
    }

    div[data-testid="stNumberInput"] input {
        border-radius: 9px;
    }


    /* =====================================================
       FILE UPLOADERS
    ===================================================== */

    div[data-testid="stFileUploader"] {
        background: #fafbfc;
        border-radius: 12px;
    }

    div[data-testid="stFileUploaderDropzone"] {
        border: 1.5px dashed #b8c2d1;
        border-radius: 12px;
        background: #f9fafb;
        padding-top: 20px;
        padding-bottom: 20px;
    }

    div[data-testid="stFileUploaderDropzone"]:hover {
        border-color: #175cd3;
        background: #f5f8ff;
    }


    /* =====================================================
       BUTTONS
    ===================================================== */

    .stButton > button {
        min-height: 50px;
        border-radius: 10px;
        font-weight: 700;
        font-size: 15px;
        border: none;
        transition: all .18s ease;
    }

    .stButton > button[kind="primary"] {
        background: #175cd3;
        color: white;
    }

    .stButton > button[kind="primary"]:hover {
        background: #1849a9;
        box-shadow: 0 5px 14px rgba(23,92,211,0.22);
        transform: translateY(-1px);
    }

    div[data-testid="stDownloadButton"] button {
        min-height: 48px;
        border-radius: 10px;
        font-weight: 650;
    }


    /* =====================================================
       METRICS
    ===================================================== */

    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e4e7ec;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 1px 3px rgba(16,24,40,0.04);
    }

    div[data-testid="stMetricLabel"] {
        font-size: 12px;
        color: #667085;
        font-weight: 600;
    }

    div[data-testid="stMetricValue"] {
        font-size: 23px;
        color: #101828;
        font-weight: 700;
    }


    /* =====================================================
       TABS
    ===================================================== */

    button[data-baseweb="tab"] {
        font-weight: 600;
        font-size: 14px;
    }


    /* =====================================================
       INFO BOXES
    ===================================================== */

    div[data-testid="stAlert"] {
        border-radius: 12px;
    }


    /* =====================================================
       FOOTER
    ===================================================== */

    .site-footer {
        margin-top: 45px;
        padding-top: 18px;
        border-top: 1px solid #e4e7ec;
        color: #98a2b3;
        text-align: center;
        font-size: 11px;
    }

    </style>
    """,
    unsafe_allow_html=True
)


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
# PDF TEXT
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
# PDF IMAGES
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

        encoded = base64.b64encode(
            pix.tobytes("png")
        ).decode("utf-8")

        images.append(
            {
                "document": uploaded_file.name,
                "page": page_index + 1,
                "image_url": f"data:image/png;base64,{encoded}"
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

    text = text.replace("**", "")

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


def section_text(analysis_text, section_name):

    sections = split_sections(analysis_text)

    lines = sections.get(
        section_name,
        []
    )

    return "\n".join(lines)


def build_quick_report_text(analysis_text):

    sections = split_sections(analysis_text)

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


def count_change_register_items(analysis_text):

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
# MARKDOWN TABLES
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
            for cell in line.strip("|").split("|")
        ]

        if cells:
            rows.append(cells)

    return rows


# ==========================================================
# PDF TEMPLATE
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

        self.addPageTemplates(
            [
                PageTemplate(
                    id="cover",
                    frames=[cover_frame]
                ),
                PageTemplate(
                    id="report",
                    frames=[report_frame],
                    onPage=self.draw_header_footer
                ),
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

        if flowable.style.name != "SectionHeading":
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

        self.canv.bookmarkPage(key)

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
# CREATE PDF TABLE
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

        normalized_rows.append(
            row
            + [""] * (
                max_columns - len(row)
            )
        )

    formatted_rows = []

    for row in normalized_rows:

        formatted_rows.append(
            [
                Paragraph(
                    format_inline_markdown(cell),
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
            available_width / max_columns
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
# PDF DASHBOARD
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
# CREATE PDF
# ==========================================================

def create_pdf_report(
    project_name,
    project_location,
    company_name,
    analysis_text,
    quick_mode=False
):

    report_text = (
        build_quick_report_text(analysis_text)
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

    # COVER
    story.append(Spacer(1, 1.2 * inch))

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
            project_name or "Construction Project",
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
            datetime.now().strftime("%B %d, %Y"),
            cover_detail
        )
    )

    story.append(
        NextPageTemplate("report")
    )

    story.append(
        PageBreak()
    )

    # EXECUTIVE DASHBOARD
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

    # FULL REPORT TOC
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
        story.append(PageBreak())

    # BODY
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
            or clean in ["---", "***", "___"]
        ):

            index += 1
            continue

        if looks_like_table_row(clean):

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

                story.append(table)

                story.append(
                    Spacer(
                        1,
                        8
                    )
                )

            continue

        heading_text = clean_heading(clean)
        heading_upper = heading_text.upper()

        if heading_upper in MAIN_SECTIONS:

            story.append(
                Paragraph(
                    heading_upper,
                    section_style
                )
            )

            index += 1
            continue

        if heading_upper in SUBSECTIONS:

            story.append(
                Paragraph(
                    heading_text.title(),
                    subsection_style
                )
            )

            index += 1
            continue

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

        label_match = re.match(
            r"^\*{0,2}"
            r"([A-Za-z0-9 /&()'’\-]+)"
            r":\*{0,2}\s*(.*)$",
            clean
        )

        if label_match:

            label = label_match.group(1).strip()
            value = label_match.group(2).strip()

            formatted = (
                "<b>"
                + format_inline_markdown(label)
                + ":</b>"
            )

            if value:

                formatted += (
                    " "
                    + format_inline_markdown(value)
                )

            story.append(
                Paragraph(
                    formatted,
                    key_value_style
                )
            )

            index += 1
            continue

        story.append(
            Paragraph(
                format_inline_markdown(clean),
                body_style
            )
        )

        index += 1

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

    document.multiBuild(story)

    buffer.seek(0)

    return buffer.getvalue()


# ==========================================================
# AI INSTRUCTIONS
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
# TOP NAVIGATION
# ==========================================================

st.markdown(
    """
    <div class="top-nav">
        <div class="brand-wrap">
            <div class="brand-icon">🏗️</div>
            <div>
                <div class="brand-name">Construction Scope AI</div>
                <div class="brand-sub">
                    Construction change intelligence
                </div>
            </div>
        </div>
        <div class="nav-badge">Early Access</div>
    </div>
    """,
    unsafe_allow_html=True
)


# ==========================================================
# HERO
# ==========================================================

st.markdown(
    """
    <div class="hero">
        <div class="hero-eyebrow">
            AI-POWERED CHANGE MANAGEMENT
        </div>

        <h1>
            Turn drawing revisions into
            construction decisions.
        </h1>

        <p>
            Compare original and revised project documents to identify
            <span class="hero-highlight">scope changes</span>,
            affected trades, cost exposure, schedule risk,
            coordination issues, and recommended next actions.
        </p>
    </div>
    """,
    unsafe_allow_html=True
)


# ==========================================================
# FEATURE STRIP
# ==========================================================

feature1, feature2, feature3 = st.columns(3)

with feature1:

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">🔎</div>
            <div class="feature-title">Find Meaningful Changes</div>
            <div class="feature-text">
                Compare baseline and revised documents while filtering
                out irrelevant drafting differences.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with feature2:

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">⚠️</div>
            <div class="feature-title">Understand Project Risk</div>
            <div class="feature-text">
                Identify potential cost, schedule, coordination,
                documentation, and regulatory exposure.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with feature3:

    st.markdown(
        """
        <div class="feature-card">
            <div class="feature-icon">📄</div>
            <div class="feature-title">Create Actionable Reports</div>
            <div class="feature-text">
                Generate management-ready quick reports and detailed
                supporting analysis.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


st.write("")


# ==========================================================
# STEP 1
# ==========================================================

st.markdown(
    """
    <div class="section-label">Step 1</div>
    <div class="section-title">Set up your project</div>
    <div class="section-description">
        Add basic project information that will appear in the analysis
        and generated reports.
    </div>
    """,
    unsafe_allow_html=True
)

with st.container(border=True):

    left, right = st.columns(2)

    with left:

        project_name = st.text_input(
            "Project Name",
            placeholder="Example: Building A Renovation"
        )

        company_name = st.text_input(
            "Contractor / Company",
            placeholder="Example: ABC Construction"
        )

    with right:

        project_location = st.text_input(
            "Project Location",
            placeholder="Example: Johnson City, Tennessee"
        )

        project_reference = st.text_input(
            "Project Number / Reference",
            placeholder="Optional"
        )


st.write("")


# ==========================================================
# STEP 2
# ==========================================================

st.markdown(
    """
    <div class="section-label">Step 2</div>
    <div class="section-title">Upload project documents</div>
    <div class="section-description">
        Add the baseline documents on the left and the newer or revised
        documents on the right.
    </div>
    """,
    unsafe_allow_html=True
)

upload_left, upload_right = st.columns(2)

with upload_left:

    with st.container(border=True):

        st.markdown("### Original / Baseline")

        st.caption(
            "Contract drawings, original scopes, specifications, "
            "or previously approved documents."
        )

        original_files = st.file_uploader(
            "Upload baseline PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="original"
        )

        if original_files:

            st.success(
                f"{len(original_files)} baseline "
                f"document(s) ready"
            )

with upload_right:

    with st.container(border=True):

        st.markdown("### New / Revised")

        st.caption(
            "Revised drawings, bulletins, RFIs, directives, "
            "or newly issued project documents."
        )

        revised_files = st.file_uploader(
            "Upload revised PDFs",
            type=["pdf"],
            accept_multiple_files=True,
            key="revised"
        )

        if revised_files:

            st.success(
                f"{len(revised_files)} revised "
                f"document(s) ready"
            )


st.write("")


# ==========================================================
# STEP 3
# ==========================================================

st.markdown(
    """
    <div class="section-label">Step 3</div>
    <div class="section-title">Run the analysis</div>
    <div class="section-description">
        Choose how much visual drawing review you want and start the
        comparison.
    </div>
    """,
    unsafe_allow_html=True
)

with st.container(border=True):

    settings_left, settings_right = st.columns([1.3, 1])

    with settings_left:

        visual_analysis = st.checkbox(
            "Visually analyze plan sheets",
            value=True,
            help=(
                "Allows the AI to inspect rendered drawing pages "
                "in addition to extracted PDF text."
            )
        )

        st.caption(
            "Recommended for architectural, structural, MEP, "
            "and other graphical plan sets."
        )

    with settings_right:

        max_pages = st.number_input(
            "Pages visually reviewed per PDF",
            min_value=1,
            max_value=20,
            value=6
        )

        st.caption(
            "Use 3–6 pages while testing to control processing cost."
        )

    st.write("")

    analyze_clicked = st.button(
        "Analyze Project →",
        type="primary",
        use_container_width=True
    )


# ==========================================================
# ANALYSIS
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
            "Reviewing documents, comparing revisions, "
            "and building the project risk analysis..."
        ):

            try:

                original_text = ""
                revised_text = ""

                original_images = []
                revised_images = []


                # ORIGINAL DOCUMENTS
                for file in original_files:

                    original_text += (
                        extract_pdf_text(file)
                    )

                    if visual_analysis:

                        original_images.extend(
                            pdf_pages_to_images(
                                file,
                                int(max_pages)
                            )
                        )


                # REVISED DOCUMENTS
                for file in revised_files:

                    revised_text += (
                        extract_pdf_text(file)
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

Use supplied project documents as the primary evidence.

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
                st.session_state["project_name"] = project_name
                st.session_state["project_location"] = project_location
                st.session_state["company_name"] = company_name
                st.session_state["project_reference"] = project_reference

                st.success(
                    "Analysis complete. Review the results below."
                )

            except Exception as error:

                st.error(
                    "The project analysis could not be completed."
                )

                st.code(
                    str(error)
                )


# ==========================================================
# RESULTS
# ==========================================================

if "analysis" in st.session_state:

    analysis = st.session_state["analysis"]

    st.write("")
    st.write("")

    st.markdown(
        """
        <div class="section-label">Analysis Complete</div>
        <div class="section-title">Project Intelligence Dashboard</div>
        <div class="section-description">
            Review the highest-priority findings before opening the
            detailed project analysis.
        </div>
        """,
        unsafe_allow_html=True
    )


    # ======================================================
    # DASHBOARD METRICS
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

    changes_found = count_change_register_items(
        analysis
    )

    red_flags = count_risk_flags(
        analysis,
        "RED"
    )


    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:

        st.metric(
            "Scope Change",
            scope_change
        )

    with metric2:

        st.metric(
            "Overall Severity",
            severity
        )

    with metric3:

        st.metric(
            "Changes Found",
            changes_found
        )

    with metric4:

        st.metric(
            "Red Flags",
            red_flags
        )


    st.write("")


    # ======================================================
    # STATUS STRIP
    # ======================================================

    with st.container(border=True):

        status_left, status_middle, status_right = st.columns(3)

        with status_left:

            st.markdown(
                "**Analysis Confidence**"
            )

            st.write(
                confidence
            )

        with status_middle:

            st.markdown(
                "**Review Before Proceeding**"
            )

            st.write(
                review_status
            )

        with status_right:

            st.markdown(
                "**Project**"
            )

            st.write(
                st.session_state.get(
                    "project_name",
                    "Not provided"
                )
            )


    st.write("")


    # ======================================================
    # RESULT TABS
    # ======================================================

    summary_tab, changes_tab, full_tab = st.tabs(
        [
            "Executive Summary",
            "Change Register",
            "Full Analysis"
        ]
    )


    with summary_tab:

        st.markdown(
            section_text(
                analysis,
                "EXECUTIVE SUMMARY"
            )
        )

        st.markdown("---")

        st.markdown(
            section_text(
                analysis,
                "PROJECT RISK SUMMARY"
            )
        )


    with changes_tab:

        st.markdown(
            section_text(
                analysis,
                "CHANGE REGISTER"
            )
        )

        st.markdown("---")

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
    # CREATE REPORTS
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
        .replace(" ", "_")
    )

    if not safe_name:
        safe_name = "Project"


    # ======================================================
    # DOWNLOAD SECTION
    # ======================================================

    st.write("")
    st.write("")

    st.markdown(
        """
        <div class="section-label">Export</div>
        <div class="section-title">Download project reports</div>
        <div class="section-description">
            Use the Quick Report for management review and the Full
            Report for detailed supporting analysis.
        </div>
        """,
        unsafe_allow_html=True
    )


    download_left, download_right = st.columns(2)


    with download_left:

        with st.container(border=True):

            st.markdown(
                "### Quick Report"
            )

            st.caption(
                "Executive summary, major risks, change register, "
                "risk flags, and recommended actions."
            )

            st.download_button(
                "Download Quick Report",
                data=quick_pdf,
                file_name=(
                    f"{safe_name}_Quick_Report.pdf"
                ),
                mime="application/pdf",
                use_container_width=True
            )


    with download_right:

        with st.container(border=True):

            st.markdown(
                "### Full Analysis"
            )

            st.caption(
                "Detailed scope comparison, technical analysis, "
                "cost, schedule, coordination, documentation, "
                "and supporting references."
            )

            st.download_button(
                "Download Full Report",
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
    <div class="site-footer">
        Construction Scope AI • Preliminary construction-management
        analysis • Findings should be verified against current project
        documents and qualified project personnel.
    </div>
    """,
    unsafe_allow_html=True
)
