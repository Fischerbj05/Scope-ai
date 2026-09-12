import os
import base64
from io import BytesIO

import streamlit as st
from pypdf import PdfReader
from dotenv import load_dotenv
from openai import OpenAI
import fitz  # PyMuPDF

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph,
    Spacer,
    PageBreak,
)
from reportlab.platypus.tableofcontents import TableOfContents


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
        "OpenAI API key not found. Add OPENAI_API_KEY to Streamlit Secrets."
    )
    st.stop()

client = OpenAI(api_key=api_key)


# ==========================================================
# EXTRACT TEXT FROM PDF
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
# CONVERT PDF PAGES TO IMAGES
# ==========================================================

def pdf_pages_to_images(uploaded_file, max_pages):
    pdf_bytes = uploaded_file.getvalue()

    document = fitz.open(
        stream=pdf_bytes,
        filetype="pdf"
    )

    images = []

    number_of_pages = min(
        len(document),
        max_pages
    )

    for page_index in range(number_of_pages):
        page = document.load_page(page_index)

        matrix = fitz.Matrix(1.7, 1.7)

        pix = page.get_pixmap(
            matrix=matrix,
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
                "image_url": f"data:image/png;base64,{encoded}"
            }
        )

    document.close()

    return images


# ==========================================================
# PDF REPORT TEMPLATE
# ==========================================================

class ConstructionReportTemplate(BaseDocTemplate):

    def __init__(self, filename, project_name="", **kwargs):
        self.project_name = project_name

        BaseDocTemplate.__init__(
            self,
            filename,
            pagesize=letter,
            rightMargin=0.65 * inch,
            leftMargin=0.65 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.65 * inch,
            **kwargs
        )

        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal"
        )

        template = PageTemplate(
            id="main",
            frames=[frame],
            onPage=self.add_header_footer
        )

        self.addPageTemplates([template])

    def add_header_footer(self, canvas, doc):
        canvas.saveState()

        canvas.setFont("Helvetica", 8)

        if self.project_name:
            canvas.drawString(
                self.leftMargin,
                letter[1] - 0.45 * inch,
                self.project_name
            )

        canvas.drawRightString(
            letter[0] - self.rightMargin,
            letter[1] - 0.45 * inch,
            "Construction Scope AI Analysis"
        )

        canvas.drawCentredString(
            letter[0] / 2,
            0.35 * inch,
            f"Page {doc.page}"
        )

        canvas.restoreState()

    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph):

            if flowable.style.name == "SectionHeading":
                text = flowable.getPlainText()

                key = f"heading_{abs(hash(text + str(self.page)))}"

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
# CREATE DOWNLOADABLE PDF
# ==========================================================

