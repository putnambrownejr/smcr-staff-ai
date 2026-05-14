from app.core.security import DEFAULT_WARNINGS
from app.schemas.tdg import TdgGenerationRequest, TdgGenerationResponse


class TdgBuilder:
    def build(self, request: TdgGenerationRequest) -> TdgGenerationResponse:
        context = [
            f"Theme: {request.theme}",
            f"Training objective: {request.training_objective}",
            "Frame the problem so the student must choose under uncertainty, limited time, and incomplete information.",
        ]
        if request.audience:
            context.append(f"Audience: {request.audience}")
        context.extend(f"Constraint to account for: {item}" for item in request.constraints)

        mettc_prompts = [
            "Mission: What must be accomplished, and what is the purpose?",
            "Enemy / opposing factors: What friction, uncertainty, or threat complicates the problem?",
            "Terrain / environment: What physical, information, or civil terrain matters most?",
            "Troops and support: What capabilities, shortfalls, and reserve-specific limitations exist?",
            "Time: What must be decided now versus later?",
            "Civil considerations: What local relationships, authorities, or public factors matter?",
        ]

        decision_points = [
            "What is your immediate decision and why?",
            "What risk are you accepting, and what risk are you avoiding?",
            "What is your branch or sequel if your first decision fails?",
        ]

        discussion_questions = [
            "What principle of warfighting or tactics best applies here?",
            "How would this decision change with more time, more support, or less support?",
            "What reserve-specific friction would make execution harder than the paper plan suggests?",
        ]

        instructor_notes = [
            "Keep the TDG short enough to fit a drill-period discussion and follow with a quick AAR.",
            "Challenge students on assumptions, not just on the final answer.",
            "Use references and doctrine as framing aids, not as a script for a single correct answer.",
        ]
        if request.references:
            instructor_notes.append("Suggested references: " + ", ".join(request.references))

        return TdgGenerationResponse(
            title=f"TDG scaffold: {request.title}",
            context=context,
            mettc_prompts=mettc_prompts,
            decision_points=decision_points,
            discussion_questions=discussion_questions,
            instructor_notes=instructor_notes,
            sketch_map_prompt=(
                "Create a simple sketch map showing key terrain, control measures, start state, and the decision point."
                if request.include_sketch_map_prompt
                else None
            ),
            warnings=[
                *DEFAULT_WARNINGS,
                "TDG output is advisory training material and should be reviewed by an instructor before use.",
            ],
        )
