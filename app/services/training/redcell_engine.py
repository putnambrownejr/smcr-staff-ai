from __future__ import annotations

from dataclasses import dataclass

from app.schemas.training import ScenarioArchetype, ThreatActorStereotype


@dataclass(frozen=True)
class RedCellDesign:
    stereotypes: list[ThreatActorStereotype]
    questions: list[str]


def build_redcell_design(
    *,
    archetype: ScenarioArchetype,
    actor_name: str,
    place_name: str,
) -> RedCellDesign:
    stereotypes = _stereotypes_for(archetype, actor_name, place_name)
    questions = _questions_for(archetype, actor_name, place_name)
    return RedCellDesign(stereotypes=stereotypes, questions=questions)


def _stereotypes_for(
    archetype: ScenarioArchetype,
    actor_name: str,
    place_name: str,
) -> list[ThreatActorStereotype]:
    if archetype == ScenarioArchetype.littoral_hybrid:
        return [
            ThreatActorStereotype(
                label="Deniable access disruptor",
                summary=(
                    f"{actor_name} pressures ports, routes, and partner confidence while staying below "
                    "clean attribution."
                ),
                indicators=[
                    "Port delays with conflicting explanations",
                    "Repeated low-level probing",
                    "Partner hesitation",
                ],
                preferred_seams=["Reporting latency", "Access-control confusion", "Civilian maritime clutter"],
                likely_friendly_mistakes=[
                    "Treating every disruption as isolated logistics friction",
                    "Overreacting tactically before clarifying the information picture",
                ],
            ),
            ThreatActorStereotype(
                label="Narrative opportunist",
                summary="Turns small incidents into public doubt faster than the staff updates its own story.",
                indicators=["Rumor spikes", "Conflicting partner claims", "Premature media questions"],
                preferred_seams=["PAO lag", "Unclear release authority", "Weak source discipline"],
                likely_friendly_mistakes=[
                    "Talking before facts are stabilized",
                    "Letting ops and messaging drift apart",
                ],
            ),
        ]
    if archetype == ScenarioArchetype.urban_unrest:
        return [
            ThreatActorStereotype(
                label="Crowd-shielded agitator",
                summary="Uses crowds, chokepoints, and moral ambiguity to slow movement and tempt overreaction.",
                indicators=["Barricades at key junctions", "Spotter behavior", "Simultaneous crowd actions"],
                preferred_seams=["Rules ambiguity", "Provost/operations seams", "Narrow access routes"],
                likely_friendly_mistakes=[
                    "Confusing movement urgency for clarity of authority",
                    "Letting one crowd problem consume the whole command post",
                ],
            ),
            ThreatActorStereotype(
                label="Perception manipulator",
                summary="Wins if the force looks clumsy, delayed, or uncoordinated in public view.",
                indicators=["Selective filming", "Edited rumor chains", "Rapid accusation cycles"],
                preferred_seams=["Unrehearsed response lines", "Civil-affairs gaps", "Late command guidance"],
                likely_friendly_mistakes=[
                    "Treating public legitimacy as a side issue",
                    "Failing to separate confirmed facts from viral claims",
                ],
            ),
        ]
    if archetype == ScenarioArchetype.disaster_unrest:
        return [
            ThreatActorStereotype(
                label="Aid-capture opportunist",
                summary="Uses relief friction and scarcity to build local leverage and discredit formal authority.",
                indicators=["Rumors about withheld aid", "Crowding at distribution points", "Checkpoint intimidation"],
                preferred_seams=["Logistics bottlenecks", "Partner coordination gaps", "Slow reassessment loops"],
                likely_friendly_mistakes=[
                    "Assuming relief friction is apolitical",
                    "Protecting schedule over legitimacy and safety",
                ],
            ),
            ThreatActorStereotype(
                label="Chaos amplifier",
                summary="Does not need to dominate; it only needs to keep the response disorganized.",
                indicators=["Conflicting local reports", "Task saturation", "Repeated false alarms"],
                preferred_seams=["Medical and safety overload", "Support reprioritization", "Poorly owned branches"],
                likely_friendly_mistakes=[
                    "Trying to solve every problem at once",
                    "Waiting too long to narrow scope",
                ],
            ),
        ]
    if archetype == ScenarioArchetype.border_proxy:
        return [
            ThreatActorStereotype(
                label="Route scout network",
                summary="Maps habits, reporting gaps, and timing routines before committing to stronger disruption.",
                indicators=["Repeated route sightings", "False checkpoint reports", "Inconsistent local warnings"],
                preferred_seams=["Movement predictability", "Sparse comm checks", "Weak convoy branch plans"],
                likely_friendly_mistakes=[
                    "Repeating the same timing and route habits",
                    "Assuming route confidence exists because movement has started",
                ],
            ),
            ThreatActorStereotype(
                label="Proxy mobility disruptor",
                summary="Uses small delays and local intimidation to make the staff burn its margin early.",
                indicators=["Minor blockages", "Late partner actions", "Small but compounding delays"],
                preferred_seams=[
                    "S-4/S-6 coordination",
                    "Accountability checks",
                    "Driver-rest and sustainment assumptions",
                ],
                likely_friendly_mistakes=[
                    "Treating delay as inconvenience instead of decision pressure",
                    "Failing to re-sequence support after the first slip",
                ],
            ),
        ]
    return [
        ThreatActorStereotype(
            label="Probe-and-pause coercer",
            summary=f"{actor_name} tests seams, pauses when watched, then presses where the staff sounds most certain.",
            indicators=["Low-cost probing", "Rapid shift to a softer seam", "Short pauses after detection"],
            preferred_seams=["Assumption-heavy plans", "Single-point reporting", "Unrehearsed support dependencies"],
            likely_friendly_mistakes=[
                "Confusing quiet for control",
                "Believing polished brief language means the branch is real",
            ],
        ),
        ThreatActorStereotype(
            label="Legitimacy eroder",
            summary=(
                f"Uses incidents near {place_name} to make the force look slow, confused, "
                "or disconnected from local reality."
            ),
            indicators=["Rumor after small incidents", "Partner doubt", "Escalating public narrative pressure"],
            preferred_seams=["Civil considerations", "PAO delay", "Inconsistent command lines"],
            likely_friendly_mistakes=[
                "Ignoring narrative effects because the event is 'only training'",
                "Assuming civil reaction will stay background noise",
            ],
        ),
    ]


