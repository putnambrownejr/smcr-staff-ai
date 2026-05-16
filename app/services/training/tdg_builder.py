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
        if request.decision_time:
            context.append(f"Decision time available: {request.decision_time}")
        context.extend(f"Scenario input: {item}" for item in request.scenario_context)
        context.extend(f"Opposing factor: {item}" for item in request.opposing_factors)
        context.extend(f"Friendly-force reality: {item}" for item in request.friendly_forces)
        context.extend(f"Civil consideration: {item}" for item in request.civil_considerations)
        context.extend(f"Reserve friction: {item}" for item in request.reserve_friction)
        context.extend(f"Constraint to account for: {item}" for item in request.constraints)

        commander_problem = [
            "What is the command problem that actually requires a decision, not just more description?",
            (
                "What must the leader protect first: mission, force, timeline, public legitimacy, "
                "or follow-on freedom of action?"
            ),
            "What assumption would most damage the plan if it proves false during execution?",
        ]

        mettc_prompts = [
            "Mission: What must be accomplished, and what is the purpose?",
            "Enemy / opposing factors: What friction, uncertainty, or threat complicates the problem?",
            "Terrain / environment: What physical, information, or civil terrain matters most?",
            "Troops and support: What capabilities, shortfalls, and reserve-specific limitations exist?",
            "Time: What must be decided now versus later?",
            "Civil considerations: What local relationships, authorities, or public factors matter?",
        ]

        forced_decision = [
            "State your immediate decision in one sentence before you explain it.",
            "Name what you are deliberately not doing, and why that exclusion is worth the risk.",
            "Identify the single condition that would make you change your decision on the spot.",
        ]

        decision_points = [
            "What is your immediate decision and why?",
            "What risk are you accepting, and what risk are you avoiding?",
            "What is your branch or sequel if your first decision fails?",
            "What report, trigger, or observation tells you the original plan is no longer good enough?",
        ]

        no_regret_actions = [
            "Clarify the task, purpose, and end state before movement or execution expands the problem.",
            "Reduce confusion by naming the main effort, the fallback, and the critical report window early.",
            "Preserve one reserve-realistic branch plan that can survive time loss, friction, or support shortfall.",
        ]

        branch_sequel_prompts = [
            (
                "If the primary approach stalls, what branch keeps the mission moving without pretending "
                "the original plan still works?"
            ),
            "If the situation improves, what sequel exploits the gain without overextending the force?",
            "What support request, control measure, or decision point should already be queued before failure occurs?",
        ]

        failure_triggers = [
            "A key assumption fails and the leader keeps planning as if it still holds.",
            "Reporting degrades and the team delays a branch decision because nobody wants to call the change.",
            "Reserve friction consumes the timeline: late arrivals, stale access, or un-rehearsed handoffs.",
        ]

        red_team_points = [
            "What would an honest skeptic say is decorative in this plan rather than executable?",
            "Which assumption sounds harmless in the classroom but becomes the first real failure on drill weekend?",
            "What did the student protect too late, and what did they overvalue too early?",
        ]

        discussion_questions = [
            "What principle of warfighting or tactics best applies here?",
            "How would this decision change with more time, more support, or less support?",
            "What reserve-specific friction would make execution harder than the paper plan suggests?",
            "What should the leader cut first if the scenario compresses and the original plan becomes too ambitious?",
        ]

        aar_focus = [
            "Did the student identify the real command problem before building the plan?",
            "Did the student make a decision early enough to preserve freedom of action?",
            "Did the branch plan reflect reserve reality or only ideal conditions?",
            "What assumption, if carried into a real event, would most likely fail first?",
        ]

        instructor_notes = [
            "Keep the TDG short enough to fit a drill-period discussion and follow with a quick AAR.",
            (
                "Challenge students on assumptions, cuts, and timing, not just on whether their final "
                "answer sounded confident."
            ),
            "Force a decision before the discussion broadens; do not let the room hide behind endless setup questions.",
            "Use references and doctrine as framing aids, not as a script for a single correct answer.",
        ]
        if request.references:
            instructor_notes.append("Suggested references: " + ", ".join(request.references))
        if request.include_red_team:
            instructor_notes.append("Assign one participant to play the skeptic and attack assumptions early.")

        return TdgGenerationResponse(
            title=f"TDG / wargaming package: {request.title}",
            context=context,
            commander_problem=commander_problem,
            mettc_prompts=mettc_prompts,
            forced_decision=forced_decision,
            decision_points=decision_points,
            no_regret_actions=no_regret_actions,
            branch_sequel_prompts=branch_sequel_prompts,
            failure_triggers=failure_triggers,
            red_team_points=red_team_points if request.include_red_team else [],
            discussion_questions=discussion_questions,
            aar_focus=aar_focus,
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