def create_pdf_report(project_name, analysis_text):
    buffer = BytesIO()

    document = ConstructionReportTemplate(
        buffer,
        project_name=project_name
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=22,
        leading=26,
        spaceAfter=15
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=11,
        leading=14,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading1"],
        fontSize=14,
        leading=17,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        spaceAfter=5
    )

    story = []

    # COVER PAGE
    story.append(Spacer(1, 1.3 * inch))

    story.append(
        Paragraph(
            "Construction Scope AI Analysis",
            title_style
        )
    )

    if project_name:
        story.append(
            Paragraph(
                f"Project: {project_name}",
                subtitle_style
            )
        )

    story.append(Spacer(1, 0.5 * inch))

    story.append(
        Paragraph(
            "Scope • Drawing Revision • Cost • Schedule • "
            "Coordination • Code • Safety • Documentation",
            subtitle_style
        )
    )

    story.append(Spacer(1, 1.5 * inch))

    story.append(
        Paragraph(
            "Preliminary Construction-Management Review",
            subtitle_style
        )
    )

    story.append(PageBreak())

    # TABLE OF CONTENTS
    story.append(
        Paragraph(
            "Table of Contents",
            title_style
        )
    )

    story.append(Spacer(1, 12))

    toc = TableOfContents()

    toc.levelStyles = [
        ParagraphStyle(
            name="TOCHeading",
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            leftIndent=10,
            firstLineIndent=-10,
            spaceBefore=4
        )
    ]

    story.append(toc)
    story.append(PageBreak())

    # REPORT SECTIONS
    section_names = [
        "EXECUTIVE SUMMARY",
        "PROJECT RISK SUMMARY",
        "VISUAL DRAWING COMPARISON",
        "PROJECT AND JURISDICTION INFORMATION",
        "ORIGINAL CONTRACTED REQUIREMENT",
        "NEW OR REVISED REQUIREMENT",
        "DETAILED SCOPE COMPARISON",
        "QUANTITY AND TECHNICAL ANALYSIS",
        "POTENTIAL DIRECT COST IMPACTS",
        "POTENTIAL INDIRECT COST IMPACTS",
        "SCHEDULE IMPACT",
        "COORDINATION, CODE, AND REGIONAL REQUIREMENTS",
        "SAFETY IMPACT",
        "CONTRACT AND DOCUMENTATION RISK",
        "DOCUMENT CONFLICTS OR INCONSISTENCIES",
        "MISSING INFORMATION",
        "ASSUMPTIONS",
        "SUPPORTING REFERENCES",
        "RECOMMENDED ACTION",
        "RISK FLAGS",
        "FINAL ASSESSMENT"
    ]

    for line in analysis_text.splitlines():

        clean = line.strip()

        if not clean:
            story.append(Spacer(1, 4))
            continue

        if clean.startswith("===="):
            continue

        # REMOVE MARKDOWN HEADING SYMBOLS
        display_text = clean

        if display_text.startswith("### "):
            display_text = display_text[4:].strip()
        elif display_text.startswith("## "):
            display_text = display_text[3:].strip()
        elif display_text.startswith("# "):
            display_text = display_text[2:].strip()

        # ESCAPE REPORTLAB CHARACTERS
        safe_text = (
            display_text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        # MAIN REPORT SECTIONS
        if display_text.upper() in section_names:
            story.append(
                Paragraph(
                    safe_text,
                    heading_style
                )
            )

        else:
            if safe_text.startswith("- "):
                safe_text = "• " + safe_text[2:]

            story.append(
                Paragraph(
                    safe_text,
                    body_style
                )
            )

    story.append(Spacer(1, 25))

    story.append(
        Paragraph(
            "This analysis is a preliminary construction-management "
            "review and is not a substitute for review by the project "
            "manager, estimator, superintendent, design professional, "
            "Authority Having Jurisdiction, or legal counsel where appropriate.",
            body_style
        )
    )

    document.multiBuild(story)

    buffer.seek(0)

    return buffer.getvalue()


# ==========================================================
# AI INSTRUCTIONS
# ==========================================================

instructions = """
You are an advanced AI construction scope, drawing-revision,
change-management, project-risk, code-awareness, and contract-document
analysis assistant.

Use both document text and visual drawing information when supplied.

Do not invent facts, quantities, dimensions, prices, dates,
code sections, contract language, owner requirements, or company policies.

Clearly distinguish:
- confirmed facts
- assumptions
- missing information
- items requiring verification

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

==================================================
PROJECT RISK SUMMARY
==================================================

OVERALL PROJECT RISK:
HIGH / MEDIUM / LOW

TOP CHANGES:
List the five most important confirmed or likely changes.

TRADES AFFECTED:
List all trades reasonably affected.

TOP COST RISKS:
List the most important potential cost exposures.

TOP SCHEDULE RISKS:
List the most important potential schedule exposures.

TOP CODE / REGULATORY RISKS:
List the most important code, permit, inspection,
or jurisdiction concerns.

TOP DOCUMENTATION RISKS:
List the most important drawing, contract,
revision-control, RFI, or authorization concerns.

RED FLAGS:
State the number of meaningful RED risks and summarize them.

YELLOW FLAGS:
State the number of meaningful YELLOW risks and summarize them.

MOST IMPORTANT NEXT ACTION:
Give one clear action the contractor or project manager should take first.

==================================================
VISUAL DRAWING COMPARISON
==================================================

If drawing images are supplied, compare original and revised sheets.

For each meaningful change provide:

CHANGE:
ORIGINAL DRAWING:
ORIGINAL PAGE:
REVISED DRAWING:
REVISED PAGE:
ORIGINAL CONDITION:
REVISED CONDITION:
POTENTIAL IMPACT:
CONFIDENCE:

==================================================
PROJECT AND JURISDICTION INFORMATION
==================================================

Identify project name, location, owner, GC, subcontractor,
design professional, AHJ, project type, and code information when available.

Flag conflicts.

==================================================
ORIGINAL CONTRACTED REQUIREMENT
==================================================

Describe original requirements and cite source documents/pages.

==================================================
NEW OR REVISED REQUIREMENT
==================================================

Describe revised requirements and cite source documents/pages.

==================================================
DETAILED SCOPE COMPARISON
==================================================

Compare original vs revised work.

==================================================
QUANTITY AND TECHNICAL ANALYSIS
==================================================

Perform calculations only when enough information is available.

==================================================
POTENTIAL DIRECT COST IMPACTS
==================================================

Analyze labor, material, equipment, subcontractor, and vendor impacts.

==================================================
POTENTIAL INDIRECT COST IMPACTS
==================================================

Analyze supervision, management, engineering, permits,
testing, inspections, coordination, disruption, rework, and productivity.

==================================================
SCHEDULE IMPACT
==================================================

Analyze sequencing, procurement, lead time, inspections,
approvals, critical path, and rework concerns.

==================================================
COORDINATION, CODE, AND REGIONAL REQUIREMENTS
==================================================

Consider structural, MEP, envelope, site, fire/life safety,
accessibility, permitting, inspections, applicable code families,
regional requirements, owner requirements, and company requirements.

Do not invent code sections.

==================================================
SAFETY IMPACT
==================================================

Identify relevant construction safety concerns.

==================================================
CONTRACT AND DOCUMENTATION RISK
==================================================

Consider directives, RFIs, notices, authorization,
daily reports, photos, labor records, equipment records,
delivery tickets, emails, meeting minutes, and revision control.

==================================================
DOCUMENT CONFLICTS OR INCONSISTENCIES
==================================================

Identify conflicts between supplied documents and user-entered information.

==================================================
MISSING INFORMATION
==================================================

List information needed to improve the analysis.

==================================================
ASSUMPTIONS
==================================================

List assumptions.

==================================================
SUPPORTING REFERENCES
==================================================

DOCUMENT:
PAGE:
REQUIREMENT / CHANGE:
WHY IT MATTERS:

==================================================
RECOMMENDED ACTION
==================================================

Give practical step-by-step recommendations.

==================================================
RISK FLAGS
==================================================

RED:
Serious concern.

YELLOW:
Requires review.

GREEN:
No major issue identified.

==================================================
FINAL ASSESSMENT
==================================================

Provide a professional construction-management conclusion.

Do not provide legal advice.
"""


# ==========================================================
# STREAMLIT PAGE
# ==========================================================

st.set_page_config(
    page_title="Construction Scope AI",
    page_icon="🏗️",
    layout="wide"
)

st.title("🏗️ Construction Scope AI")

st.write(
    "Upload original and revised construction documents. "
    "The system analyzes scope, drawings, cost, schedule, "
    "coordination, code, safety, and documentation impacts."
)

st.warning(
    "This tool provides preliminary construction-management analysis. "
    "Important findings should be verified by qualified project personnel."
)


# PROJECT INFO

st.header("Project Information")

project_name = st.text_input("Project Name")

project_location = st.text_input(
    "Project Location",
    placeholder="Example: Johnson City, Tennessee"
)

company_name = st.text_input(
    "Contractor / Company"
)


# DRAWING SETTINGS

st.header("Drawing Analysis Settings")

visual_analysis = st.checkbox(
    "Visually analyze plan sheets",
    value=True
)

max_pages = st.number_input(
    "Maximum drawing pages to visually analyze per PDF",
    min_value=1,
    max_value=20,
    value=6
)

st.caption(
    "Higher page counts provide more drawing coverage "
    "but increase API usage and cost."
)


# ORIGINAL DOCUMENTS

st.header("Original Project Documents")

original_files = st.file_uploader(
    "Upload original contract, drawings, specifications, scope, etc.",
    type=["pdf"],
    accept_multiple_files=True,
    key="original"
)


# REVISED DOCUMENTS

st.header("New / Revised Project Documents")

new_files = st.file_uploader(
    "Upload revised drawings, RFIs, bulletins, directives, etc.",
    type=["pdf"],
    accept_multiple_files=True,
    key="revised"
)


# RUN ANALYSIS

if st.button(
    "Analyze Project",
    type="primary",
    use_container_width=True
):

    if not original_files:
        st.error(
            "Please upload at least one original document."
        )

    elif not new_files:
        st.error(
            "Please upload at least one revised document."
        )

    else:

        with st.spinner(
            "Reading documents and analyzing the project..."
        ):

            try:
                original_text = ""
                revised_text = ""

                original_images = []
                revised_images = []

                for file in original_files:
                    original_text += extract_pdf_text(file)

                    if visual_analysis:
                        original_images.extend(
                            pdf_pages_to_images(
                                file,
                                int(max_pages)
                            )
                        )

                for file in new_files:
                    revised_text += extract_pdf_text(file)

                    if visual_analysis:
                        revised_images.extend(
                            pdf_pages_to_images(
                                file,
                                int(max_pages)
                            )
                        )

                prompt_text = f"""
PROJECT NAME:
{project_name}

PROJECT LOCATION PROVIDED BY USER:
{project_location}

CONTRACTOR / COMPANY:
{company_name}

ORIGINAL DOCUMENT TEXT:

{original_text}

REVISED DOCUMENT TEXT:

{revised_text}

Perform a detailed construction-management analysis.

Use supplied documents as the primary source of confirmed facts.

Clearly distinguish:
- confirmed facts
- assumptions
- missing information
- items requiring verification
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
                                f"ORIGINAL DRAWING IMAGE: "
                                f"{image['document']} "
                                f"PAGE {image['page']}"
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
                                f"REVISED DRAWING IMAGE: "
                                f"{image['document']} "
                                f"PAGE {image['page']}"
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
                    instructions=instructions,
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

                st.success(
                    "Analysis complete."
                )

            except Exception as error:
                st.error(
                    "The analysis could not be completed."
                )

                st.code(str(error))


# RESULTS

if "analysis" in st.session_state:

    st.header(
        "Construction Scope Analysis"
    )

    analysis = st.session_state["analysis"]

    st.markdown(
        analysis
    )

    pdf_report = create_pdf_report(
        st.session_state.get(
            "project_name",
            ""
        ),
        analysis
    )

    safe_project_name = (
        st.session_state
        .get("project_name", "Project")
        .strip()
        .replace(" ", "_")
    )

    if not safe_project_name:
        safe_project_name = "Project"

    st.download_button(
        "📄 Download PDF Report",
        data=pdf_report,
        file_name=f"{safe_project_name}_Scope_Analysis.pdf",
        mime="application/pdf",
        use_container_width=True
    )
