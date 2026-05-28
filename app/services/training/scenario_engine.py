from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.schemas.training import (
    ScenarioActorProfile,
    ScenarioArchetype,
    ScenarioInjectCard,
    ScenarioInjectTag,
    ScenarioNarrativeBeat,
    ThreatActorStereotype,
)
from app.services.training.redcell_engine import build_redcell_design


@dataclass(frozen=True)
class ScenarioDesign:
    archetype: ScenarioArchetype
    inject_tags_used: list[ScenarioInjectTag]
    setting: list[str]
    frame: list[str]
    actors: list[ScenarioActorProfile]
    stereotypes: list[ThreatActorStereotype]
    escalation: list[str]
    beats: list[ScenarioNarrativeBeat]
    injects: list[ScenarioInjectCard]
    facilitator_notes: list[str]
    redcell_questions: list[str]


def build_s3_scenario_design(
    *,
    title: str,
    mission_or_training_goal: str,
    event_type: str,
    audience: str | None,
    scenario_archetype: ScenarioArchetype | None,
    inject_tags: list[ScenarioInjectTag],
    primary_scenario_input: str | None,
    secondary_scenario_input: str | None,
    current_event_context: list[str],
    source_items: list[dict[str, str]],
    coordinating_sections: list[str],
    constraints: list[str],
) -> ScenarioDesign:
    seed = _seed_text(title, mission_or_training_goal, event_type, primary_scenario_input, secondary_scenario_input)
    archetype = _scenario_archetype(
        scenario_archetype=scenario_archetype,
        mission_or_training_goal=mission_or_training_goal,
        event_type=event_type,
        primary_scenario_input=primary_scenario_input,
        secondary_scenario_input=secondary_scenario_input,
        current_event_context=current_event_context,
        constraints=constraints,
    )
    place_name = _fictional_place(seed)
    country_name = _fictional_country(seed)
    actor = _fictional_actor(seed, archetype, place_name)
    redcell_design = build_redcell_design(
        archetype=archetype,
        actor_name=actor.name,
        place_name=place_name,
    )
    setting = _setting_lines(
        archetype=archetype,
        country_name=country_name,
        place_name=place_name,
        mission_or_training_goal=mission_or_training_goal,
        audience=audience,
        current_event_context=current_event_context,
        source_items=source_items,
    )
    frame = _frame_lines(
        archetype=archetype,
        country_name=country_name,
        place_name=place_name,
        primary_scenario_input=primary_scenario_input,
        secondary_scenario_input=secondary_scenario_input,
        source_items=source_items,
    )
    beats = _narrative_beats(
        archetype=archetype,
        actor=actor,
        place_name=place_name,
        primary_scenario_input=primary_scenario_input,
        secondary_scenario_input=secondary_scenario_input,
    )
    escalation = [f"{beat.phase} - {beat.summary}" for beat in beats]
    injects = _inject_cards(
        archetype=archetype,
        actor=actor,
        place_name=place_name,
        coordinating_sections=coordinating_sections,
        constraints=constraints,
        inject_tags=inject_tags,
        primary_scenario_input=primary_scenario_input,
        secondary_scenario_input=secondary_scenario_input,
    )
    facilitator_notes = _facilitator_notes(archetype, actor.name, coordinating_sections)
    return ScenarioDesign(
        archetype=archetype,
        inject_tags_used=list(dict.fromkeys(inject_tags)),
        setting=setting,
        frame=frame,
        actors=[actor],
        stereotypes=redcell_design.stereotypes,
        escalation=escalation,
        beats=beats,
        injects=injects,
        facilitator_notes=facilitator_notes,
        redcell_questions=redcell_design.questions,
    )


def _seed_text(*parts: str | None) -> str:
    return "|".join(part or "" for part in parts)


def _stable_index(seed: str, modulo: int) -> int:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % modulo


def _fictional_country(seed: str) -> str:
    prefixes = ["Vel", "Kor", "Mar", "Cal", "Tor", "Ser", "Dra", "Bel", "Nor", "Isk"]
    suffixes = ["ara", "ovia", "estan", "oria", "enne", "ara", "yat", "inor", "ec", "undi"]
    return prefixes[_stable_index(seed + "country-a", len(prefixes))] + suffixes[
        _stable_index(seed + "country-b", len(suffixes))
    ]


