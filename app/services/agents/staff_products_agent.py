from app.schemas.agents import AgentMetadata, AgentRunResponse
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.services.agents.base import Agent, AgentContext
from app.services.staff_products.builder import StaffProductBuilder


class StaffProductsAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="staff-products",
            name="Staff Products Assistant",
            description="Builds advisory scaffolds for OPORDs, WARNOs, FRAGOs, SITREPs, AARs, and correspondence.",
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
                "What product type do you need: OPORD, WARNO, FRAGO, SITREP, AAR, letter, memo, or endorsement?",
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
    if "aar" in text or "after action" in text:
        return StaffProductType.aar
    if "letter" in text:
        return StaffProductType.naval_letter
    if "memo" in text:
        return StaffProductType.memorandum
    return StaffProductType.opord


def build_staff_products_agent() -> StaffProductsAgent:
    return StaffProductsAgent()
