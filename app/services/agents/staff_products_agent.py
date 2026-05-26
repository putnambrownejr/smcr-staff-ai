from app.schemas.agents import AgentMetadata, AgentRunResponse
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.services.agents.base import Agent, AgentContext
from app.services.staff_products.builder import StaffProductBuilder


class StaffProductsAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="staff-products",
            name="Staff Products Assistant",
            description=(
                "Builds advisory scaffolds for OPORDs, WARNOs, FRAGOs, SITREPs, AARs, "
                "running estimates, synchronization matrices, admin estimates, admin task trackers, routing matrices, "
                "pre-drill admin readiness checks, decision support matrices, due-out trackers, "
                "collection matrices, sustainment matrices, "
                "medical estimates, public affairs plans, security annexes, resource estimates, inspection "
                "readiness plans, IPBs, decision briefs, "
                "command-update briefs, and correspondence."
            ),
            domain="staff products",
            intended_users=["SMCR officers", "staff officers", "company and battalion staff"],
            allowed_sources=[
                "public Marine Corps doctrine",
                "correspondence formatting sources",
                "training-only fictional context",
                "user-confirmed local context",
            ],
            disallowed_inputs=[
                "classified information",
                "CUI",
                "real operational plans",
                "exact current movements",
                "COMSEC",
                "frequencies",
            ],
            system_prompt=(
                "Create advisory staff-product scaffolds, not authoritative orders. "
                "Require source verification and human review."
            ),
        )
        self.builder = StaffProductBuilder()

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        product_type = _product_type_from_context(context, input_text)
        draft = self.builder.build(
            StaffProductDraftRequest(
                product_type=product_type,
                topic=input_text,
                training_or_fictional=context.request_is_training_or_fictional,
            )
        )
        sections = "\n".join(
            f"{section.heading}\n" + "\n".join(f"- {prompt}" for prompt in section.prompts)
            for section in draft.sections
        )
        answer = f"{draft.title}\n\n{sections}\n\nReview checklist:\n" + "\n".join(
            f"- {item}" for item in draft.review_checklist
        )
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=draft.citations,
            structured_citations=draft.structured_citations,
            confidence=draft.confidence,
            follow_up_questions=[
                (
                    "What product type do you need: OPORD, WARNO, FRAGO, SITREP, AAR, "
                    "running estimate, synchronization matrix, admin estimate, admin task tracker, routing matrix, "
                    "pre-drill admin readiness check, decision support matrix, due-out tracker, "
                    "collection matrix, sustainment matrix, medical "
                    "estimate, public affairs plan, security annex, resource estimate, inspection readiness plan, "
                    "IPB, decision brief, command update brief, "
                    "letter, memo, or endorsement?"
                ),
                "Is this fictional/training-only or a real administrative workflow?",
                "What audience, echelon, and required format should it follow?",
            ],
        )


def _product_type_from_context(context: AgentContext, input_text: str) -> StaffProductType:
    raw = str(context.extra.get("product_type") or "").lower()
    text = f"{raw} {input_text}".lower()
    for product_type in StaffProductType:
        if product_type.value in text or product_type.value.replace("_", " ") in text:
            return product_type
    if "warno" in text:
        return StaffProductType.warno
    if "frago" in text:
        return StaffProductType.frago
    if "sitrep" in text:
        return StaffProductType.sitrep
    if "running estimate" in text or "staff estimate" in text:
        return StaffProductType.running_estimate
    if "synchronization matrix" in text or "sync matrix" in text or "synchronization board" in text:
        return StaffProductType.synchronization_matrix
    if "admin estimate" in text or ("s-1" in text and "estimate" in text):
        return StaffProductType.admin_estimate
    if "admin task tracker" in text or ("s-1" in text and "task tracker" in text):
        return StaffProductType.admin_task_tracker
    if "routing matrix" in text and ("admin" in text or "orders" in text or "s-1" in text):
        return StaffProductType.routing_matrix
    if "pre-drill admin readiness check" in text or "pre drill admin readiness check" in text:
        return StaffProductType.pre_drill_admin_readiness_check
    if "decision support matrix" in text or "decision matrix" in text:
        return StaffProductType.decision_support_matrix
    if "due-out tracker" in text or "due out tracker" in text or "suspense tracker" in text:
        return StaffProductType.due_out_tracker
    if "collection matrix" in text or "pir/ir" in text or "pir ir" in text or "collection plan" in text:
        return StaffProductType.collection_matrix
    if "sustainment matrix" in text or "movement table" in text or "movement matrix" in text:
        return StaffProductType.sustainment_matrix
    if "medical estimate" in text:
        return StaffProductType.medical_estimate
    if (
        "public affairs plan" in text
        or "commstrat plan" in text
        or "communication strategy plan" in text
        or "release approval matrix" in text
        or "release matrix" in text
        or "themes and messages" in text
        or "response to query" in text
    ):
        return StaffProductType.public_affairs_plan
    if (
        "security annex" in text
        or "force protection" in text
        or "access control plan" in text
        or "visitor control" in text
        or "traffic control plan" in text
    ):
        return StaffProductType.security_annex
    if (
        "resource estimate" in text
        or "funding risk" in text
        or "priority tradeoff brief" in text
        or "resourcing decision point" in text
        or "budget tradeoff" in text
    ):
        return StaffProductType.resource_estimate
    if (
        "inspection readiness plan" in text
        or "readiness trend memo" in text
        or "ig inquiry boundary" in text
        or "inspection plan" in text
        or "inspector general" in text
    ):
        return StaffProductType.inspection_readiness_plan
    if "decision brief" in text or ("decision" in text and ("brief" in text or "slides" in text or "deck" in text)):
        return StaffProductType.decision_brief
    if "command update" in text or "update brief" in text:
        return StaffProductType.command_update_brief
    if "aar" in text or "after action" in text:
        return StaffProductType.aar
    if (
        "ipb" in text
        or "intelligence preparation" in text
        or "intelligence prep" in text
        or "prep of the battlespace" in text
    ):
        return StaffProductType.ipb
    if "slides" in text or "slide deck" in text or "powerpoint" in text or "briefing deck" in text:
        return StaffProductType.decision_brief
    if "letter" in text:
        return StaffProductType.naval_letter
    if "memo" in text:
        return StaffProductType.memorandum
    return StaffProductType.opord


def build_staff_products_agent() -> StaffProductsAgent:
    return StaffProductsAgent()
