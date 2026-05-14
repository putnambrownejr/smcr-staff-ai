from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import G9PlanningRequest, G9PlanningResponse


class G9Planner:
    def build(self, request: G9PlanningRequest) -> G9PlanningResponse:
        civil_situation_frame = [
            f"Supported problem: {request.supported_problem}",
            "Describe the civil or partner environment in broad, public, and non-sensitive terms.",
            "Separate known stakeholder facts from assumptions, impressions, or stale continuity notes.",
            "Keep this in the advisory planning lane; do not treat it as an authoritative engagement plan.",
        ]
        if request.audience:
            civil_situation_frame.append(f"Supported audience / formation: {request.audience}")
        civil_situation_frame.extend(
            f"Civil consideration to frame: {item}" for item in request.civil_considerations
        )

        partner_coordination = [
            "Identify which relationships require coordination before the event, during execution, "
            "and after follow-up.",
            "Separate military, civilian, interagency, host-community, and NGO touchpoints clearly.",
            "Clarify who owns each outreach or coordination task and what approval level is required.",
        ]
        partner_coordination.extend(f"Partner set to consider: {item}" for item in request.partner_types)

        information_requirements = [
            "What public context is still missing about the local area, stakeholders, or partner constraints?",
            "What information would most change the commander's decision or engagement posture?",
            "What continuity note should survive between drills so the same questions are not relearned next month?",
        ]

        engagement_considerations = [
            "Keep interactions lawful, professional, and consistent with command guidance.",
            "Prepare key leader engagement questions and a short note-taking structure before contact.",
            "Document assumptions, commitments made, and promised follow-up while details are still fresh.",
        ]
        engagement_considerations.extend(f"Constraint to manage: {item}" for item in request.constraints)

        continuity_and_transition = [
            "Store partner context, engagement notes, and next actions in a clean turnover format.",
            "Flag what must be revalidated next drill because reserve continuity is fragile.",
            "Separate enduring relationships from one-off event support tasks.",
            "Record follow-up owners before the team disperses.",
        ]

        return G9PlanningResponse(
            title=f"G-9 planning support: {request.title}",
            civil_situation_frame=civil_situation_frame,
            partner_coordination=partner_coordination,
            information_requirements=information_requirements,
            engagement_considerations=engagement_considerations,
            continuity_and_transition=continuity_and_transition,
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "G-9 planning support is advisory only and should be reconciled with current command guidance, "
                    "civil-affairs authorities, and approved coordination channels."
                ),
            ],
        )
