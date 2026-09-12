import os
import re
import base64
from io import BytesIO
from datetime import datetime

import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from openai import OpenAI
import fitz  # PyMuPDF

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
# APP CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="Construction Scope AI",
    page_icon="🏗️",
    layout="wide"
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
# CONSTANTS
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

    reader = PdfReader(
        BytesIO(pdf_bytes)
    )

    text = ""

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        page_text = page.extract_text() or ""

        text += (
            f"\n\n--- DOCUMENT: {uploaded_file.name} "
            f"| PAGE {page_number} ---\n"
        )

        text += page_text

    return text


# ==========================================================
# PDF TO IMAGE CONVERSION
# ==========================================================

def pdf_pages_to_images(
    uploaded_file,
    max_pages
):

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

        page = document.load_page(
            page_index
        )

        matrix = fitz.Matrix(
            1.7,
            1.7
        )

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image_bytes = pix.tobytes(
            "png"
        )

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
# TEXT CLEANING
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
            for cell
            in line.strip().strip("|").split("|")
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
            topMargin=0.8 * inch,
            bottomMargin=0.7 * inch,
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

        # HEADER LINE
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

        # HEADER LEFT
        canvas.setFont(
            "Helvetica-Bold",
            8
        )

        canvas.setFillColor(
            colors.HexColor("#344054")
        )

        canvas.drawString(
            self.leftMargin,
            letter[1] - 0.42 * inch,
            self.project_name[:55]
        )

        # HEADER RIGHT
        canvas.setFont(
            "Helvetica",
            8
        )

        canvas.drawRightString(
            letter[0] - self.rightMargin,
            letter[1] - 0.42 * inch,
            "Construction Scope AI Analysis"
        )

        # FOOTER LINE
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
                self.company_name[:50]
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

        heading_text = (
            flowable.getPlainText()
        )

        key = (
            "section_"
            + str(
                abs(
                    hash(
                        heading_text
                        + str(self.page)
                    )
                )
            )
        )

        self.canv.bookmarkPage(
            key
        )

        self.canv.addOutlineEntry(
            heading_text,
            key,
            level=0,
            closed=False
        )

        self.notify(
            "TOCEntry",
            (
                0,
                heading_text,
                self.page,
                key
            )
        )


# ==========================================================
# REPORT TABLE
# ==========================================================

def create_report_table(
    rows,
    width,
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

        formatted_row = []

        for cell in row:

            formatted_row.append(
                Paragraph(
                    format_inline_markdown(
                        cell
                    ),
                    cell_style
                )
            )

        formatted_rows.append(
            formatted_row
        )

    column_width = (
        width
        / max_columns
    )

    table = Table(
        formatted_rows,
        colWidths=[
            column_width
        ] * max_columns,
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
                    0.4,
                    colors.HexColor("#D0D5DD")
                ),

                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6
                ),

                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6
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
# CREATE PDF REPORT
# ==========================================================