def _fictional_place(seed: str) -> str:
    prefixes = ["Port", "New", "San", "Camp", "Lake", "Fort", "Cape", "North", "South", "Old"]
    roots = ["Aster", "Coral", "Morrow", "Trident", "Harbor", "Vantage", "Kestrel", "River", "Beacon", "Sable"]
    prefix = prefixes[_stable_index(seed + "place-a", len(prefixes))]
    root = roots[_stable_index(seed + "place-b", len(roots))]
    return f"{prefix} {root}"


def _scenario_archetype(
    *,
    scenario_archetype: ScenarioArchetype | None,
    mission_or_training_goal: str,
    event_type: str,
    primary_scenario_input: str | None,
    secondary_scenario_input: str | None,
    current_event_context: list[str],
    constraints: list[str],
) -> ScenarioArchetype:
    if scenario_archetype is not None:
        return scenario_archetype
    text = " ".join(
        [
            mission_or_training_goal,
            event_type,
            primary_scenario_input or "",
            secondary_scenario_input or "",
            *current_event_context,
            *constraints,
        ]
    ).lower()
    if any(term in text for term in {"littoral", "maritime", "coast", "port", "meu", "shipping"}):
        return ScenarioArchetype.littoral_hybrid
    if any(term in text for term in {"flood", "storm", "earthquake", "disaster", "evacuation", "humanitarian"}):
        return ScenarioArchetype.disaster_unrest
    if any(term in text for term in {"urban", "city", "metro", "riot", "civil unrest", "megacity"}):
        return ScenarioArchetype.urban_unrest
    if any(term in text for term in {"border", "crossing", "smuggling", "riverine", "cartel"}):
        return ScenarioArchetype.border_proxy
    return ScenarioArchetype.expeditionary_coercion


def _fictional_actor(seed: str, archetype: ScenarioArchetype, place_name: str) -> ScenarioActorProfile:
    if archetype == ScenarioArchetype.littoral_hybrid:
        name = _group_name(seed, "Maritime", "Restoration", place_name)
        return ScenarioActorProfile(
            name=name,
            role="Hybrid coastal proxy network",
            disposition="Coercive, deniable, and politically opportunistic",
            objectives=[
                "Disrupt access and partner confidence without triggering a clean conventional response",
                "Create public confusion and delay command decisions",
            ],
            capabilities=["Small boat harassment", "Commercial-drone observation", "Proxy agitators", "Info ops"],
            signature_tactics=["Port disruption", "Rumor campaigns", "Harassment of local security forces"],
        )
    if archetype == ScenarioArchetype.disaster_unrest:
        name = _group_name(seed, "People's", "Relief", place_name)
        return ScenarioActorProfile(
            name=name,
            role="Opportunistic armed political front",
            disposition="Exploits disaster response gaps to build local influence",
            objectives=[
                "Control relief access points and shape the local narrative",
                "Discredit partner governance and outside support",
            ],
            capabilities=["Crowd mobilization", "Checkpoint intimidation", "Localized sabotage", "Social media rumor"],
            signature_tactics=["Aid-diversion claims", "False security warnings", "Crowd pressure at key sites"],
        )
    if archetype == ScenarioArchetype.urban_unrest:
        name = _group_name(seed, "Civic", "Liberation", place_name)
        return ScenarioActorProfile(
            name=name,
            role="Urban militant movement with political cover",
            disposition="Escalatory and media-aware",
            objectives=[
                "Trigger overreaction by security elements",
                "Turn local disruptions into legitimacy wins",
            ],
            capabilities=["Barricades", "Spotter networks", "Selective sabotage", "Narrative manipulation"],
            signature_tactics=["Simultaneous protests", "Road obstructions", "Targeted misinformation"],
        )
    if archetype == ScenarioArchetype.border_proxy:
        name = _group_name(seed, "Frontier", "Defense", place_name)
        return ScenarioActorProfile(
            name=name,
            role="Proxy smuggling-security militia",
            disposition="Adaptive, transactional, and familiar with local terrain",
            objectives=[
                "Preserve illicit movement corridors",
                "Test response seams between local authorities and external support",
            ],
            capabilities=["Route scouts", "Cross-border caches", "Lookouts", "Vehicle ambush potential"],
            signature_tactics=["False reports", "Route feints", "Pressure on isolated checkpoints"],
        )
    name = _group_name(seed, "National", "Resistance", place_name)
    return ScenarioActorProfile(
        name=name,
        role="Revisionist local armed movement",
        disposition="Probing, disciplined enough to exploit seams, but not conventionally dominant",
        objectives=[
            "Undermine partner control over key terrain and the information environment",
            "Create enough instability to slow outside decision-making",
        ],
        capabilities=["Reconnaissance-by-observation", "Small-unit harassment", "Narrative shaping", "Proxy support"],
        signature_tactics=["Test patrols", "Localized disruption", "Manipulation of civilian perception"],
    )


