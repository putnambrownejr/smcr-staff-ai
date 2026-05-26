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
                "air-support estimates, air-ground coordination matrices, aviation supportability matrices, "
                "running estimates, synchronization matrices, ORM worksheets, no-go criteria, "
                "residual-risk decision notes, "
                "rehearsal safety briefs, admin estimates, admin task trackers, routing matrices, "
                "pre-drill admin readiness checks, troop-flow checklists, formation/transition matrices, "
                "leader touchpoint plans, decision support matrices, due-out trackers, "
                "collection matrices, sustainment matrices, movement tables, "
                "medical estimates, CASEVAC quick cards, religious support plans, RMT support matrices, "
                "morale and welfare estimates, road-to-war briefs, public affairs plans, security annexes, "
                "visitor-control checklists, traffic and parking control plans, "
                "resource estimates, inspection readiness plans, "
                "IPBs, decision briefs, "
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
                    "air support estimate, air-ground coordination matrix, aviation supportability matrix, "
                    "running estimate, synchronization matrix, ORM worksheet, no-go criteria, "
                    "residual-risk decision note, "
                    "rehearsal safety brief, admin estimate, admin task tracker, routing matrix, "
                    "pre-drill admin readiness check, troop-flow checklist, formation/transition matrix, "
                    "leader touchpoint plan, decision support matrix, due-out tracker, "
                    "collection matrix, sustainment matrix, movement table, medical "
                    "estimate, CASEVAC quick card, religious support plan, RMT support matrix, "
                    "morale and welfare estimate, road-to-war brief, public affairs plan, security annex, "
                    "visitor-control checklist, traffic and parking control plan, "
                    "resource estimate, inspection readiness plan, "
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
    if "visitor-control checklist" in text or "visitor control checklist" in text:
        return StaffProductType.visitor_control_checklist
    if "traffic and parking control plan" in text or "traffic control plan" in text or "parking control" in text:
        return StaffProductType.traffic_parking_control_plan
    for product_type in StaffProductType:
        if product_type.value in text or product_type.value.replace("_", " ") in text:
            return product_type
    if "warno" in text:
        return StaffProductType.warno
    if "frago" in text:
        return StaffProductType.frago
    if "sitrep" in text:
        return StaffProductType.sitrep
    if "air support estimate" in text:
        return StaffProductType.air_support_estimate
    if "air-ground coordination matrix" in text or "air ground coordination matrix" in text:
        return StaffProductType.air_ground_coordination_matrix
    if "aviation supportability matrix" in text:
        return StaffProductType.aviation_supportability_matrix
    if "running estimate" in text or "staff estimate" in text:
        return StaffProductType.running_estimate
    if "synchronization matrix" in text or "sync matrix" in text or "synchronization board" in text:
        return StaffProductType.synchronization_matrix
    if "orm worksheet" in text or ("orm" in text and "worksheet" in text):
        return StaffProductType.orm_worksheet
    if "no-go criteria" in text or "no go criteria" in text:
        return StaffProductType.no_go_criteria
    if "residual-risk decision note" in text or "residual risk decision note" in text:
        return StaffProductType.residual_risk_decision_note
    if "rehearsal safety brief" in text or ("safety brief" in text and "rehearsal" in text):
        return StaffProductType.rehearsal_safety_brief
    if "admin estimate" in text or ("s-1" in text and "estimate" in text):
        return StaffProductType.admin_estimate
    if "admin task tracker" in text or ("s-1" in text and "task tracker" in text):
        return StaffProductType.admin_task_tracker
    if "routing matrix" in text and ("admin" in text or "orders" in text or "s-1" in text):
        return StaffProductType.routing_matrix
    if "pre-drill admin readiness check" in text or "pre drill admin readiness check" in text:
        return StaffProductType.pre_drill_admin_readiness_check
    if "troop-flow checklist" in text or "troop flow checklist" in text:
        return StaffProductType.troop_flow_checklist
    if "formation/transition matrix" in text or "formation transition matrix" in text:
        return StaffProductType.formation_transition_matrix
    if "leader touchpoint plan" in text or "leader touchpoint checklist" in text:
        return StaffProductType.leader_touchpoint_plan
    if "decision support matrix" in text or "decision matrix" in text:
        return StaffProductType.decision_support_matrix
    if "due-out tracker" in text or "due out tracker" in text or "suspense tracker" in text:
        return StaffProductType.due_out_tracker
    if "collection matrix" in text or "pir/ir" in text or "pir ir" in text or "collection plan" in text:
        return StaffProductType.collection_matrix
    if "sustainment matrix" in text or "movement table" in text or "movement matrix" in text:
        if "movement table" in text:
            return StaffProductType.movement_table
        return StaffProductType.sustainment_matrix
    if "medical estimate" in text:
        return StaffProductType.medical_estimate
    if "casevac quick card" in text or "medevac quick card" in text or "casevac card" in text:
        return StaffProductType.casevac_quick_card
    if "religious support plan" in text:
        return StaffProductType.religious_support_plan
    if "rmt support matrix" in text or "religious ministry team support matrix" in text:
        return StaffProductType.rmt_support_matrix
    if "morale and welfare estimate" in text or "morale welfare estimate" in text:
        return StaffProductType.morale_welfare_estimate
    if (
        "road to war" in text
        or "road-to-war" in text
        or "levelset brief" in text
        or "scenario background brief" in text
    ):
        return StaffProductType.road_to_war_brief
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
        if "visitor control" in text or "visitor-control" in text:
            return StaffProductType.visitor_control_checklist
        if "traffic control plan" in text or "traffic and parking control plan" in text or "parking control" in text:
            return StaffProductType.traffic_parking_control_plan
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
