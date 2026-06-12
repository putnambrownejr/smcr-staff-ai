from __future__ import annotations

from dataclasses import dataclass

from app.schemas.training import (
    S3PlanningRequest,
    ScenarioArchetype,
    ScenarioInjectTag,
    ScenarioPresetListResponse,
    ScenarioPresetRecord,
    TrainingScenarioRequest,
)


@dataclass(frozen=True)
class ScenarioPreset:
    preset_id: str
    name: str
    scenario_archetype: ScenarioArchetype
    inject_tags: tuple[ScenarioInjectTag, ...]
    summary: str
    recommended_for: tuple[str, ...]
    primary_scenario_input: str
    secondary_scenario_input: str
    current_event_context: tuple[str, ...]
    coordinating_sections: tuple[str, ...]
    constraints: tuple[str, ...]

    def to_record(self) -> ScenarioPresetRecord:
        return ScenarioPresetRecord(
            preset_id=self.preset_id,
            name=self.name,
            scenario_archetype=self.scenario_archetype,
            inject_tags=list(self.inject_tags),
            summary=self.summary,
            recommended_for=list(self.recommended_for),
            primary_scenario_input=self.primary_scenario_input,
            secondary_scenario_input=self.secondary_scenario_input,
            current_event_context=list(self.current_event_context),
            coordinating_sections=list(self.coordinating_sections),
            constraints=list(self.constraints),
        )


