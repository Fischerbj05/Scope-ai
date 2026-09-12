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
        "OpenAI API key not found. Add OPENAI_API_KEY "
        "to Streamlit Secrets."
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

        # Higher resolution for construction notes/dimensions
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

    # ------------------------------------------------------
    # COVER PAGE
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # TABLE OF CONTENTS
    # ------------------------------------------------------

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

    # ------------------------------------------------------
    # REPORT SECTIONS
    # ------------------------------------------------------

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

        clean = (
            clean
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )

        if clean.upper() in section_names:
            story.append(
                Paragraph(
                    clean,
                    heading_style
                )
            )

        else:
            if clean.startswith("- "):
                clean = "• " + clean[2:]

            story.append(
                Paragraph(
                    clean,
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

    # multiBuild is required so the TOC can calculate page numbers
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

You will receive:
1. Text extracted from original construction documents.
2. Text extracted from revised construction documents.
3. Images of original plan sheets when visual analysis is enabled.
4. Images of revised plan sheets when visual analysis is enabled.

Use BOTH document text and visible drawing information.

Analyze potential:
- scope changes
- drawing revisions
- dimensions
- quantities
- materials
- labor impacts
- equipment impacts
- schedule impacts
- productivity impacts
- trade coordination
- code concerns
- regional requirements
- safety concerns
- contract/documentation risks
- procurement impacts
- rework
- owner requirements
- company requirements

VISUAL DRAWING REVIEW:

When images are supplied, inspect plan sheets for:
- dimensions
- thicknesses
- elevations
- quantities
- materials
- callouts
- keynotes
- detail references
- section references
- structural notes
- equipment
- doors
- walls
- slabs
- reinforcement
- MEP information
- penetrations
- utilities
- grading
- finishes
- revision clouds
- delta symbols
- revision notes
- schedules
- added work
- deleted work
- relocated work

IMPORTANT RULES:

- Do not provide legal advice.
- Do not make a final legal determination.
- Do not state that payment is definitely owed.
- Do not invent facts.
- Do not invent contract language.
- Do not invent quantities.
- Do not invent dimensions.
- Do not invent prices.
- Do not invent dates.
- Do not invent delay durations.
- Do not invent code sections.
- Do not invent local amendments.
- Do not invent owner requirements.
- Do not invent company policies.
- Clearly distinguish confirmed facts from assumptions.
- Clearly identify missing information.
- Clearly identify items requiring verification.
- Cite document names and page numbers whenever possible.
- If visual evidence is unclear, say so.
- Do not claim to see something that is not visible.
- Consider both direct and indirect impacts.
- Consider other trades and adjacent work.
- Be detailed but do not create unsupported problems.

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
Provide a concise summary of the major finding.

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

Do not exaggerate risk.
Only include supported risks or clearly identified assumptions.

==================================================
VISUAL DRAWING COMPARISON
==================================================

If drawing images were supplied, identify meaningful visible changes.

For each change use:

CHANGE:

ORIGINAL DRAWING:

ORIGINAL PAGE:

REVISED DRAWING:

REVISED PAGE:

ORIGINAL CONDITION:

REVISED CONDITION:

POTENTIAL IMPACT:

CONFIDENCE:

If no visual images were supplied, state that visual comparison
was not performed.

==================================================
PROJECT AND JURISDICTION INFORMATION
==================================================

Identify when available:

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

If information is missing, write NOT PROVIDED.

If user-entered information conflicts with the documents,
clearly flag the conflict.

==================================================
ORIGINAL CONTRACTED REQUIREMENT
==================================================

Describe the original requirements.

Include where available:
- dimensions
- quantities
- materials
- location
- responsibilities
- exclusions
- limitations
- drawing requirements
- specification requirements

Cite source documents and pages.

==================================================
NEW OR REVISED REQUIREMENT
==================================================

Describe exactly what changed.

Include:
- added work
- deleted work
- quantity changes
- dimensional changes
- material changes
- location changes
- sequencing changes
- schedule changes
- responsibilities
- testing changes
- inspection changes

Cite source documents and pages.

==================================================
DETAILED SCOPE COMPARISON
==================================================

For each meaningful difference use:

ITEM:

ORIGINAL:

NEW:

DIFFERENCE:

POTENTIAL CONSEQUENCE:

SOURCE:

Clearly distinguish confirmed changes from assumptions.

==================================================
QUANTITY AND TECHNICAL ANALYSIS
==================================================

Perform calculations when enough information is available.

Consider:
- length
- width
- depth
- thickness
- area
- volume
- count
- weight

Show calculations.

Do not invent missing dimensions.

Clearly state assumptions.

==================================================
POTENTIAL DIRECT COST IMPACTS
==================================================

LABOR:
Consider:
- additional labor
- crew changes
- overtime
- rework
- remobilization
- lost productivity

MATERIAL:
Consider:
- increased quantities
- changed materials
- reinforcement
- waste
- freight
- expedited material
- deleted materials or credits

EQUIPMENT:
Consider:
- additional equipment
- larger equipment
- longer duration
- pumping
- hauling
- lifting
- mobilization

SUBCONTRACTORS / VENDORS:
Consider impacts.

Do not invent dollar values unless enough pricing information exists.

==================================================
POTENTIAL INDIRECT COST IMPACTS
==================================================

Consider:
- supervision
- project management
- engineering
- general conditions
- overhead
- testing
- inspections
- permits
- cleanup
- documentation
- remobilization
- disruption
- lost productivity
- extended duration
- coordination
- procurement cancellation
- restocking

==================================================
SCHEDULE IMPACT
==================================================

Consider:
- activity duration
- start date
- finish date
- critical path
- float
- sequencing
- predecessors
- successors
- procurement
- lead times
- fabrication
- inspections
- approvals
- submittals
- access
- other trades
- rework

Do not invent specific delay durations.

If schedule data is missing, explain what is needed.

==================================================
COORDINATION, CODE, AND REGIONAL REQUIREMENTS
==================================================

COORDINATION:

Consider:
- structural work
- reinforcing
- embeds
- MEP
- waterproofing
- fireproofing
- finishes
- excavation
- formwork
- grading
- drainage
- utilities
- access
- site logistics
- adjacent trades
- temporary work
- inspections
- testing

CODE AND REGULATORY REVIEW:

Based on project type and confirmed location, consider where relevant:
- IBC
- IRC
- IEBC
- IFC
- NEC / NFPA 70
- NFPA standards
- OSHA
- accessibility
- energy codes
- plumbing codes
- mechanical codes
- state requirements
- local amendments
- permits
- inspection requirements
- testing requirements
- environmental regulations
- fire marshal requirements
- DOT requirements
- utility requirements
- manufacturer requirements

Do not invent exact code sections.

If jurisdiction is known:
- identify it
- identify potentially applicable code families
- state that adopted editions must be verified
- state that local amendments must be verified
- identify items requiring AHJ confirmation

If jurisdiction is unclear, state:

"Project jurisdiction is not sufficiently identified to determine
specific regional code requirements. Confirm the city, county,
state, and Authority Having Jurisdiction."

COMPANY / OWNER REQUIREMENTS:

Review supplied documents for:
- owner standards
- company safety requirements
- company QC requirements
- specifications
- contract exhibits
- approved manufacturers
- inspection procedures
- testing procedures
- submittal procedures
- change-management procedures

Do not invent missing requirements.

CODE IMPACT ON CHANGE:

Consider whether the change may require:
- redesign
- engineering review
- revised calculations
- permit revision
- resubmittal
- additional inspection
- additional testing
- structural review
- fire/life-safety review
- electrical review
- mechanical review
- plumbing review
- environmental review
- owner approval
- architect approval
- engineer approval

CODE / REGULATORY CONFIDENCE:
HIGH / MEDIUM / LOW

ITEMS TO VERIFY:

==================================================
SAFETY IMPACT
==================================================

Consider relevant risks involving:
- excavation
- fall protection
- lifting
- electrical exposure
- hot work
- silica
- heavy equipment
- temporary bracing
- structural stability
- traffic control
- crane operations
- material handling
- scaffolding
- trenching
- demolition
- PPE
- public protection

Only include relevant concerns.

==================================================
CONTRACT AND DOCUMENTATION RISK
==================================================

Consider:
- written directive
- revised drawing
- RFI
- field instruction
- owner direction
- notice requirements
- notice deadlines
- written authorization
- work before pricing
- time-and-material tracking
- daily reports
- photographs
- labor records
- equipment records
- delivery tickets
- purchase orders
- invoices
- correspondence
- emails
- meeting minutes

If contract terms are unavailable, state:

"Contract notice, authorization, and change-order requirements
should be reviewed."

==================================================
DOCUMENT CONFLICTS OR INCONSISTENCIES
==================================================

Identify conflicts between:
- contract
- scope
- specifications
- drawings
- RFIs
- revisions
- field instructions
- owner requirements
- user-entered project information

If none:
NONE IDENTIFIED

==================================================
MISSING INFORMATION
==================================================

List missing information that would materially improve the analysis.

==================================================
ASSUMPTIONS
==================================================

List assumptions.

If none:
NONE

==================================================
SUPPORTING REFERENCES
==================================================

For each important reference provide:

DOCUMENT:

PAGE:

REQUIREMENT / CHANGE:

WHY IT MATTERS:

==================================================
RECOMMENDED ACTION
==================================================

Provide practical step-by-step recommendations.

Consider:
1. Verify the revised requirement.
2. Confirm the governing drawing set.
3. Compare against the executed contract and scope.
4. Review drawings and specifications.
5. Confirm jurisdiction.
6. Review code/regulatory requirements.
7. Review owner/company requirements.
8. Document directives.
9. Quantify added/deleted work.
10. Evaluate labor.
11. Evaluate material.
12. Evaluate equipment.
13. Evaluate schedule.
14. Evaluate other trades.
15. Evaluate inspection/testing.
16. Review notice requirements.
17. Preserve records.
18. Prepare pricing/change documentation.
19. Obtain required authorization.
20. Track actual impacts.

==================================================
RISK FLAGS
==================================================

RED:
Serious commercial, contractual, safety,
code, or schedule concern.

YELLOW:
Requires review or additional information.

GREEN:
No major issue identified.

==================================================
FINAL ASSESSMENT
==================================================

Give a professional conclusion explaining:
- whether this appears to be a potential scope change
- why
- major cost risk
- major schedule risk
- major coordination risk
- major code/regulatory concern
- major documentation concern
- next action

End with:

"This analysis is a preliminary construction-management review
and is not a substitute for review by the project manager,
estimator, superintendent, design professional, Authority Having
Jurisdiction, or legal counsel where appropriate."
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
    "The system will analyze document text and can visually inspect "
    "plan sheets for scope, cost, schedule, code, safety, "
    "coordination, and documentation impacts."
)

st.warning(
    "This tool provides preliminary construction-management analysis. "
    "Important findings should be verified by qualified project personnel."
)


# ==========================================================
# PROJECT INFO
# ==========================================================

st.header("Project Information")

project_name = st.text_input(
    "Project Name"
)

project_location = st.text_input(
    "Project Location",
    placeholder="Example: Johnson City, Tennessee"
)

company_name = st.text_input(
    "Contractor / Company"
)


# ==========================================================
# DRAWING SETTINGS
# ==========================================================

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


# ==========================================================
# ORIGINAL DOCUMENTS
# ==========================================================

st.header("Original Project Documents")

original_files = st.file_uploader(
    "Upload original contract, drawings, specifications, scope, etc.",
    type=["pdf"],
    accept_multiple_files=True,
    key="original"
)


# ==========================================================
# REVISED DOCUMENTS
# ==========================================================

st.header("New / Revised Project Documents")

new_files = st.file_uploader(
    "Upload revised drawings, RFIs, bulletins, directives, etc.",
    type=["pdf"],
    accept_multiple_files=True,
    key="revised"
)


# ==========================================================
# RUN ANALYSIS
# ==========================================================

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

Use the supplied documents as the primary source of confirmed facts.

Use visual drawing evidence when images are supplied.

Clearly distinguish:
- confirmed facts
- assumptions
- missing information
- items requiring verification

If user-entered project information conflicts with the documents,
identify the conflict clearly.

Do not invent requirements.
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


# ==========================================================
# RESULTS
# ==========================================================

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