def _group_name(seed: str, first: str, second: str, place_name: str) -> str:
    suffixes = ["Movement", "Front", "Brigade", "Network", "Collective", "Alliance"]
    suffix = suffixes[_stable_index(seed + "group-suffix", len(suffixes))]
    short_place = place_name.split()[-1]
    return f"{first} {short_place} {second} {suffix}"


def _setting_lines(
    *,
    archetype: ScenarioArchetype,
    country_name: str,
    place_name: str,
    mission_or_training_goal: str,
    audience: str | None,
    current_event_context: list[str],
    source_items: list[dict[str, str]],
) -> list[str]:
    base = [
        (
            f"Scenario setting: the fictional state of {country_name} and the {place_name} corridor are used to "
            "mirror real-world instability patterns without copying a live conflict directly."
        ),
        f"Training purpose anchor: {mission_or_training_goal}",
        "Use real-world conflict logic, infrastructure friction, and civil complexity, but keep all names fictional.",
    ]
    if archetype == ScenarioArchetype.littoral_hybrid:
        base.append(
            "Operational backdrop: contested littoral access, partner-force fragility, and deniable maritime coercion."
        )
    elif archetype == ScenarioArchetype.disaster_unrest:
        base.append(
            "Operational backdrop: disaster response strain, governance gaps, "
            "and armed opportunists competing for control."
        )
    elif archetype == ScenarioArchetype.urban_unrest:
        base.append(
            "Operational backdrop: dense urban terrain, information distortion, and civil unrest with armed edges."
        )
    elif archetype == ScenarioArchetype.border_proxy:
        base.append(
            "Operational backdrop: cross-border movement, route insecurity, and proxy actors exploiting local seams."
        )
    else:
        base.append(
            "Operational backdrop: ambiguous coercion, partner dependence, "
            "and a problem set bigger than a one-lane response."
        )
    if audience:
        base.append(f"Primary training audience: {audience}")
    if current_event_context:
        base.append(f"Real-world grounding cue: {current_event_context[0]}")
    if source_items:
        base.append(f"Public-source grounding cue: {source_items[0].get('title', 'Source item')}")
    return base


def _frame_lines(
    *,
    archetype: ScenarioArchetype,
    country_name: str,
    place_name: str,
    primary_scenario_input: str | None,
    secondary_scenario_input: str | None,
    source_items: list[dict[str, str]],
) -> list[str]:
    frame = [
        "Build a scenario that pressures command relationships, reporting, and standards instead of only adding noise.",
        (
            f"Baseline fiction: authorities in {country_name} are struggling to stabilize the {place_name} area "
            "while a hostile network probes for seams."
        ),
    ]
    if primary_scenario_input:
        frame.append(f"Primary scenario driver: {primary_scenario_input}")
    if secondary_scenario_input:
        frame.append(f"Secondary complication to turn it up: {secondary_scenario_input}")
    if source_items:
        frame.append(f"Public-source grounding: {source_items[0].get('title', 'Source item')}")
    frame.append(
        "Keep the scenario nested with the training standard: every inject should force a decision, "
        "report, branch, or cross-staff handoff."
    )
    if archetype == ScenarioArchetype.urban_unrest:
        frame.append("Urban crowd behavior, access control, and public narrative should matter as much as movement.")
    return frame


