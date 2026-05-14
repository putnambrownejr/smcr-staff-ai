from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence, StructuredCitation
from app.schemas.pki import PkiIssueType, PkiTroubleshootingRequest
from app.services.admin.pki_support import PkiTroubleshootingService
from app.services.agents.base import Agent, AgentContext


class PkiTroubleshooterAgent(Agent):
    def __init__(self) -> None:
        self._service = PkiTroubleshootingService()
        self.metadata = AgentMetadata(
            id="pki-cac-troubleshooter",
            name="PKI / CAC Troubleshooter",
            description=(
                "Provides advisory troubleshooting structure for CAC, certificate, middleware, browser-auth, "
                "and portal-access issues in public/unclassified workflows."
            ),
            domain="administration",
            intended_users=["SMCR officers", "AdminO", "S-1", "Chief of Staff / Aide", "individual Marines"],
            allowed_sources=[
                "public PKI/CAC troubleshooting references",
                "public browser and portal guidance",
                "local user symptom descriptions",
            ],
            disallowed_inputs=[
                "PINs",
                "private keys",
                "certificate screenshots with sensitive serial details",
                "full personnel records",
            ],
            system_prompt=(
                "Provide practical PKI/CAC troubleshooting steps and escalation structure. "
                "Do not request secrets, do not claim authoritative enterprise IT guidance, "
                "and do not process sensitive certificate material."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        issue_type = _infer_issue_type(input_text)
        response = self._service.build(
            PkiTroubleshootingRequest(
                title="Agent request",
                issue_type=issue_type,
                symptoms=[input_text],
                on_government_furnished_equipment=_infer_gfe_context(context),
            )
        )
        answer = (
            "PKI/CAC troubleshooting advisory.\n\n"
            f"Focus area: {response.issue_type.value.replace('_', ' ')}.\n\n"
            "Likely causes:\n"
            + "\n".join(f"- {item}" for item in response.likely_causes)
            + "\n\nImmediate checks:\n"
            + "\n".join(f"- {item}" for item in response.immediate_checks)
            + "\n\nDeeper checks:\n"
            + "\n".join(f"- {item}" for item in response.deeper_checks)
            + "\n\nEscalation path:\n"
            + "\n".join(f"- {item}" for item in response.escalation_path)
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=[
                "Public PKI/CAC troubleshooting references",
                "Portal/browser support guidance",
            ],
            structured_citations=[
                StructuredCitation(
                    title="Public PKI/CAC troubleshooting references",
                    confidence=Confidence.low,
                    notes="Use this as an advisory placeholder until a verified public source stack is added.",
                )
            ],
            confidence=Confidence.low,
            follow_up_questions=[
                "Is the failure happening before certificate selection, during selection, or after login?",
                "Does the same CAC work on another approved device or portal?",
                "Are you on GFE, and which browser or client is affected?",
            ],
        )


def _infer_issue_type(input_text: str) -> PkiIssueType:
    text = input_text.lower()
    if "reader" in text or "not detected" in text or "not reading" in text:
        return PkiIssueType.cac_not_detected
    if "certificate" in text or "cert" in text:
        return PkiIssueType.certificate_issue
    if "middleware" in text:
        return PkiIssueType.middleware_issue
    if "chrome" in text or "edge" in text or "firefox" in text or "browser" in text:
        return PkiIssueType.browser_auth_issue
    if "sign" in text or "encrypt" in text or "smime" in text or "outlook" in text:
        return PkiIssueType.signing_encryption_issue
    if "portal" in text or "marinenet" in text or "mol" in text or "mctims" in text:
        return PkiIssueType.portal_access_issue
    return PkiIssueType.general


def _infer_gfe_context(context: AgentContext) -> bool | None:
    value = context.extra.get("on_government_furnished_equipment")
    if isinstance(value, bool):
        return value
    return None


def build_pki_troubleshooter_agent() -> PkiTroubleshooterAgent:
    return PkiTroubleshooterAgent()