def create_pdf_report(
    project_name,
    project_location,
    company_name,
    analysis_text
):

    buffer = BytesIO()

    document = ConstructionReportTemplate(
        buffer,
        project_name=project_name,
        company_name=company_name
    )

    styles = getSampleStyleSheet()


    # ======================================================
    # STYLES
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

    section_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=19,
        textColor=colors.HexColor("#101828"),
        spaceBefore=18,
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
        spaceBefore=11,
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
        spaceBefore=13,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "BodyTextCustom",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.4,
        leading=13.2,
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
        fontSize=7.8,
        leading=10.2,
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
            "Construction Scope AI Analysis",
            cover_title
        )
    )

    story.append(
        Paragraph(
            project_name
            if project_name
            else "Construction Project",
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
    # TABLE OF CONTENTS
    # ======================================================

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

    story.append(
        toc
    )

    story.append(
        PageBreak()
    )


    # ======================================================
    # REPORT BODY
    # ======================================================

    lines = analysis_text.splitlines()

    index = 0

    while index < len(lines):

        clean = lines[index].strip()

        # BLANK
        if not clean:

            story.append(
                Spacer(
                    1,
                    3
                )
            )

            index += 1
            continue

        # DIVIDERS
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


        # ==================================================
        # TABLE
        # ==================================================

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

            report_table = create_report_table(
                rows,
                document.width,
                table_cell_style
            )

            if report_table:

                story.append(
                    Spacer(
                        1,
                        5
                    )
                )

                story.append(
                    report_table
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

        heading_upper = (
            heading_text.upper()
        )


        # ==================================================
        # MAIN SECTION
        # ==================================================

        if heading_upper in MAIN_SECTIONS:

            story.append(
                Paragraph(
                    heading_upper,
                    section_style
                )
            )

            index += 1
            continue


        # ==================================================
        # SUBSECTION
        # ==================================================

        if heading_upper in SUBSECTIONS:

            story.append(
                Paragraph(
                    heading_text.title(),
                    subsection_style
                )
            )

            index += 1
            continue


        # ==================================================
        # CHANGE CARD HEADING
        # ==================================================

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


        # ==================================================
        # MARKDOWN SUBHEADINGS
        # ==================================================

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


        # ==================================================
        # BULLET
        # ==================================================

        if (
            clean.startswith("• ")
            or clean.startswith("- ")
        ):

            bullet_text = (
                clean[2:].strip()
            )

            story.append(
                Paragraph(
                    "• "
                    + format_inline_markdown(
                        bullet_text
                    ),
                    bullet_style
                )
            )

            index += 1
            continue


        # ==================================================
        # NUMBERED ITEM
        # ==================================================

        number_match = re.match(
            r"^(\d+)\.\s+(.*)",
            clean
        )

        if number_match:

            number = (
                number_match
                .group(1)
            )

            item_text = (
                number_match
                .group(2)
            )

            story.append(
                Paragraph(
                    f"<b>{number}.</b> "
                    + format_inline_markdown(
                        item_text
                    ),
                    numbered_style
                )
            )

            index += 1
            continue


        # ==================================================
        # KEY: VALUE
        # ==================================================

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


        # ==================================================
        # NORMAL TEXT
        # ==================================================

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
    # REPORT DISCLAIMER
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
# AI INSTRUCTIONS
# ==========================================================

ANALYSIS_INSTRUCTIONS = """
You are an advanced construction change-management and
document-analysis assistant.

Your job is to compare original construction documents against
new or revised construction documents and explain meaningful
construction consequences.

The goal is NOT simply to identify graphical differences.

The goal is to help a project manager, estimator, superintendent,
general contractor, or subcontractor understand:

- what changed
- where it changed
- which trades are affected
- whether it may affect scope
- potential cost exposure
- potential schedule exposure
- coordination requirements
- documentation risk
- code or jurisdiction concerns
- what should happen next


==================================================
CORE RULES
==================================================

Do not provide legal advice.

Do not make a final contractual entitlement determination.

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
- company procedures
- field conditions

Clearly distinguish:

CONFIRMED FACT
ASSUMPTION
MISSING INFORMATION
ITEM REQUIRING VERIFICATION

Use document names, drawing sheets, and page numbers whenever
they are reasonably identifiable.

Written dimensions take priority over measurements estimated
from an image.

If visual information is unclear, say so.

Do not manufacture risk simply to fill a report.

Do not repeat the same information unnecessarily.

Keep the report concise enough to be useful while still
capturing important construction consequences.


==================================================
REPORT ORDER
==================================================

Use the sections below in EXACTLY this order.

Do not rename sections.

Do not add new main sections.


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

Provide no more than two concise paragraphs.

Focus only on the most important findings.


==================================================
PROJECT RISK SUMMARY
==================================================

OVERALL PROJECT RISK:
HIGH / MEDIUM / LOW

TOP CHANGES

List no more than five.

AFFECTED TRADES

List construction trades affected by the changes.

TOP COST RISKS

List no more than five.

TOP SCHEDULE RISKS

List no more than five.

TOP REGULATORY RISKS

List no more than five.

TOP DOCUMENTATION RISKS

List no more than five.

MOST IMPORTANT NEXT ACTION

Provide one clear action.


==================================================
CHANGE REGISTER
==================================================

Create one markdown table:

| ID | Change | Primary Trade | Cost Risk | Schedule Risk | Confidence | Source |

Use:

CR-01
CR-02
CR-03

and so on.

Cost Risk:
HIGH / MEDIUM / LOW / UNKNOWN

Schedule Risk:
HIGH / MEDIUM / LOW / UNKNOWN

Confidence:
HIGH / MEDIUM / LOW

Keep each table cell concise.


==================================================
VISUAL DRAWING COMPARISON
==================================================

Only include changes supported by supplied drawing images
or clearly supported drawing text.

For each meaningful change use exactly:

CHANGE 1 — Short Title

CHANGE:
Briefly describe the change.

PRIMARY TRADE:
Trade or trades.

ORIGINAL SOURCE:
Drawing / sheet / page.

REVISED SOURCE:
Drawing / sheet / page.

ORIGINAL CONDITION:
Describe original condition.

REVISED CONDITION:
Describe revised condition.

COST RISK:
HIGH / MEDIUM / LOW / UNKNOWN

SCHEDULE RISK:
HIGH / MEDIUM / LOW / UNKNOWN

POTENTIAL IMPACT:
Explain practical construction consequences.

RECOMMENDED ACTION:
Give the next practical action.

CONFIDENCE:
HIGH / MEDIUM / LOW

Do not report rendering-only or cosmetic differences as
construction scope unless they are supported by governing
drawings or notes.


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

If unavailable, write:

NOT PROVIDED

If user-entered project information conflicts with the
documents, explicitly identify the conflict.


==================================================
ORIGINAL REQUIREMENT
==================================================

Describe the baseline requirement.

If no executed contract or subcontract was supplied,
state that the analysis is based on original drawing or
document requirements rather than confirmed contractual scope.

Use bullets where useful.

Cite the relevant document and sheet/page.


==================================================
REVISED REQUIREMENT
==================================================

Describe the revised requirement.

Identify meaningful:

- additions
- deletions
- relocations
- material changes
- quantity changes
- dimensional changes
- equipment changes
- sequencing changes

Use source references.


==================================================
DETAILED SCOPE COMPARISON
==================================================

Create a markdown table:

| Scope Area | Original | Revised | Potential Impact | Source |

Keep table entries concise.

Do not duplicate long explanations already given elsewhere.


==================================================
QUANTITY AND TECHNICAL ANALYSIS
==================================================

When confirmed quantities are available use:

| Item | Original | Revised | Net Change |

Show calculations below the table only when useful.

Clearly identify quantities that cannot be determined.

Never invent dimensions or takeoff quantities.


==================================================
DIRECT COST IMPACT
==================================================

LABOR

List reasonable labor exposure.

MATERIAL

List additions, deletions, substitutions, waste,
or procurement exposure.

EQUIPMENT

List relevant equipment impact.

SUBCONTRACTORS AND VENDORS

List vendor, procurement, cancellation, restocking,
or subcontractor exposure.

Do not invent prices.


==================================================
INDIRECT COST IMPACT
==================================================

Only include relevant items such as:

- project management
- supervision
- engineering
- permit revision
- testing
- inspection
- remobilization
- disruption
- lost productivity
- cleanup
- storage
- restocking
- documentation
- extended general conditions

Do not claim they definitely occur.


==================================================
SCHEDULE IMPACT
==================================================

POTENTIAL SCHEDULE IMPACT:
HIGH / MEDIUM / LOW / UNKNOWN

Evaluate relevant:

- sequencing
- procurement
- long lead material
- engineering
- submittals
- approvals
- inspections
- rework
- access
- predecessors
- successors
- potential critical-path exposure

Do not invent delay days.

If schedule information was not supplied, say so.


==================================================
COORDINATION AND CODE REVIEW
==================================================

JURISDICTION

Explain confirmed location and jurisdiction conflicts.

STRUCTURAL

Discuss relevant structural coordination.

MECHANICAL

Discuss HVAC or mechanical issues.

PLUMBING

Discuss plumbing issues.

ELECTRICAL AND LIFE SAFETY

Discuss electrical and life-safety issues.

ENVELOPE AND ENERGY

Discuss roofing, waterproofing, insulation,
air sealing, moisture, and energy issues.

ACCESSIBILITY

Discuss only if relevant.

REGULATORY REVIEW

Consider relevant code families and permitting issues.

Do not invent code sections.

Do not state that a code requirement applies unless the
jurisdiction and project conditions support it.

If jurisdiction is uncertain, require AHJ verification.


==================================================
SAFETY IMPACT
==================================================

Only include safety concerns directly related to
identified changes.

Examples when relevant:

- fall exposure
- structural stability
- temporary shoring
- lifting
- demolition
- electrical exposure
- silica
- excavation
- temporary guards
- access
- material handling

Do not fill the section with generic safety advice.


==================================================
CONTRACT AND DOCUMENTATION RISK
==================================================

Evaluate relevant:

- controlling drawing set
- revision dates
- transmittals
- clouds
- delta symbols
- revision narratives
- RFIs
- written directives
- authorization
- notice requirements
- photographs
- daily reports
- labor records
- equipment records
- purchase orders
- delivery tickets
- vendor correspondence

Do not provide legal advice.


==================================================
DOCUMENT CONFLICTS
==================================================

List only meaningful conflicts.

Examples:

- drawing versus drawing
- drawing versus specification
- original versus revision
- user information versus project document
- inconsistent sheet dates
- conflicting dimensions
- unresolved equipment locations

If none are found:

NONE IDENTIFIED


==================================================
MISSING INFORMATION
==================================================

List only information that would materially improve
the analysis or is needed before acting.


==================================================
ASSUMPTIONS
==================================================

List material assumptions only.

If none:

NONE


==================================================
SUPPORTING REFERENCES
==================================================

Create a markdown table:

| Document | Page / Sheet | Requirement or Change | Why It Matters |

Avoid duplicate references.


==================================================
RECOMMENDED ACTIONS
==================================================

Provide a prioritized numbered list.

The first action should be the most important.

Focus on practical construction-management actions.


==================================================
RISK FLAGS
==================================================

RED

Only serious concerns requiring immediate review.

YELLOW

Issues requiring clarification, monitoring,
or additional information.

GREEN

Important items reviewed where no material
change was identified.

Do not create green flags simply to fill the section.


==================================================
FINAL ASSESSMENT
==================================================

Use no more than three paragraphs.

Summarize:

- scope-change conclusion
- primary cost exposure
- primary schedule exposure
- primary coordination concern
- primary regulatory concern
- primary documentation concern
- recommended next step

Do not repeat the entire report.

End the report here.
"""


# ==========================================================
# WEBSITE
# ==========================================================

st.title(
    "🏗️ Construction Scope AI"
)

st.write(
    "Compare original and revised construction documents "
    "to identify meaningful changes, affected trades, "
    "cost risk, schedule risk, coordination issues, "
    "and documentation concerns."
)

st.info(
    "This platform provides preliminary construction-management "
    "analysis. Important findings should be verified against "
    "current project documents and qualified project personnel."
)


# ==========================================================
# PROJECT INFORMATION
# ==========================================================

st.header(
    "1. Project Information"
)

left, right = st.columns(2)

with left:

    project_name = st.text_input(
        "Project Name"
    )

    company_name = st.text_input(
        "Contractor / Company"
    )

with right:

    project_location = st.text_input(
        "Project Location",
        placeholder="Example: Johnson City, Tennessee"
    )


# ==========================================================
# DOCUMENTS
# ==========================================================

st.header(
    "2. Project Documents"
)

original_col, revised_col = st.columns(2)

with original_col:

    st.subheader(
        "Original / Baseline"
    )

    original_files = st.file_uploader(
        "Upload original drawings, contracts, scopes, specifications, etc.",
        type=["pdf"],
        accept_multiple_files=True,
        key="original"
    )

with revised_col:

    st.subheader(
        "New / Revised"
    )

    revised_files = st.file_uploader(
        "Upload revised drawings, RFIs, bulletins, directives, etc.",
        type=["pdf"],
        accept_multiple_files=True,
        key="revised"
    )


# ==========================================================
# ANALYSIS SETTINGS
# ==========================================================

st.header(
    "3. Analysis Settings"
)

visual_analysis = st.checkbox(
    "Visually analyze plan sheets",
    value=True
)

max_pages = st.number_input(
    "Maximum drawing pages visually analyzed per PDF",
    min_value=1,
    max_value=20,
    value=6
)

st.caption(
    "For testing, 3–6 pages per PDF is recommended. "
    "Larger drawing sets will eventually use changed-sheet detection "
    "instead of analyzing every page."
)


# ==========================================================
# ANALYZE
# ==========================================================

st.divider()

if st.button(
    "Analyze Project",
    type="primary",
    use_container_width=True
):

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
            "Reviewing project documents and drawing revisions..."
        ):

            try:

                original_text = ""
                revised_text = ""

                original_images = []
                revised_images = []


                # ORIGINALS
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


                # REVISIONS
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


                # ==================================================
                # ANALYSIS INPUT
                # ==================================================

                prompt_text = f"""
PROJECT INFORMATION PROVIDED BY USER

Project Name:
{project_name}

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

If user-entered information conflicts with the documents,
report the conflict rather than choosing one silently.

Prioritize meaningful construction changes over cosmetic
or drafting differences.
"""


                content = [
                    {
                        "type": "input_text",
                        "text": prompt_text
                    }
                ]


                # ORIGINAL DRAWING IMAGES
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


                # REVISED DRAWING IMAGES
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


                st.session_state[
                    "analysis"
                ] = analysis

                st.session_state[
                    "project_name"
                ] = project_name

                st.session_state[
                    "project_location"
                ] = project_location

                st.session_state[
                    "company_name"
                ] = company_name


                st.success(
                    "Project analysis complete."
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

    st.divider()

    st.header(
        "4. Project Analysis"
    )

    analysis = st.session_state[
        "analysis"
    ]

    st.markdown(
        analysis
    )


    # PDF
    pdf_report = create_pdf_report(

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

        analysis
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


    st.download_button(
        "📄 Download Professional PDF Report",
        data=pdf_report,
        file_name=(
            f"{safe_name}_Scope_Analysis.pdf"
        ),
        mime="application/pdf",
        use_container_width=True
    )
