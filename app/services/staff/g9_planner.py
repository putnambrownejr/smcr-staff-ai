import json

from app.core.security import DEFAULT_WARNINGS, detect_sensitive_input
from app.schemas.civil_network import (
    CivilEvidenceKind,
    CivilNetworkNode,
    CivilNetworkRelationship,
    CivilNetworkSnapshot,
)
from app.schemas.source_state import VerifiedSourceStatus
from app.schemas.staff import (
    G9CulturalContextItem,
    G9EvidenceAssessment,
    G9EvidenceKind,
    G9InfrastructureSystem,
    G9OperatingContext,
    G9PlanningRequest,
    G9PlanningResponse,
    G9SourceItem,
)

_DRAFT_FOOTER = "DRAFT — Verify all references against current official sources before acting."


class G9Planner:
    def build(self, request: G9PlanningRequest) -> G9PlanningResponse:
        boundary_warnings = detect_sensitive_input(_request_text(request))
        if boundary_warnings:
            return _safe_response(boundary_warnings)

        civil_situation_frame = [
            f"Supported problem: {request.supported_problem}",
            "Describe the civil or partner environment in broad, public, and non-sensitive terms.",
            "Separate known stakeholder facts from assumptions, impressions, or stale continuity notes.",
            "Keep this in the advisory planning lane; do not treat it as an authoritative engagement plan.",
        ]
        if request.audience:
            civil_situation_frame.append(f"Supported audience / formation: {request.audience}")
        civil_situation_frame.extend(f"Civil consideration to frame: {item}" for item in request.civil_considerations)

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
        if request.operating_context is None:
            information_requirements.append(
                "Confirm the operating context (domestic support or overseas/partner exercise) before tailoring coordination."
            )

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
        civil_network_assessment, network_evidence, network_warnings = _civil_network_assessment(
            request.civil_network_snapshot
        )
        civil_situation_frame.extend(_civil_situation_projection(request.civil_network_snapshot))
        partner_coordination.extend(_partner_coordination_projection(request.civil_network_snapshot))
        engagement_considerations.extend(_engagement_projection(request.civil_network_snapshot))

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
                *network_warnings,
                _DRAFT_FOOTER,
            ],
            operating_context_frame=_operating_context_frame(request.operating_context),
            infrastructure_dependency_assessment=_infrastructure_assessment(request.infrastructure_systems),
            cultural_context_assessment=_cultural_context_assessment(request.cultural_context_items),
            evidence_and_assumptions=[*_evidence_assessments(request.source_items), *network_evidence],
            civil_estimate_outline=_civil_estimate_outline(),
            civil_network_assessment=civil_network_assessment,
        )


def _request_text(request: G9PlanningRequest) -> str:
    return json.dumps(request.model_dump(mode="json"), sort_keys=True)


def _safe_response(boundary_warnings: list[str]) -> G9PlanningResponse:
    generic_guidance = (
        "Sensitive details were withheld. Use only generic, training-safe civil-military planning "
        "questions and route specific details through approved channels."
    )
    return G9PlanningResponse(
        title="G-9 planning support: Sensitive request withheld",
        civil_situation_frame=[generic_guidance],
        partner_coordination=[
            "Confirm approved coordination channels without recording sensitive partner or operational details."
        ],
        information_requirements=[
            "Restate the planning need with fictional or non-sensitive context before identifying information gaps."
        ],
        engagement_considerations=[
            "Use lawful, professional, command-approved engagement procedures and avoid sensitive details."
        ],
        continuity_and_transition=["Keep only non-sensitive, approved continuity notes for the next planning session."],
        warnings=[*DEFAULT_WARNINGS, *boundary_warnings, _DRAFT_FOOTER],
        operating_context_frame=[
            "Confirm the operating context through approved channels using non-sensitive information only."
        ],
        infrastructure_dependency_assessment=[
            "Use a generic review of essential civil systems; do not record sensitive vulnerabilities or locations."
        ],
        cultural_context_assessment=["Use public, sourced context and avoid profiling or unsupported generalizations."],
        evidence_and_assumptions=[],
        civil_estimate_outline=[
            "Use a generic civil-estimate outline after the request is restated with non-sensitive context."
        ],
        civil_network_assessment=[],
    )


