import os
import tempfile
from io import BytesIO

import streamlit as st
from pypdf import PdfReader
from openai import OpenAI
from dotenv import load_dotenv

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


# --------------------------------------------------
# API KEY
# --------------------------------------------------

load_dotenv()

api_key = None

# Streamlit Cloud
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    pass

# Local computer fallback
if not api_key:
    api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error(
        "OpenAI API key not found. Add OPENAI_API_KEY to Streamlit Secrets."
    )
    st.stop()

client = OpenAI(api_key=api_key)


# --------------------------------------------------
# READ UPLOADED PDF
# --------------------------------------------------

def read_pdf(uploaded_file):

    uploaded_file.seek(0)

    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=".pdf"
    ) as temp_file:

        temp_file.write(uploaded_file.read())
        temp_path = temp_file.name

    reader = PdfReader(temp_path)

    text = ""

    for page_number, page in enumerate(reader.pages, start=1):

        page_text = page.extract_text() or ""

        text += (
            f"\n\n--- DOCUMENT: {uploaded_file.name} "
            f"| PAGE {page_number} ---\n"
        )

        text += page_text

    os.remove(temp_path)

    return text


# --------------------------------------------------
# CREATE PDF REPORT
# --------------------------------------------------

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
        spaceAfter=10,
    )

    subtitle_style = ParagraphStyle(
        "SubtitleStyle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=10,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "HeadingStyle",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
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
                subtitle_style
            )
        )

    section_names = [
        "EXECUTIVE SUMMARY",
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
                Paragraph(clean, heading_style)
            )

        else:

            if clean.startswith("- "):
                clean = "• " + clean[2:]

            story.append(
                Paragraph(clean, body_style)
            )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            "This report is a preliminary construction-management "
            "review and should be verified by appropriate project "
            "personnel before decisions are made.",
            body_style,
        )
    )

    document.build(story)

    buffer.seek(0)

    return buffer.getvalue()


# --------------------------------------------------
# AI INSTRUCTIONS
# --------------------------------------------------