def _questions_for(archetype: ScenarioArchetype, actor_name: str, place_name: str) -> list[str]:
    base = [
        f"If {actor_name} were trying to make the staff look clumsy near {place_name}, what seam would it hit first?",
        "What part of the plan assumes the adversary will cooperate with our timeline?",
        "What small disruption would force the biggest command overreaction?",
        "What would a thinking enemy want us to misread as mere friction or bad luck?",
    ]
    if archetype == ScenarioArchetype.littoral_hybrid:
        base.extend(
            [
                "If access degrades, what does the adversary gain first: time, confusion, or public doubt?",
                "Are we rehearsing maritime-style ambiguity, or only rehearsing our own reports?",
            ]
        )
    elif archetype == ScenarioArchetype.urban_unrest:
        base.extend(
            [
                "What crowd or legitimacy problem could tempt an unhelpful use of force or authority?",
                "What does the adversary gain if we fixate on one street problem and stop thinking operationally?",
            ]
        )
    elif archetype == ScenarioArchetype.disaster_unrest:
        base.extend(
            [
                "What aid or casualty inject would force us to choose between speed and legitimacy?",
                "Where would an opportunist hide inside our disaster-response assumptions?",
            ]
        )
    elif archetype == ScenarioArchetype.border_proxy:
        base.extend(
            [
                "What route or checkpoint assumption would a proxy network test first?",
                "If reporting slips by one cycle, what movement decision becomes unsafe or unserious?",
            ]
        )
    return base
