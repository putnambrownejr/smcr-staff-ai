from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.services.agents.base import Agent, AgentContext


class CorrespondenceFormattingAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="correspondence-formatting",
            name="Correspondence Formatting Assistant",
            description=(
                "Advisory assistant for naval correspondence, Marine Corps supplement formatting, "
                "staff packages, letters, memos, endorsements, and routing checklists."
            ),
            domain="administration",
            intended_users=["SMCR officers", "staff officers", "AdminO", "S-1", "Chief of Staff / Aide"],
            allowed_sources=[
                "SECNAV M-5216.5 Department of the Navy Correspondence Manual",
                "MCO 5216.20B Marine Corps Supplement to the DON Correspondence Manual",
                "local templates marked UNCLASSIFIED",
            ],
            disallowed_inputs=[
                "classified content",
                "CUI",
                "PII",
                "sensitive personnel matters",
                "non-public command correspondence",
            ],
            system_prompt=(
                "Provide advisory correspondence-formatting checklists and draft structures. "
                "Require human review and cite current correspondence manuals when RAG is connected."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Correspondence formatting advisory draft.\n\n"
            "Use this for UNCLASSIFIED formatting support only. Verify against the current DON "
            "Correspondence Manual and Marine Corps supplement before release.\n\n"
            "Checklist:\n"
            "- Identify the correspondence type: naval letter, business letter, memorandum, endorsement, "
            "standard letter, point paper, or routing package.\n"
            "- Confirm sender, addressee, via line, subject, references, enclosures, signature authority, "
            "and copy-to requirements.\n"
            "- Use short, plain-language paragraphs with action-focused opening and closing statements.\n"
            "- Keep references and enclosures traceable; avoid citing stale local templates as authority.\n"
            "- Confirm classification markings, privacy review, release authority, and records-management handling.\n"
            "- Route final correspondence through the appropriate human admin/reviewer chain.\n\n"
            "Common output patterns I can later support:\n"
            "- Format checklist for a staff package\n"
            "- Skeleton naval letter or endorsement\n"
            "- Memo review for missing fields\n"
            "- Staff-package routing checklist\n"
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
                "MCO 5216.20B w/Admin Ch-4 Marine Corps Supplement to the DON Correspondence Manual",
            ],
            structured_citations=[
                StructuredCitation(
                    title="SECNAV M-5216.5 CH-1 Department of the Navy Correspondence Manual",
                    url="https://www.secnav.navy.mil/doni/SECNAV%20Manuals1/5216.5%20%20CH-1.pdf",
                    publisher="Department of the Navy",
                    confidence=Confidence.low,
                    notes="Manifest/source-note citation; exact section citation requires RAG ingestion.",
                ),
                StructuredCitation(
                    title=(
                        "MCO 5216.20B w/Admin Ch-4 Marine Corps Supplement to the Department of the Navy "
                        "Correspondence Manual"
                    ),
                    url=(
                        "https://www.marines.mil/News/Publications/MCPEL/Electronic-Library-Display/"
                        "Article/2795618/mco-521620b-wadmin-ch-4/"
                    ),
                    publisher="Headquarters Marine Corps",
                    confidence=Confidence.low,
                    notes="Manifest/source-note citation; verify current MCPEL status before use.",
                ),
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "What correspondence type are you preparing?",
                "Who is the sender and approval authority?",
                "Do you need a checklist, a skeleton format, or a review of a draft?",
            ],
        )


def build_correspondence_formatting_agent() -> CorrespondenceFormattingAgent:
    return CorrespondenceFormattingAgent()