instructions = """
You are an AI construction scope, change-management,
project-risk, code-awareness, and contract-document analysis assistant.

Your job is to compare an original contracted scope against
a new or revised project document.

Identify potential:
- scope changes
- quantity changes
- cost impacts
- schedule impacts
- productivity impacts
- coordination issues
- safety concerns
- code concerns
- regional requirements
- owner requirements
- company requirements
- documentation risks

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
- Do not invent schedule delays.
- Do not invent code sections.
- Do not invent local amendments.
- Do not invent company policies.
- Do not invent owner requirements.
- Clearly separate facts from assumptions.
- Clearly identify missing information.
- Cite document names and page numbers whenever possible.
- Be detailed and construction-specific.
- Consider direct and indirect impacts.
- Consider impacts on adjacent work and other trades.
- Consider project location when available.
- Consider contract, specifications, drawings, RFIs,
  owner requirements, and company requirements when supplied.

If jurisdiction cannot be determined, say so clearly.

For code review:
- identify potentially applicable code families only when relevant
- identify the project jurisdiction when supported by the documents
- do not invent exact code sections
- note that adopted editions and local amendments must be verified
- identify items requiring confirmation with the Authority Having Jurisdiction
- treat code review as preliminary

Use this report structure:

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

APPLICABLE CODE OR CODE EDITION:
Only state confirmed information.

PROJECT-SPECIFIC STANDARDS:

If information is missing, clearly say NOT PROVIDED.

==================================================
ORIGINAL CONTRACTED REQUIREMENT
==================================================

Describe the original work in detail.

Consider:
- scope
- dimensions
- quantities
- materials
- location
- responsibilities
- exclusions
- limitations
- specifications
- drawing requirements

Include document and page references.

==================================================
NEW OR REVISED REQUIREMENT
==================================================

Describe exactly what changed.

Consider:
- added work
- deleted work
- quantity changes
- dimension changes
- material changes
- location changes
- sequence changes
- schedule changes
- responsibility changes
- quality changes
- inspection changes
- testing changes

Include document and page references.

==================================================
DETAILED SCOPE COMPARISON
==================================================

Compare each meaningful change using:

ITEM:

ORIGINAL:

NEW:

DIFFERENCE:

POTENTIAL CONSEQUENCE:

Clearly distinguish confirmed differences from assumptions.

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

Clearly state assumptions.

Do not invent missing dimensions.

==================================================
POTENTIAL DIRECT COST IMPACTS
==================================================

LABOR:
Consider:
- additional labor
- crew changes
- skill requirements
- overtime
- rework
- remobilization
- productivity

MATERIAL:
Consider:
- increased quantities
- changed materials
- reinforcement
- waste
- freight
- expedited materials

EQUIPMENT:
Consider:
- equipment changes
- additional equipment
- duration
- mobilization
- pumping
- hauling
- lifting

SUBCONTRACTORS / VENDORS:
Consider potential impacts.

Do not invent dollar values unless enough pricing information is supplied.

==================================================
POTENTIAL INDIRECT COST IMPACTS
==================================================

Consider:
- supervision
- project management
- field engineering
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

==================================================
SCHEDULE IMPACT
==================================================

Consider:
- activity duration
- start
- finish
- critical path
- float
- sequencing
- predecessor activities
- successor activities
- procurement
- lead time
- fabrication
- inspections
- approvals
- submittals
- access
- other trades

Do not invent specific delay days.

If schedule information is missing, say what is needed.

==================================================
COORDINATION, CODE, AND REGIONAL REQUIREMENTS
==================================================

COORDINATION IMPACTS:

Consider relevant impacts involving:
- structural work
- elevations
- reinforcing
- embeds
- MEP penetrations
- waterproofing
- fireproofing
- finishes
- excavation
- formwork
- grading
- drainage
- utilities
- equipment access
- site logistics
- adjacent trades
- temporary work
- inspections
- testing

CODE AND REGULATORY REVIEW:

Based on the project type and confirmed project location,
consider where relevant:

- International Building Code
- International Residential Code
- International Existing Building Code
- International Fire Code
- NEC / NFPA 70
- NFPA standards
- OSHA
- accessibility requirements
- energy codes
- plumbing codes
- mechanical codes
- state amendments
- local amendments
- permits
- inspections
- testing requirements
- environmental regulations
- DOT requirements
- fire marshal requirements
- utility requirements
- manufacturer requirements

Do not invent exact sections.

REGIONAL REQUIREMENTS:

If city, county, or state is confirmed:
- identify the jurisdiction
- identify potentially applicable code families
- state that the adopted code edition must be verified
- state that local amendments must be verified
- identify items requiring AHJ confirmation

If jurisdiction is unclear, write:

"Project jurisdiction is not sufficiently identified to determine
specific regional code requirements. Confirm the city, county,
state, and Authority Having Jurisdiction."

COMPANY / OWNER REQUIREMENTS:

Look for:
- company safety requirements
- company quality requirements
- owner design standards
- project specifications
- contract exhibits
- approved manufacturers
- inspection procedures
- testing procedures
- submittal requirements
- change-management requirements

Do not invent company requirements.

If none are provided, state:

"Company-specific requirements were not provided and should
be reviewed before finalizing the analysis."

CODE IMPACT ON THE CHANGE:

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

Explain why.

ITEMS TO VERIFY:

List relevant verification items.

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

Do not invent safety issues unrelated to the change.

==================================================
CONTRACT AND DOCUMENTATION RISK
==================================================

Consider:
- written directive
- revised drawing
- RFI
- field instruction
- owner direction
- notice requirement
- notice deadline
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

If full contract terms are unavailable, state:

"Contract notice, authorization, and change-order requirements
should be reviewed."

==================================================
DOCUMENT CONFLICTS OR INCONSISTENCIES
==================================================

Identify conflicts between supplied documents.

If none are identified, write:

NONE IDENTIFIED

==================================================
MISSING INFORMATION
==================================================

List missing information that could materially improve the analysis.

==================================================
ASSUMPTIONS
==================================================

List every important assumption.

If none:

NONE

==================================================
SUPPORTING REFERENCES
==================================================

For each important reference provide:

DOCUMENT:

PAGE:

RELEVANT REQUIREMENT:

WHY IT MATTERS:

==================================================
RECOMMENDED ACTION
==================================================

Provide practical step-by-step recommendations.

Consider:
1. Verify the revised requirement.
2. Compare against executed contract and scope.
3. Review drawings and specifications.
4. Confirm project jurisdiction.
5. Review code and regulatory requirements.
6. Review owner requirements.
7. Review company requirements.
8. Document the directive.
9. Quantify added or deleted work.
10. Evaluate labor.
11. Evaluate materials.
12. Evaluate equipment.
13. Evaluate schedule.
14. Evaluate other trades.
15. Evaluate inspection and testing.
16. Review notice requirements.
17. Preserve project records.
18. Prepare pricing or change documentation.
19. Obtain required authorization.
20. Track actual impacts.

==================================================
RISK FLAGS
==================================================

Use:

RED:
Serious commercial, contractual, safety, code,
or schedule concern.

YELLOW:
Requires review or more information.

GREEN:
No major concern identified.

==================================================
FINAL ASSESSMENT
==================================================

Give a concise professional conclusion explaining:
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


# --------------------------------------------------
# PAGE
# --------------------------------------------------

st.set_page_config(
    page_title="Construction Scope AI",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ Construction Scope AI")

st.write(
    "Compare original construction documents against new or revised "
    "project documents to identify potential scope, cost, schedule, "
    "coordination, code, safety, and documentation impacts."
)

st.info(
    "This tool provides preliminary construction-management analysis. "
    "Results should be verified by qualified project personnel."
)


# --------------------------------------------------
# PROJECT INFORMATION
# --------------------------------------------------

st.header("Project Information")

project_name = st.text_input(
    "Project Name",
    placeholder="Example: Medical Office Building"
)

project_location = st.text_input(
    "Project Location",
    placeholder="Example: Johnson City, Tennessee"
)

company_name = st.text_input(
    "Contractor / Company",
    placeholder="Example: ABC Concrete"
)


# --------------------------------------------------
# FILES
# --------------------------------------------------

st.header("Original Project Documents")

original_files = st.file_uploader(
    "Upload original contracts, scopes, specifications, drawings, or other original documents",
    type=["pdf"],
    accept_multiple_files=True,
    key="original_files",
)

st.header("New or Revised Project Documents")

new_files = st.file_uploader(
    "Upload revised drawings, RFIs, field directives, bulletins, or other changed documents",
    type=["pdf"],
    accept_multiple_files=True,
    key="new_files",
)


# --------------------------------------------------
# ANALYSIS
# --------------------------------------------------

if st.button(
    "Analyze Project",
    type="primary",
    use_container_width=True
):

    if not original_files:

        st.error(
            "Upload at least one original project document."
        )

    elif not new_files:

        st.error(
            "Upload at least one new or revised project document."
        )

    else:

        with st.spinner(
            "Reviewing project documents and preparing analysis..."
        ):

            try:

                original_text = ""

                for file in original_files:
                    original_text += read_pdf(file)

                new_text = ""

                for file in new_files:
                    new_text += read_pdf(file)

                user_input = f"""
