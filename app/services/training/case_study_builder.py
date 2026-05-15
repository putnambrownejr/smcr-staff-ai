from app.core.security import DEFAULT_WARNINGS
from app.schemas.staff import S2EstimateRequest
from app.schemas.training import TrainingCaseStudyRequest, TrainingCaseStudyResponse
from app.services.staff.s2_estimator import S2Estimator


class TrainingCaseStudyBuilder:
    def __init__(self) -> None:
        self._s2 = S2Estimator()

    def build(self, request: TrainingCaseStudyRequest) -> TrainingCaseStudyResponse:
        s2_estimate = self._build_s2(request)

        situation_frame = [
            f"Framing question: {request.framing_question}",
            f"Training objective: {request.training_objective}",
            "Treat the case study as a decision-support and training device, not as a current operational directive.",
            "Use current public-source context to sharpen judgment, but do not let news replace standards.",
        ]
        if request.audience:
            situation_frame.append(f"Audience: {request.audience}")
        situation_frame.extend(f"Current-event context: {item}" for item in request.current_event_context[:4])

        case_summary = [
            "Reduce the event or issue to the handful of facts that actually change commander or staff decisions.",
            "Separate what is observed, what is inferred, and what still needs verification.",
            "Push the audience to explain not just what happened, but what they would direct, cut, or re-sequence.",
        ]
        if request.constraints:
            case_summary.extend(f"Constraint to hold in the study: {item}" for item in request.constraints[:3])

        key_observations = [
            "What was the first real friction point, not the first thing people complained about?",
            "What command relationship, support assumption, or reporting gap made the problem harder?",
            "What did the unit or staff need to decide earlier than it actually did?",
            "What would a reserve unit miss here if it treated this like a generic checklist problem?",
        ]

        met_alignment = _met_alignment(request)

        conop_implications = [
            "Identify what part of the case should drive the parent concept "
            "and what should be left to subordinate refinement.",
            "Translate the lesson into task organization, support requirements, and reporting expectations.",
            "Turn the case into one concrete change to the FRAGO or initial CONOP "
            "instead of leaving it as general wisdom.",
        ]

        discussion_questions = [
            "What should the commander or OIC decide first, and why?",
            "What information would most change the plan if it proved wrong?",
            "What would S-3, S-4, and S-6 each say is the first thing to fix here?",
            "What part of this case is most transferable to the unit's next drill or field problem?",
        ]

        aar_focus = [
            "Capture observations by standard, task, friction point, and corrective action.",
            "Distinguish between a sustain worth preserving and an improvised workaround "
            "that should not become doctrine.",
            "Tie every improve item to an owner, suspense, and the next event where the fix gets checked.",
        ]

        citations = [item.get("title", "Public-source item") for item in request.source_items[:6]]
        if not citations:
            citations = [
                "MCDP 5 Planning",
                "MCO 1553.3C Unit Training Management",
                "Public-source case material supplied by user",
            ]

        return TrainingCaseStudyResponse(
            title=f"Training case study: {request.title}",
            situation_frame=situation_frame,
            case_summary=case_summary,
            key_observations=key_observations,
            s2_estimate=s2_estimate,
            met_alignment=met_alignment,
            conop_implications=conop_implications,
            discussion_questions=discussion_questions,
            aar_focus=aar_focus,
            citations=citations,
            warnings=[
                *DEFAULT_WARNINGS,
                "Case-study output is advisory training material and requires human review before formal use.",
            ],
        )

    def _build_s2(self, request: TrainingCaseStudyRequest) -> list[str]:
        if not request.source_items and not request.current_event_context:
            return []
        estimate = self._s2.build(
            S2EstimateRequest(
                title=request.title,
                question=request.framing_question,
                source_items=request.source_items,
                audience=request.audience,
                planning_only=request.training_only,
            )
        )
        return [
            *estimate.summary_assessment[:2],
            *estimate.assessed_claims[:2],
            *estimate.collection_gaps[:2],
        ]


def _met_alignment(request: TrainingCaseStudyRequest) -> list[str]:
    items = [f"MET alignment candidate: {task}" for task in request.met_tasks]
    items.extend(f"METL alignment candidate: {task}" for task in request.metl_focus)
    if not items:
        items.append("Manual review required: identify the MET/METL or standard the case is supposed to sharpen.")
    return items