def _narrative_beats(
    *,
    archetype: ScenarioArchetype,
    actor: ScenarioActorProfile,
    place_name: str,
    primary_scenario_input: str | None,
    secondary_scenario_input: str | None,
) -> list[ScenarioNarrativeBeat]:
    opening_summary = primary_scenario_input or (
        f"Routine operations around {place_name} are disrupted by signs that {actor.name} is testing local control."
    )
    complication_summary = secondary_scenario_input or (
        f"{actor.name} escalates pressure through a second disruption that stresses timing, support, and reporting."
    )
    beats = [
        ScenarioNarrativeBeat(
            phase="Phase I - Baseline",
            summary=opening_summary,
            command_problem="Frame the real problem early and decide what matters first before the staff overbuilds.",
        ),
        ScenarioNarrativeBeat(
            phase="Phase II - Friction",
            summary=complication_summary,
            command_problem="Re-prioritize under friction instead of trying to save every original assumption.",
        ),
        ScenarioNarrativeBeat(
            phase="Phase III - Escalation",
            summary=f"{actor.name} creates overlapping pressure on access, reporting, and local legitimacy.",
            command_problem="Choose what to protect first and what to cut before coordination debt compounds.",
        ),
        ScenarioNarrativeBeat(
            phase="Phase IV - Convergence",
            summary="Subordinate elements report, adapt, and push a final recommendation to the parent unit.",
            command_problem="Produce a clear recommendation, branch, or transition decision before time expires.",
        ),
    ]
    if archetype == ScenarioArchetype.disaster_unrest:
        beats[2] = ScenarioNarrativeBeat(
            phase="Phase III - Escalation",
            summary=f"{actor.name} exploits relief friction and crowd pressure around {place_name}.",
            command_problem="Decide how to preserve legitimacy, movement, and safety without losing the timeline.",
        )
    return beats