def _civil_network_assessment(
    snapshot: CivilNetworkSnapshot | None,
) -> tuple[list[str], list[G9EvidenceAssessment], list[str]]:
    if snapshot is None:
        return ([], [], [])
    assessment = [f"Civil-network snapshot (read-only): {snapshot.label} for event {snapshot.network.event_id}."]
    evidence_assessments: list[G9EvidenceAssessment] = []
    warnings: list[str] = []
    for node in snapshot.network.nodes:
        _append_network_record_assessment(node, node.display_name, assessment, evidence_assessments, warnings)
    for relationship in snapshot.network.relationships:
        _append_network_record_assessment(
            relationship, relationship.description, assessment, evidence_assessments, warnings
        )
    return (assessment, evidence_assessments, warnings)


def _append_network_record_assessment(
    record: CivilNetworkNode | CivilNetworkRelationship,
    label: str,
    assessment: list[str],
    evidence_assessments: list[G9EvidenceAssessment],
    warnings: list[str],
) -> None:
    kind = _network_evidence_kind(record.evidence_kind)
    assessment.append(f"{_network_label(record.evidence_kind)}: {label}")
    if not record.evidence:
        assessment.append(f"Evidence gap: {label} has no cited evidence.")
    for item in record.evidence:
        evidence_assessments.append(
            G9EvidenceAssessment(
                kind=kind,
                statement=label,
                source_label=item.title,
                source_date=item.retrieved_at.isoformat(),
                confidence=item.confidence.value,
                verification_note=(
                    f"Provenance retained: {item.url or item.bibliographic_note or 'citation note missing'}; "
                    f"trust status={item.trust_status.value}."
                ),
            )
        )
        if item.trust_status is not VerifiedSourceStatus.current:
            warnings.append(
                f"Civil-network source '{item.title}' is {item.trust_status.value}; confirm before relying on it."
            )


def _network_evidence_kind(kind: CivilEvidenceKind) -> G9EvidenceKind:
    if kind is CivilEvidenceKind.sourced_observation:
        return G9EvidenceKind.reported_fact
    if kind is CivilEvidenceKind.analytic_inference:
        return G9EvidenceKind.analytic_inference
    return G9EvidenceKind.planning_assumption


def _network_label(kind: CivilEvidenceKind) -> str:
    return {
        CivilEvidenceKind.sourced_observation: "Sourced observation",
        CivilEvidenceKind.analytic_inference: "Analytic inference",
        CivilEvidenceKind.planning_hypothesis: "Planning hypothesis",
    }[kind]


def _civil_situation_projection(snapshot: CivilNetworkSnapshot | None) -> list[str]:
    if snapshot is None:
        return []
    return [
        f"Civil-network {node.kind.value}: {node.display_name} ({_network_label(node.evidence_kind).lower()})."
        for node in snapshot.network.nodes
        if node.kind.value in {"organization", "service", "forum", "broad_group"}
    ]


def _partner_coordination_projection(snapshot: CivilNetworkSnapshot | None) -> list[str]:
    if snapshot is None:
        return []
    return [
        f"Read-only civil-network relationship: {edge.kind.value} — {edge.description} "
        f"({_network_label(edge.evidence_kind).lower()})."
        for edge in snapshot.network.relationships
        if edge.kind.value
        in {"coordination", "dependency", "authority_approval", "resource_support", "information_flow"}
    ]


def _engagement_projection(snapshot: CivilNetworkSnapshot | None) -> list[str]:
    if snapshot is None:
        return []
    return [
        f"Role-bound public engagement consideration: {node.public_role}, {node.organization}; "
        f"event relevance: {node.event_relevance}. Preserve cited role context and confirm currency before contact."
        for node in snapshot.network.nodes
        if node.kind.value == "public_role_holder"
    ]


def _operating_context_frame(context: G9OperatingContext | None) -> list[str]:
    if context is G9OperatingContext.domestic_support:
        return [
            "Domestic-support frame: identify the appropriate civilian lead and emergency-management coordination channels.",
            "Confirm applicable authorities, approvals, and command guidance with the appropriate officials; this worksheet makes no authority determination.",
        ]
    if context is G9OperatingContext.overseas_partner:
        return [
            "Overseas/partner frame: coordinate through appropriate host-nation and embassy channels.",
            "Respect partner and NGO independence; confirm applicable agreements, releasability, and command guidance through approved channels.",
            "This worksheet does not determine agreement status or authorities.",
        ]
    return [
        "Generic civil-military frame: confirm whether this is domestic support or an overseas/partner exercise before tailoring the package.",
        "Use only broad, public, non-sensitive civil context until the operating context is confirmed.",
    ]