class ScenarioPresetCatalog:
    def __init__(self, presets: list[ScenarioPreset]) -> None:
        self._by_id = {preset.preset_id: preset for preset in presets}

    @classmethod
    def default(cls) -> ScenarioPresetCatalog:
        return cls(
            [
                ScenarioPreset(
                    preset_id="baltic-littoral-coercion",
                    name="Baltic Littoral Coercion",
                    scenario_archetype=ScenarioArchetype.littoral_hybrid,
                    inject_tags=(
                        ScenarioInjectTag.comms_degraded,
                        ScenarioInjectTag.media_pressure,
                        ScenarioInjectTag.partner_force_failure,
                    ),
                    summary="Coastal coercion, partner fragility, degraded reporting, and public pressure.",
                    recommended_for=("MEU rehearsal", "MAGTF planning drill", "command-post exercise"),
                    primary_scenario_input=(
                        "A partner force requests support as a fictional coastal corridor faces deniable disruption."
                    ),
                    secondary_scenario_input=(
                        "Port access degrades while false reports and delayed partner actions "
                        "pressure command decisions."
                    ),
                    current_event_context=(
                        "Use real-world-style northern littoral tension without copying a live conflict directly.",
                    ),
                    coordinating_sections=("S-3", "S-2", "S-4", "S-6", "PAO / COMMSTRAT"),
                    constraints=("Limited time to clarify the operating picture",),
                ),
                ScenarioPreset(
                    preset_id="urban-unrest-partner-fragility",
                    name="Urban Unrest With Partner Fragility",
                    scenario_archetype=ScenarioArchetype.urban_unrest,
                    inject_tags=(
                        ScenarioInjectTag.civil_unrest,
                        ScenarioInjectTag.disinformation,
                        ScenarioInjectTag.legal_gray_zone,
                    ),
                    summary=(
                        "Dense urban friction, information distortion, legitimacy pressure, "
                        "and gray-zone decisions."
                    ),
                    recommended_for=("CA exercise", "staff drill", "tabletop exercise"),
                    primary_scenario_input=(
                        "A fictional city's protests and roadblocks complicate movement, "
                        "reporting, and partner legitimacy."
                    ),
                    secondary_scenario_input=(
                        "Conflicting reports, legal ambiguity, and narrative pressure force the unit to narrow scope."
                    ),
                    current_event_context=(
                        "Mirror familiar unrest dynamics and media compression without reproducing a current event.",
                    ),
                    coordinating_sections=("S-3", "G-9", "SJA", "Provost", "PAO / COMMSTRAT"),
                    constraints=("Public legitimacy matters as much as movement control",),
                ),
                ScenarioPreset(
                    preset_id="hadr-armed-opportunists",
                    name="HA/DR Plus Armed Opportunists",
                    scenario_archetype=ScenarioArchetype.disaster_unrest,
                    inject_tags=(
                        ScenarioInjectTag.casualty,
                        ScenarioInjectTag.logistics_failure,
                        ScenarioInjectTag.civil_unrest,
                    ),
                    summary=(
                        "Disaster response strain, aid friction, opportunistic armed actors, "
                        "and casualty pressure."
                    ),
                    recommended_for=("HA/DR rehearsal", "AT planning drill", "civil-support lane"),
                    primary_scenario_input=(
                        "Severe storm damage in a fictional coastal district disrupts movement, "
                        "accountability, and relief flow."
                    ),
                    secondary_scenario_input=(
                        "Armed opportunists exploit aid congestion and partner confusion while a "
                        "casualty complicates tempo."
                    ),
                    current_event_context=(
                        "Ground the problem in familiar disaster-response patterns and reserve support limits.",
                    ),
                    coordinating_sections=("S-3", "S-4", "Medical", "Safety / ORM", "G-9"),
                    constraints=("Support capacity and leader attention are both limited",),
                ),
                ScenarioPreset(
                    preset_id="border-proxy-mobility-problem",
                    name="Border Proxy Mobility Problem",
                    scenario_archetype=ScenarioArchetype.border_proxy,
                    inject_tags=(
                        ScenarioInjectTag.logistics_failure,
                        ScenarioInjectTag.comms_degraded,
                        ScenarioInjectTag.partner_force_failure,
                    ),
                    summary="Route insecurity, proxy activity, reporting degradation, and mobility friction.",
                    recommended_for=("mobility rehearsal", "convoy TDG", "distributed field exercise"),
                    primary_scenario_input=(
                        "A fictional border corridor sees smuggling-linked proxy pressure that "
                        "disrupts route confidence."
                    ),
                    secondary_scenario_input=(
                        "A partner checkpoint fails to report on time while route access narrows and support slips."
                    ),
                    current_event_context=(
                        "Use real-world-style cross-border friction without reproducing any current operation.",
                    ),
                    coordinating_sections=("S-3", "S-4", "S-6", "Provost", "Medical"),
                    constraints=("Vehicle flow and accountability are pacing functions",),
                ),
            ]
        )

    def list(self) -> ScenarioPresetListResponse:
        records = [preset.to_record() for preset in self._by_id.values()]
        return ScenarioPresetListResponse(total_presets=len(records), records=records)

    def apply_to_training_request(self, request: TrainingScenarioRequest) -> TrainingScenarioRequest:
        preset = self._require(request.scenario_preset_id)
        return request.model_copy(
            update={
                # Optional scalars: None means "not provided", use preset
                "scenario_archetype": (
                    request.scenario_archetype
                    if request.scenario_archetype is not None
                    else preset.scenario_archetype
                ),
                "primary_scenario_input": (
                    request.primary_scenario_input
                    if request.primary_scenario_input is not None
                    else preset.primary_scenario_input
                ),
                "secondary_scenario_input": (
                    request.secondary_scenario_input
                    if request.secondary_scenario_input is not None
                    else preset.secondary_scenario_input
                ),
                # Lists default to [] when not provided; empty means "use preset"
                "inject_tags": request.inject_tags or list(preset.inject_tags),
                "current_event_context": request.current_event_context or list(preset.current_event_context),
                "coordinating_sections": request.coordinating_sections or list(preset.coordinating_sections),
                "constraints": request.constraints or list(preset.constraints),
            }
        )

    def apply_to_s3_request(self, request: S3PlanningRequest) -> S3PlanningRequest:
        preset = self._require(request.scenario_preset_id)
        return request.model_copy(
            update={
                # Optional scalars: None means "not provided", use preset
                "scenario_archetype": (
                    request.scenario_archetype
                    if request.scenario_archetype is not None
                    else preset.scenario_archetype
                ),
                "primary_scenario_input": (
                    request.primary_scenario_input
                    if request.primary_scenario_input is not None
                    else preset.primary_scenario_input
                ),
                "secondary_scenario_input": (
                    request.secondary_scenario_input
                    if request.secondary_scenario_input is not None
                    else preset.secondary_scenario_input
                ),
                # Lists default to [] when not provided; empty means "use preset"
                "inject_tags": request.inject_tags or list(preset.inject_tags),
                "current_event_context": request.current_event_context or list(preset.current_event_context),
                "coordinating_sections": request.coordinating_sections or list(preset.coordinating_sections),
                "constraints": request.constraints or list(preset.constraints),
            }
        )

    def _require(self, preset_id: str | None) -> ScenarioPreset:
        if not preset_id or preset_id not in self._by_id:
            raise KeyError(preset_id or "")
        return self._by_id[preset_id]