def _inject_cards(
    *,
    archetype: ScenarioArchetype,
    actor: ScenarioActorProfile,
    place_name: str,
    coordinating_sections: list[str],
    constraints: list[str],
    inject_tags: list[ScenarioInjectTag],
    primary_scenario_input: str | None,
    secondary_scenario_input: str | None,
) -> list[ScenarioInjectCard]:
    sections = coordinating_sections or ["S-1", "S-4", "S-6", "Safety / ORM"]
    injects = [
        ScenarioInjectCard(
            phase="Phase I - Baseline",
            title="Initial scenario lift",
            trigger="Opening brief complete",
            inject=(
                primary_scenario_input
                or (
                    f"Initial reports from {place_name} suggest {actor.name} is shaping local conditions "
                    "below open conflict."
                )
            ),
            training_purpose="Force the first commander problem statement, initial report, and support assumptions.",
            expected_actions=[
                "Publish initial assessment and priority information gaps",
                "State who reports what first and by when",
            ],
            primary_sections=["S-3", "S-2", "XO"],
        ),
        ScenarioInjectCard(
            phase="Phase II - Friction",
            title="Support seam exposed",
            trigger="After first staff sync",
            inject=(
                secondary_scenario_input
                or (
                    f"A movement or sustainment assumption fails as traffic, access, or supply friction "
                    f"builds around {place_name}."
                )
            ),
            training_purpose="Force a branch decision and cross-staff coordination under time pressure.",
            expected_actions=[
                "Update support estimate and identify the event-canceling shortfall",
                "Recommend what to cut, delay, or protect first",
            ],
            primary_sections=["S-3", "S-4", "XO"],
        ),
    ]
    if any("6" in section.lower() or "comm" in section.lower() for section in sections):
        injects.append(
            ScenarioInjectCard(
                phase="Phase II - Friction",
                title="Reporting degradation",
                trigger="When the unit settles on its first plan",
                inject="Primary reporting path degrades and one subordinate element misses the expected window.",
                training_purpose="Test PACE discipline and whether the plan survives comm friction.",
                expected_actions=[
                    "Shift to the next PACE layer",
                    "Reconfirm guard, report windows, and accountability triggers",
                ],
                primary_sections=["S-6", "S-3", "SEL"],
            )
        )
    if any("4" in section.lower() or "log" in section.lower() for section in sections):
        injects.append(
            ScenarioInjectCard(
                phase="Phase III - Escalation",
                title="Mobility choke point",
                trigger="As the branch plan begins",
                inject=f"Access to the {place_name} objective narrows and vehicle flow becomes the pacing problem.",
                training_purpose="Force movement-table thinking, route discipline, and sustainment reprioritization.",
                expected_actions=[
                    "Re-sequence movement and support flow",
                    "Report revised arrival or sustainment implications to the command group",
                ],
                primary_sections=["S-4", "S-3", "Provost"],
            )
        )
    if any("medical" in section.lower() or "surgeon" in section.lower() for section in sections):
        injects.append(
            ScenarioInjectCard(
                phase="Phase III - Escalation",
                title="Training casualty complication",
                trigger="At the point of peak timeline compression",
                inject=(
                    "A simulated casualty occurs while the staff is already juggling delayed reporting "
                    "and support drift."
                ),
                training_purpose="Test CASEVAC logic, stop-training triggers, and command focus under compression.",
                expected_actions=[
                    "Execute the CASEVAC / MEDEVAC decision path",
                    "Reassess whether the event should pause, narrow, or continue",
                ],
                primary_sections=["Medical", "Safety", "S-3"],
            )
        )
    if any("g-9" in section.lower() or "civil" in section.lower() for section in sections):
        injects.append(
            ScenarioInjectCard(
                phase="Phase III - Escalation",
                title="Civil friction spike",
                trigger="As control measures tighten",
                inject=(
                    f"A local rumor tied to {actor.name} spreads that outside forces are restricting aid "
                    f"or movement near {place_name}."
                ),
                training_purpose=(
                    "Force civil considerations, messaging discipline, and legitimacy awareness into the plan."
                ),
                expected_actions=[
                    "Clarify the civil impact and partner implications",
                    "Recommend commander messaging and coordination adjustments",
                ],
                primary_sections=["G-9", "PAO / COMMSTRAT", "S-3"],
            )
        )
    if constraints:
        injects.append(
            ScenarioInjectCard(
                phase="Phase IV - Convergence",
                title="Constraint squeeze",
                trigger="Final recommendation window",
                inject=f"The scenario closes under a real planning constraint: {constraints[0]}",
                training_purpose=(
                    "Make the final recommendation reflect actual reserve limits instead of ideal execution."
                ),
                expected_actions=[
                    "Push the final recommendation in plain language",
                    "Name what will be carried to the next drill or cut now",
                ],
                primary_sections=["XO", "S-3", "Chief"],
            )
        )
    return _apply_tagged_injects(injects, inject_tags, actor.name, place_name)


