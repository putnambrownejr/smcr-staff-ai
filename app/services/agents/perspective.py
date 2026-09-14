"""External-AI staff perspectives for any input, behind the approval preview.

The deterministic agents return doctrine templates. When the caller asks for
external inference (``agent_options.inference`` = ``"external"``, or ``"auto"``
with an LLM configured) and an agent's own run produced no scenario output,
this module re-runs the seat through the approved external path with the
seat's template as its *lens* and asks for an actual assessment of the input.

Every call still goes through ``_try_llm_populate`` -> ``generate_scenario_response``
so the preview / acknowledgement / digest rules from ADR-001 apply unchanged.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, create_model

from app.schemas.agents import AgentRunResponse, ScenarioOutputStatus
from app.schemas.scenario_handoff import RoundtableSynthesisOutput, StaffPerspectiveOutput
from app.services.agents.base import DRAFT_NOTICE, Agent, AgentContext

_PERSPECTIVE_MODELS: dict[str, type[BaseModel]] = {}


def inference_mode(context: AgentContext) -> str:
    options = context.extra.get("agent_options")
    raw: Any = options.get("inference") if isinstance(options, dict) else None
    if not raw:
        raw = context.extra.get("inference")
    return str(raw) if isinstance(raw, str) and raw else "local"


def wants_external_perspective(context: AgentContext) -> bool:
    mode = inference_mode(context)
    if mode == "external":
        return True
    if mode == "auto":
        from app.core.config import get_settings

        return bool(get_settings().llm_api_key)
    return False


def role_key_for(agent: Agent) -> str:
    target = getattr(agent, "_target", agent)
    archetype = getattr(target, "archetype", None)
    role = getattr(archetype, "role", None)
    if isinstance(role, str) and role:
        return role
    return target.metadata.id.replace("-", "_")


def perspective_model_for(role_key: str) -> type[BaseModel]:
    model = _PERSPECTIVE_MODELS.get(role_key)
    if model is None:
        model = create_model(
            f"Perspective_{role_key}",
            __base__=StaffPerspectiveOutput,
            role=(str, role_key),
        )
        _PERSPECTIVE_MODELS[role_key] = model
    return model


def _perspective_template(title: str, framework_text: str, prior_context: str) -> str:
    return (
        f"{title} — STAFF PERSPECTIVE\n\n"
        "You are this staff seat. Apply your lens to the user's input and give the commander your "
        "section's view of THIS input — not a description of your framework, and not generic advice.\n\n"
        "YOUR LENS (the framework this seat normally applies; use it, do not repeat it):\n"
        f"{framework_text}\n\n"
        "PRODUCE, in this order:\n"
        "1. SUMMARY — your bottom line in two to four sentences.\n"
        "2. KEY CONCERNS — the specific issues in this input your section must flag, each with why it matters.\n"
        "3. RECOMMENDATIONS — concrete actions with an owner and a time or trigger.\n"
        "4. PRODUCTS TO BUILD — the staff products your section owes for this, one line each on content.\n"
        "5. QUESTIONS FOR THE COMMANDER — what you need decided or answered before you can go further.\n"
        "6. RISKS — what breaks first if this is ignored.\n\n"
        "Rules: cite doctrine by publication number where you can; say 'confirm current status' for any "
        "policy, organization, or funding fact that may have changed; never invent unit-specific facts "
        "that are not in the input — name them as gaps instead; keep everything UNCLASSIFIED and advisory."
        f"{prior_context}"
    )


def _synthesis_template(prior_context: str) -> str:
    return (
        "Chief of Staff — ROUND TABLE SYNTHESIS\n\n"
        "The staff seats have each given their perspective on the user's input (see PRIOR STAFF "
        "ASSESSMENTS and the round-table digest). Integrate them for the commander. Do not repeat every "
        "seat; resolve them.\n\n"
        "PRODUCE, in this order:\n"
        "1. BOTTOM LINE — what the commander must understand, in three sentences or fewer.\n"
        "2. INTEGRATED ASSESSMENT — where the seats agree, where they disagree, and what the disagreement means.\n"
        "3. DECISIONS FOR THE COMMANDER — in priority order, each with the information needed and a deadline.\n"
        "4. TASKINGS BY SEAT — who owes what, by when.\n"
        "5. PRODUCTS TO PRODUCE — one consolidated list, de-duplicated across seats.\n"
        "6. OPEN QUESTIONS — the questions that must be answered before execution.\n"
        "7. RISKS — the assumption doing the most work and the seam most likely to fail.\n\n"
        "Rules: keep it UNCLASSIFIED and advisory; cite doctrine by publication number; flag anything that "
        "may be out of date with 'confirm current status'."
        f"{prior_context}"
    )


def apply_external_perspective(
    agent: Agent,
    response: AgentRunResponse,
    input_text: str,
    context: AgentContext,
    *,
    synthesis: bool = False,
) -> AgentRunResponse:
    """Upgrade a template-only answer to an external-AI perspective when the caller asked for one."""
    if response.scenario_output_status is not ScenarioOutputStatus.not_applicable:
        return response
    if not wants_external_perspective(context):
        return response

    from app.services.agents.staff_advisor_agent import (
        _LLM_FAILURE_NOTICE,
        _LLM_LOCAL_ONLY_NOTICE,
        _LLM_UNAVAILABLE_NOTICE,
        _prior_assessment_context,
        _try_llm_populate,
    )

    prior_context = _prior_assessment_context(context)
    if synthesis:
        template = _synthesis_template(prior_context)
        model: type[BaseModel] = RoundtableSynthesisOutput
        role_key = "cos_synthesis"
    else:
        role_key = role_key_for(agent)
        template = _perspective_template(agent.metadata.name, response.answer, prior_context)
        model = perspective_model_for(role_key)

    population = _try_llm_populate(
        template,
        input_text,
        agent.metadata.system_prompt or "",
        model,
        role_key,
        context,
    )
    if population.scenario_output is not None:
        answer = population.answer
        if DRAFT_NOTICE not in answer:
            answer = answer.rstrip() + "\n\n" + DRAFT_NOTICE
        return response.model_copy(
            update={
                "answer": answer,
                "scenario_output": population.scenario_output,
                "scenario_output_status": population.status,
                "warnings": [*response.warnings, *(population.warnings or [])],
            }
        )
    # External path declined or failed: keep the local template, say why.
    if population.status is ScenarioOutputStatus.invalid:
        suffix = _LLM_FAILURE_NOTICE
    elif _LLM_LOCAL_ONLY_NOTICE.strip() in population.answer:
        suffix = _LLM_LOCAL_ONLY_NOTICE
    else:
        suffix = _LLM_UNAVAILABLE_NOTICE
    return response.model_copy(
        update={
            "answer": response.answer.rstrip() + suffix,
            "scenario_output_status": population.status,
            "warnings": [*response.warnings, *(population.warnings or [])],
        }
    )
