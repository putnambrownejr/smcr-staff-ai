from app.core.security import DEFAULT_WARNINGS
from app.schemas.poam import PoamLineItem, PoamRequest, PoamResponse


class PoamBuilder:
    def build(self, request: PoamRequest) -> PoamResponse:
        sections = request.staff_sections or ["S-1", "S-3", "S-4", "S-6"]
        line_items: list[PoamLineItem] = []
        for section in sections:
            for guidance in request.higher_guidance[:6]:
                line_items.append(
                    PoamLineItem(
                        workstream=_workstream_for_guidance(guidance, request.warfighting_functions),
                        owner=section,
                        task=f"{section}: {guidance}",
                        suspense_hint="Back-plan from execution date and command suspense.",
                        coordination=_coordination_for_section(section),
                    )
                )
        return PoamResponse(
            title=f"POA&M scaffold: {request.title}",
            summary_lines=[
                "Use this as a jump-start POA&M, not as a final command-approved tasking document.",
                (
                    f"Built from {len(request.higher_guidance)} higher-guidance input(s) "
                    f"across {len(sections)} section(s)."
                ),
            ],
            line_items=line_items[:24],
            review_points=[
                "Confirm every task has a real owner, suspense, and dependency.",
                "Review whether tasks should be grouped by staff section, warfighting function, or execution phase.",
                "Validate that no key section or support relationship is missing before distribution.",
                *[f"Assumption to validate: {item}" for item in request.assumptions],
            ],
            warnings=[
                *DEFAULT_WARNINGS,
                (
                    "POA&M scaffolding is advisory only and must be reviewed against "
                    "the actual order and command guidance."
                ),
            ],
        )


def _workstream_for_guidance(guidance: str, warfighting_functions: list[str]) -> str:
    lowered = guidance.lower()
    for function in warfighting_functions:
        if function.lower() in lowered:
            return function
    if "comm" in lowered or "signal" in lowered:
        return "command and control"
    if "log" in lowered or "supply" in lowered or "transport" in lowered:
        return "logistics"
    return warfighting_functions[0] if warfighting_functions else "staff integration"


def _coordination_for_section(section: str) -> list[str]:
    mapping = {
        "S-1": ["Commander/XO", "Admin chief", "Travel/DTS support as needed"],
        "S-3": ["XO", "Operations chief", "Training support"],
        "S-4": ["S-3", "Motor/logistics support", "Supply"],
        "S-6": ["S-3", "Comm support", "Information management"],
    }
    return mapping.get(section, ["XO", "Related staff sections"])