def _apply_tagged_injects(
    injects: list[ScenarioInjectCard],
    inject_tags: list[ScenarioInjectTag],
    actor_name: str,
    place_name: str,
) -> list[ScenarioInjectCard]:
    tagged = list(injects)
    for tag in dict.fromkeys(inject_tags):
        if tag == ScenarioInjectTag.comms_degraded:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase II - Tagged Friction",
                    title="Comms blackout window",
                    trigger="Controller-directed on the main effort's first update",
                    inject="Primary and alternate reporting paths fail for one reporting cycle.",
                    training_purpose="Force PACE discipline and missed-report decision logic.",
                    expected_actions=["Shift to contingency communications", "Reconfirm report windows and guard"],
                    primary_sections=["S-6", "S-3", "XO"],
                )
            )
        elif tag == ScenarioInjectTag.casualty:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase III - Tagged Escalation",
                    title="Casualty inject",
                    trigger="When tempo and workload are already high",
                    inject="A simulated casualty changes the commander's timeline and force-protection math.",
                    training_purpose="Force medical reporting, CASEVAC logic, and command reprioritization.",
                    expected_actions=["Run the casualty report", "Recommend pause, continue, or narrow scope"],
                    primary_sections=["Medical", "Safety", "S-3"],
                )
            )
        elif tag == ScenarioInjectTag.logistics_failure:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase II - Tagged Friction",
                    title="Support collapse",
                    trigger="Immediately after the first concept is published",
                    inject="Fuel, transport, or key sustainment support becomes unavailable without warning.",
                    training_purpose="Force sustainment realism and branch planning.",
                    expected_actions=["Identify the event-canceling shortfall", "Recommend a supportable branch"],
                    primary_sections=["S-4", "XO", "S-3"],
                )
            )
        elif tag == ScenarioInjectTag.disinformation:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase III - Tagged Escalation",
                    title="Disinformation burst",
                    trigger="Once the staff thinks the picture is stable",
                    inject=(
                        f"False reporting tied to {actor_name} spreads quickly and changes how local "
                        "actors read the situation."
                    ),
                    training_purpose="Force source skepticism, public-narrative control, and decision discipline.",
                    expected_actions=[
                        "Separate confirmed facts from rumor",
                        "Update commander lines and public posture",
                    ],
                    primary_sections=["S-2", "PAO / COMMSTRAT", "S-3"],
                )
            )
        elif tag == ScenarioInjectTag.civil_unrest:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase III - Tagged Escalation",
                    title="Civil unrest spike",
                    trigger="As control measures begin to tighten",
                    inject=(
                        f"Demonstrators gather near {place_name} and complicate access, legitimacy, "
                        "and force posture."
                    ),
                    training_purpose="Force civil considerations and escalation control into the plan.",
                    expected_actions=[
                        "Assess civil impact",
                        "Recommend force posture and messaging adjustments",
                    ],
                    primary_sections=["G-9", "S-3", "Provost"],
                )
            )
        elif tag == ScenarioInjectTag.partner_force_failure:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase II - Tagged Friction",
                    title="Partner collapse",
                    trigger="After the unit has built reliance on partner support",
                    inject=(
                        "A partner-force element misses its task, reports late, or acts outside the "
                        "expected scheme."
                    ),
                    training_purpose="Force assumptions-checking and support reallocation.",
                    expected_actions=[
                        "Reassign support responsibilities",
                        "Reframe the command problem quickly",
                    ],
                    primary_sections=["S-3", "XO", "S-4"],
                )
            )
        elif tag == ScenarioInjectTag.legal_gray_zone:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase III - Tagged Escalation",
                    title="Legal ambiguity",
                    trigger="As the staff proposes a stronger response",
                    inject="A proposed action touches detention, search, evidence handling, or authority boundaries.",
                    training_purpose="Force legal review timing and boundary awareness.",
                    expected_actions=[
                        "Flag the legal review trigger",
                        "Reframe the option inside training-safe limits",
                    ],
                    primary_sections=["SJA", "Provost", "S-3"],
                )
            )
        elif tag == ScenarioInjectTag.media_pressure:
            tagged.append(
                ScenarioInjectCard(
                    phase="Phase III - Tagged Escalation",
                    title="Media pressure",
                    trigger="Once the scenario turns public-facing",
                    inject=(
                        f"A local outlet and online voices begin asking why forces are operating around {place_name}."
                    ),
                    training_purpose="Force command messaging, release control, and narrative discipline.",
                    expected_actions=["Draft response lines", "Confirm release authority and what not to say"],
                    primary_sections=["PAO / COMMSTRAT", "XO", "S-3"],
                )
            )
    return tagged


def _facilitator_notes(
    archetype: ScenarioArchetype, actor_name: str, coordinating_sections: list[str]
) -> list[str]:
    notes = [
        "Run the scenario like a thinking enemy and a messy environment, not like a scripted slideshow.",
        f"Use {actor_name} as the fictional adversary name, but keep the conflict logic recognizable and grounded.",
        "Every inject should force a decision, a report, or a cross-staff handoff within the training objective.",
        "If the audience solves the problem too quickly, tighten timing, degrade one support assumption, "
        "or complicate the information picture.",
    ]
    if archetype in {ScenarioArchetype.littoral_hybrid, ScenarioArchetype.expeditionary_coercion}:
        notes.append("Keep access, legitimacy, and reporting friction as important as kinetic-seeming activity.")
    if any("medical" in section.lower() or "safety" in section.lower() for section in coordinating_sections):
        notes.append("Do not let casualty or safety injects become decoration; they should change command behavior.")
    return notes