PROJECT NAME:
{project_name}

PROJECT LOCATION PROVIDED BY USER:
{project_location}

CONTRACTOR / COMPANY:
{company_name}


ORIGINAL PROJECT DOCUMENTS:

{original_text}


NEW OR REVISED PROJECT DOCUMENTS:

{new_text}


Perform a detailed construction-management analysis.

Use the supplied documents as the primary source of confirmed facts.

The user-provided project location may be used to help identify
the likely project region, but do not invent code editions,
local amendments, AHJ requirements, owner requirements,
or company policies.

Clearly distinguish:
- confirmed facts
- assumptions
- missing information
- items requiring verification
"""

                response = client.responses.create(
                    model="gpt-5.6",
                    reasoning={
                        "effort": "medium"
                    },
                    instructions=instructions,
                    input=user_input,
                )

                analysis = response.output_text

                st.session_state["analysis"] = analysis
                st.session_state["project_name"] = project_name

                st.success(
                    "Project analysis complete."
                )

            except Exception as error:

                st.error(
                    "The analysis could not be completed."
                )

                st.code(str(error))


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

if "analysis" in st.session_state:

    st.header(
        "Construction Scope Analysis"
    )

    analysis = st.session_state["analysis"]

    st.markdown(analysis)

    pdf_bytes = create_pdf_report(
        st.session_state.get(
            "project_name",
            ""
        ),
        analysis,
    )

    safe_name = (
        st.session_state
        .get("project_name", "Project")
        .strip()
        .replace(" ", "_")
    )

    if not safe_name:
        safe_name = "Project"

    st.download_button(
        "📄 Download PDF Report",
        data=pdf_bytes,
        file_name=f"{safe_name}_Scope_Analysis.pdf",
        mime="application/pdf",
        use_container_width=True,
    )