def _infrastructure_assessment(systems: list[G9InfrastructureSystem]) -> list[str]:
    if not systems:
        categories = "water, power, transport, communications, health, fuel, shelter, and waste"
        return [
            f"Review broad public context for essential civil systems: {categories}.",
            "Research gap: identify which system categories are relevant to the event and confirm civil coordination questions through approved channels.",
        ]

    assessment: list[str] = []
    for item in systems:
        details = [f"Infrastructure system: {item.system}."]
        if item.condition_or_concern:
            details.append(f"Submitted concern: {item.condition_or_concern}.")
        if item.known_dependency:
            details.append(f"Submitted dependency: {item.known_dependency}.")
        if item.source_label:
            details.append(f"Source label to verify: {item.source_label}.")
        details.append(f"Civil-effect question: What broad civil effect should be validated for {item.system}?")
        details.append("Coordination question: Which approved civil coordination channel should confirm this context?")
        assessment.append(" ".join(details))
    return assessment


def _cultural_context_assessment(items: list[G9CulturalContextItem]) -> list[str]:
    if not items:
        return [
            "Documented-context prompt: identify public, sourced context relevant to the event.",
            "Variation prompt: identify regional or situational variation; do not generalize group behavior.",
            "Engagement-relevance prompt: identify how documented context may inform respectful coordination.",
            "Assumptions-to-avoid prompt: record unverified generalizations and questions requiring confirmation.",
        ]

    assessment: list[str] = []
    for item in items:
        details = [f"Documented context to verify: {item.documented_context}."]
        if item.source_label:
            details.append(f"Source label: {item.source_label}.")
        if item.regional_variation:
            details.append(f"Stated variation: {item.regional_variation}.")
        else:
            details.append("Variation question: confirm relevant regional or situational variation.")
        if item.planning_relevance:
            details.append(f"Stated engagement relevance: {item.planning_relevance}.")
        else:
            details.append("Engagement relevance question: confirm how this context informs respectful coordination.")
        details.append("Avoid predicting group behavior; treat unverified statements as planning assumptions.")
        assessment.append(" ".join(details))
    return assessment


def _evidence_assessments(items: list[G9SourceItem]) -> list[G9EvidenceAssessment]:
    assessments: list[G9EvidenceAssessment] = []
    for item in items:
        source_label = item.publisher or item.title
        if item.claim and item.source_type and item.corroborated:
            assessments.append(
                G9EvidenceAssessment(
                    kind=G9EvidenceKind.reported_fact,
                    statement=item.claim,
                    source_label=source_label,
                    source_date=item.retrieved_at,
                    confidence="moderate",
                    verification_note="Reported public-source claim; verify currency and applicability before acting.",
                )
            )
        elif item.claim:
            assessments.append(
                G9EvidenceAssessment(
                    kind=G9EvidenceKind.planning_assumption,
                    statement=item.claim,
                    source_label=source_label,
                    source_date=item.retrieved_at,
                    confidence="low",
                    verification_note=(
                        "Validation needed: classify as reported fact only after a source type and corroboration are supplied."
                    ),
                )
            )
        else:
            assessments.append(
                G9EvidenceAssessment(
                    kind=G9EvidenceKind.planning_assumption,
                    statement=f"Evidence gap: review source item '{item.title}' and record a relevant claim if supported.",
                    source_label=source_label,
                    source_date=item.retrieved_at,
                    confidence="low",
                    verification_note="Title-only source item is an evidence gap, not a factual assertion; verify before use.",
                )
            )
    return assessments


def _civil_estimate_outline() -> list[str]:
    return [
        "Event/context",
        "Civil situation/actors",
        "Infrastructure/civil effects",
        "Cultural context/variation",
        "Authorities/coordination",
        "Judgments/assumptions/requirements",
        "Recommended actions/decision points",
        "Sources/confidence/verification",
    ]
