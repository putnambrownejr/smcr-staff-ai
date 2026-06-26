from app.schemas.agents import AgentMetadata, AgentRunResponse, Confidence
from app.services.agents.base import Agent, AgentContext
from app.services.agents.source_refs import (
    STAFF_PROCESS_REFERENCES,
    TRAINING_REFERENCES,
    citation_titles,
    source_trust_markers,
    structured_citations,
)


class AssessmentLearningAgent(Agent):
    def __init__(self) -> None:
        self.metadata = AgentMetadata(
            id="assessment-learning-advisor",
            name="Assessment / Learning Advisor",
            description=(
                "Connects METs, METLs, measures, AARs, and next-drill corrections so staff learning survives beyond "
                "the event itself."
            ),
            domain="assessment and learning",
            intended_users=["SMCR officers", "S-3", "XO", "training teams"],
            allowed_sources=[
                "public Marine Corps planning doctrine",
                "public training management references",
                "local training-only AAR and event context",
            ],
            disallowed_inputs=[
                "private personnel performance counseling beyond minimum need",
                "classified operational details",
            ],
            system_prompt=(
                "Respond like a Marine staff officer under a demanding S-3 who cares whether the unit actually "
                "learned anything. Tie observations to standards, measures, and follow-through instead of letting "
                "AARs become venting.\n\n"
                "Training management framework (MCO 1553.3C):\n"
                "- Training is commander's business. The S-3 manages, not owns.\n"
                "- Annual training plan → quarterly training guidance → monthly schedule → "
                "weekly training schedule → daily training schedule.\n"
                "- Reserve cycle: plan AT 90 days out, confirm T&R events 60 days, "
                "publish drill schedule 30 days, finalize logistics 15 days.\n\n"
                "T&R manual structure:\n"
                "- MET (Mission Essential Task): a collective task a unit must perform to accomplish "
                "its mission. Each MET has associated standards and conditions.\n"
                "- METL (Mission Essential Task List): the commander's prioritized list of METs.\n"
                "- Core METs: universal tasks every unit must perform (e.g., employ fires, "
                "conduct tactical movement, perform combat marksmanship).\n"
                "- Mission METs: tasks specific to the unit's assigned mission.\n"
                "- Individual T&R events: coded by MOS and skill level "
                "(e.g., 0300-TRNG-1001 = basic infantry task, skill level 1).\n"
                "- Collective T&R events: coded by unit type "
                "(e.g., INF-MN-6001 = infantry platoon defensive operations).\n"
                "- Evaluation codes: T (trained), P (partially trained), U (untrained).\n"
                "- For reserve units, T&R events must be executable in 2-day or 4-day drill blocks.\n\n"
                "AAR structure (doctrinal):\n"
                "- Step 1: Review what was supposed to happen (intent, scheme of maneuver, T&R event).\n"
                "- Step 2: Establish what actually happened (timeline, key decisions, friction).\n"
                "- Step 3: Determine why (root cause, not symptoms).\n"
                "- Step 4: Determine how to improve (specific, owned, time-bound actions).\n"
                "- Format: formal (scheduled, full unit), informal (on-the-spot, small unit).\n"
                "- Reserve AAR discipline: capture must survive the drill weekend — assign owners and "
                "suspense dates before Marines depart. If it is not written down with an owner, "
                "it does not exist at the next drill.\n\n"
                "Training evaluation criteria:\n"
                "- Did the unit execute the T&R event to standard?\n"
                "- Were conditions realistic (MOPP, night, degraded comms)?\n"
                "- Did the evaluation measure performance, not just attendance?\n"
                "- Was the evaluator qualified (T&R specifies evaluator requirements)?\n"
                "- Was the result recorded in MCTIMS/DRRS-MC?\n\n"
                "DRRS-MC reporting:\n"
                "- Defense Readiness Reporting System – Marine Corps tracks unit readiness.\n"
                "- Training readiness (T-rating) is one of four pillars (personnel, equipment, supply, training).\n"
                "- T-rating drives the unit's overall C-rating. Reserve units report monthly.\n"
                "- The S-3 owns the training readiness assessment; the CO signs."
            ),
        )

    def run(self, input_text: str, context: AgentContext) -> AgentRunResponse:
        answer = (
            "Assessment / learning advisory.\n\n"
            "Use this to connect the event to the next event — training that does not change "
            "future execution was a waste of drill time.\n\n"
            "Assessment frame:\n"
            "- What MET/METL lane or T&R event was supposed to improve?\n"
            "- What evaluation code applies: T (trained), P (partially trained), U (untrained)?\n"
            "- What evidence shows improvement, not just completion?\n"
            "- Which observation is about execution, and which is about event design?\n"
            "- What must change before the next drill to avoid relearning the same lesson?\n\n"
            "AAR structure (use this format):\n"
            "1. What was supposed to happen — state the T&R event, intent, and standard.\n"
            "2. What actually happened — timeline, key decisions, friction points.\n"
            "3. Why — root cause analysis, not symptom listing.\n"
            "4. How to improve — specific actions, named owners, suspense dates.\n\n"
            "Good AAR discipline:\n"
            "- Distinguish sustains from lucky recovery.\n"
            "- Name where the standard held and where it broke.\n"
            "- Assign corrective actions with owners and suspense dates.\n"
            "- Tie fixes to the next rehearsal, next drill, or next event.\n"
            "- Preserve only the handful of lessons that change future execution.\n"
            "- Reserve rule: if it is not written down with an owner before Marines depart, "
            "it does not exist at the next drill.\n\n"
            "Training readiness reporting:\n"
            "- T-rating feeds DRRS-MC C-rating. S-3 owns the assessment, CO signs.\n"
            "- Track: events executed vs planned, evaluation results, T&R event completion %.\n"
            "- Reserve-specific: did the event fit a 2-day or 4-day drill block? "
            "If not, was the scope appropriate or did we try to cram too much?\n\n"
            "Do not tolerate:\n"
            "- complaint language without a fix\n"
            "- observations that are really just preferences\n"
            "- lessons that nobody owns by the time drill ends\n"
            "- events counted as 'trained' without a real evaluation\n\n"
            "Measures to pressure:\n"
            "- T&R event completion rate vs annual training plan\n"
            "- evaluation quality (was it to standard, or just attendance?)\n"
            "- report timeliness and decision quality\n"
            "- corrective action closure rate (drill-over-drill)\n"
            "- comm reliability and accountability discipline\n"
            "- commander decision support quality\n"
        )
        refs = TRAINING_REFERENCES + STAFF_PROCESS_REFERENCES
        return self._response(
            answer=answer,
            input_text=input_text,
            citations=citation_titles(refs),
            structured_citations=structured_citations(refs),
            source_trust=source_trust_markers(
                refs,
                notes_prefix=(
                    "Verify current training-management and staff-process references before formal assessment."
                ),
            ),
            confidence=Confidence.medium,
            follow_up_questions=[
                "What standard or MET/METL lane was this event supposed to improve?",
                "What observation actually changes the next drill?",
                "Who owns the corrective action before the next event?",
            ],
        )


def build_assessment_learning_agent() -> AssessmentLearningAgent:
    return AssessmentLearningAgent()
