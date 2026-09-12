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
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


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
    st.error("OpenAI API key not found.")
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
# TURN PDF PAGES INTO IMAGES
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

        # Higher resolution so dimensions and notes are readable
        matrix = fitz.Matrix(1.7, 1.7)

        pix = page.get_pixmap(
            matrix=matrix,
            alpha=False
        )

        image_bytes = pix.tobytes("png")

        encoded = base64.b64encode(
            image_bytes
        ).decode("utf-8")

        data_url = (
            f"data:image/png;base64,{encoded}"
        )

        images.append(
            {
                "document": uploaded_file.name,
                "page": page_index + 1,
                "image_url": data_url
            }
        )

    document.close()

    return images


# ==========================================================
# CREATE PDF REPORT
# ==========================================================

def create_pdf_report(project_name, analysis_text):

    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.65 * inch,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=20,
        spaceAfter=12,
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=13,
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyStyle",
        parent=styles["BodyText"],
        fontSize=9.5,
        leading=13,
        spaceAfter=5,
    )

    story = []

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
                body_style
            )
        )

    section_names = [
        "EXECUTIVE SUMMARY",
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
        "FINAL ASSESSMENT",
    ]

    for line in analysis_text.splitlines():

        clean = line.strip()

        if not clean:
            story.append(Spacer(1, 5))
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

    document.build(story)

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
3. Images of original plan sheets.
4. Images of revised plan sheets.

Use BOTH the document text and visible drawing information.

You must visually inspect plan sheets for changes including:

- dimensions
- thicknesses
- elevations
- quantities
- materials
- callouts
- keynote changes
- detail references
- section references
- structural notes
- equipment
- doors
- walls
- slab information
- reinforcement
- MEP information
- penetrations
- utilities
- grading
- finishes
- revisions
- clouds
- delta symbols
- revision notes
- schedules
- added work
- deleted work
- relocated work

IMPORTANT:

Never claim you can see something that is not clearly visible.

If a drawing is difficult to read, say so.

Do not invent dimensions.

Do not invent quantities.

Do not invent code sections.

Do not invent prices.

Do not invent contract language.

Clearly distinguish:

CONFIRMED FACT

LIKELY IMPACT

ASSUMPTION

ITEM REQUIRING VERIFICATION

When comparing drawings, identify the document name and page number.

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
VISUAL DRAWING COMPARISON
==================================================

Identify changes found by visually examining the original and revised sheets.

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

If the visual evidence is unclear, explicitly say so.

==================================================
PROJECT AND JURISDICTION INFORMATION
==================================================

Identify when available:

PROJECT NAME:

PROJECT LOCATION:

CITY:

COUNTY:

STATE:

OWNER:

GENERAL CONTRACTOR:

SUBCONTRACTOR:

DESIGN PROFESSIONAL:

AUTHORITY HAVING JURISDICTION:

APPLICABLE CODE INFORMATION:

Do not invent missing information.

==================================================
ORIGINAL CONTRACTED REQUIREMENT
==================================================

Describe the relevant original requirements.

Cite document and page.

==================================================
NEW OR REVISED REQUIREMENT
==================================================

Describe the revised requirements.

Cite document and page.

==================================================
DETAILED SCOPE COMPARISON
==================================================

For each meaningful difference:

ITEM:

ORIGINAL:

NEW:

DIFFERENCE:

POTENTIAL CONSEQUENCE:

SOURCE:

==================================================
QUANTITY AND TECHNICAL ANALYSIS
==================================================

Calculate differences when adequate information exists.

Show calculations.

Clearly state assumptions.

==================================================
POTENTIAL DIRECT COST IMPACTS
==================================================

Analyze:

LABOR

MATERIAL

EQUIPMENT

SUBCONTRACTORS

VENDORS

Do not invent dollar values.

==================================================
POTENTIAL INDIRECT COST IMPACTS
==================================================

Consider:

supervision
project management
engineering
general conditions
overhead
inspection
testing
cleanup
remobilization
lost productivity
coordination

==================================================
SCHEDULE IMPACT
==================================================

Consider:

duration
critical path
float
sequencing
procurement
lead times
fabrication
inspection
approval
submittals
other trades

Do not invent delay durations.

==================================================
COORDINATION, CODE, AND REGIONAL REQUIREMENTS
==================================================

Review possible coordination impacts involving:

structural work
reinforcement
embeds
MEP
waterproofing
fireproofing
finishes
excavation
formwork
grading
utilities
access
adjacent trades
site logistics

Review potentially relevant:

IBC
IRC
IEBC
IFC
NEC / NFPA 70
NFPA
OSHA
accessibility requirements
energy codes
mechanical codes
plumbing codes
state requirements
local amendments
permits
inspection requirements
testing requirements
fire marshal requirements
utility requirements
manufacturer requirements

Base regional discussion on the provided project location.

Do not invent code sections.

Clearly identify anything requiring AHJ verification.

Review owner/company requirements when documents provide them.

==================================================
SAFETY IMPACT
==================================================

Identify safety impacts reasonably caused by the revision.

==================================================
CONTRACT AND DOCUMENTATION RISK
==================================================

Consider:

written directive
revision
RFI
notice requirements
change authorization
daily reports
photographs
labor records
equipment records
delivery tickets
emails
meeting minutes

==================================================
DOCUMENT CONFLICTS OR INCONSISTENCIES
==================================================

Identify conflicts between drawings, specifications, contract scope,
RFIs, or other supplied documents.

==================================================
MISSING INFORMATION
==================================================

List information needed for a stronger determination.

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

Provide step-by-step contractor recommendations.

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

Give a professional construction-management conclusion.

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
    "The system will analyze document text AND visually inspect "
    "plan sheets for potential changes."
)

st.warning(
    "This is preliminary construction-management analysis. "
    "Important findings should be verified by qualified project personnel."
)


# ==========================================================
# PROJECT INFORMATION
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
# VISUAL SETTINGS
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
    "Higher page counts provide more drawing coverage but increase API usage and cost."
)


# ==========================================================
# FILE UPLOADS
# ==========================================================

st.header("Original Project Documents")

original_files = st.file_uploader(
    "Upload original contract, drawings, specifications, scope, etc.",
    type=["pdf"],
    accept_multiple_files=True,
    key="original"
)

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
            "Reading documents and visually reviewing plan sheets..."
        ):

            try:

                original_text = ""
                revised_text = ""

                original_images = []
                revised_images = []

                # ORIGINAL
                for file in original_files:

                    original_text += extract_pdf_text(
                        file
                    )

                    if visual_analysis:

                        original_images.extend(
                            pdf_pages_to_images(
                                file,
                                int(max_pages)
                            )
                        )

                # REVISED
                for file in new_files:

                    revised_text += extract_pdf_text(
                        file
                    )

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

PROJECT LOCATION:
{project_location}

CONTRACTOR / COMPANY:
{company_name}


ORIGINAL DOCUMENT TEXT:

{original_text}


REVISED DOCUMENT TEXT:

{revised_text}


Compare the original project information against the revised
project information.

Use both text and visual drawing evidence.

Identify scope, drawing, quantity, cost, schedule, coordination,
code, safety, and documentation impacts.

Do not invent facts.
"""

                content = [
                    {
                        "type": "input_text",
                        "text": prompt_text
                    }
                ]

                # Label and attach original pages
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

                # Label and attach revised pages
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
        st.session_state.get(
            "project_name",
            "Project"
        )
        .strip()
        .replace(" ", "_")
    )

    if not safe_project_name:
        safe_project_name = "Project"

    st.download_button(
        "📄 Download PDF Report",
        data=pdf_report,
        file_name=(
            f"{safe_project_name}_Scope_Analysis.pdf"
        ),
        mime="application/pdf",
        use_container_width=True
    )
