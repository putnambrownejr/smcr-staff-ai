from __future__ import annotations

import os
from typing import Any

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from pydantic import BaseModel, Field, ValidationError

from app.chatgpt_bridge.adapter import ChatGptBridgeAdapter


def _split_env_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _transport_security_settings() -> TransportSecuritySettings:
    allowed_hosts = _split_env_list(os.getenv("MCP_ALLOWED_HOSTS"))
    allowed_origins = _split_env_list(os.getenv("MCP_ALLOWED_ORIGINS"))
    if not allowed_hosts and not allowed_origins:
        return TransportSecuritySettings(enable_dns_rebinding_protection=False)
    return TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=allowed_hosts,
        allowed_origins=allowed_origins,
    )


def _tool_invocation_meta(in_progress: str, complete: str, *, read_only: bool) -> dict[str, Any]:
    return {
        "openai/toolInvocation/invoking": in_progress,
        "openai/toolInvocation/invoked": complete,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": read_only,
        },
    }


adapter = ChatGptBridgeAdapter(
    base_url=os.getenv("SMCR_STAFF_AI_BACKEND_URL", "http://127.0.0.1:8000"),
    local_api_key=os.getenv("SMCR_STAFF_AI_LOCAL_API_KEY"),
)

mcp = FastMCP(
    name="smcr-staff-ai",
    stateless_http=True,
    transport_security=_transport_security_settings(),
)


class StaffPackageToolInput(BaseModel):
    title: str = Field(..., description="Short package title.")
    event_type: str = Field(default="drill_weekend", description="Training or event type.")
    mission_or_training_goal: str = Field(..., description="What the event is meant to achieve.")
    audience: str | None = Field(default=None, description="Who the package is for.")
    timeframe: str | None = Field(default=None, description="When the event will occur.")
    constraints: list[str] = Field(default_factory=list, description="Main planning constraints.")
    coordinating_sections: list[str] = Field(default_factory=list, description="Staff sections or support lanes.")
    support_requirements: list[str] = Field(default_factory=list, description="Broad support needs.")
    partner_types: list[str] = Field(default_factory=list, description="External partners or role players.")
    civil_considerations: list[str] = Field(default_factory=list, description="Civil or population factors.")
    medical_risk_context: list[str] = Field(default_factory=list, description="Medical risk factors.")
    casualty_scenarios: list[str] = Field(default_factory=list, description="Training-safe casualty scenarios.")
    source_items: list[dict[str, str]] = Field(default_factory=list, description="Optional open-source context items.")
    intelligence_question: str | None = Field(default=None, description="Optional S-2 question.")
    c2_objective: str | None = Field(default=None, description="Optional comm/C2 objective.")
    support_objective: str | None = Field(default=None, description="Optional S-4 objective.")
    include_g9: bool | None = Field(default=None, description="Whether to force G-9 review.")
    product_types: list[str] = Field(default_factory=lambda: ["warno", "frago", "aar"])
    preferred_format: str | None = Field(default=None, description="Optional preferred output format.")
    training_only: bool = Field(default=True, description="Set true for training-only or fictional scenarios.")


class StaffProductToolInput(BaseModel):
    product_type: str = Field(..., description="Product type such as warno, frago, aar, or naval_letter.")
    topic: str = Field(..., description="Topic or purpose of the product.")
    audience: str | None = Field(default=None, description="Who the product is for.")
    echelon: str | None = Field(default=None, description="Command echelon.")
    preferred_format: str | None = Field(default=None, description="Formatting preference if applicable.")
    facts: list[str] = Field(default_factory=list, description="Known facts to incorporate.")
    constraints: list[str] = Field(default_factory=list, description="Known constraints to respect.")
    training_or_fictional: bool = Field(default=True, description="Whether the scenario is training-only.")
    include_review_checklist: bool = Field(default=True, description="Whether to include the review checklist.")


class AgentRunToolInput(BaseModel):
    agent_id: str = Field(..., description="Registered staff or specialty agent id.")
    input: str = Field(..., description="The actual user question or task for the agent.")
    context: dict[str, Any] = Field(default_factory=dict, description="Optional agent context.")


class ChiefBriefToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")
    include_personal_documents: bool = Field(default=True, description="Include local document summary.")
    include_drill_plans: bool = Field(default=True, description="Include stored drill plans.")
    maradmin_records: list[dict[str, Any]] = Field(default_factory=list, description="Optional MARADMIN inputs.")


class UserKeyToolInput(BaseModel):
    user_key: str = Field(..., description="Stable local user profile key.")


class AdminWorkflowToolInput(BaseModel):
    workflow_type: str = Field(..., description="Workflow type such as gtcc, dts_authorization, or award_package.")
    title: str = Field(..., description="Short workflow title.")
    facts: list[str] = Field(default_factory=list, description="Facts relevant to the workflow.")
    constraints: list[str] = Field(default_factory=list, description="Constraints that shape the workflow.")


TOOL_SPECS: list[types.Tool] = [
    types.Tool(
        name="build_staff_package",
        title="Build Staff Package",
        description=(
            "Use this when the user wants one reserve training or event problem turned into a full staff package "
            "with S-2, S-3, S-4, S-6, medical, staff review, XO vet, and recommended products."
        ),
        inputSchema=StaffPackageToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the staff package", "Staff package ready", read_only=False),
    ),
    types.Tool(
        name="draft_staff_product",
        title="Draft Staff Product",
        description=(
            "Use this when the user needs an advisory WARNO, FRAGO, AAR, naval letter, memorandum, or similar "
            "staff product scaffold."
        ),
        inputSchema=StaffProductToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Drafting the staff product", "Staff product draft ready", read_only=False),
    ),
    types.Tool(
        name="list_staff_agents",
        title="List Staff Agents",
        description="Use this when the user wants to see which staff and specialty agents are available.",
        inputSchema={"type": "object", "properties": {}, "additionalProperties": False},
        _meta=_tool_invocation_meta("Loading staff agents", "Staff agents listed", read_only=True),
    ),
    types.Tool(
        name="run_staff_agent",
        title="Run Staff Agent",
        description="Use this when the user wants targeted help from one specific staff or specialty agent.",
        inputSchema=AgentRunToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Running the staff agent", "Staff agent response ready", read_only=False),
    ),
    types.Tool(
        name="build_chief_brief",
        title="Build Chief Brief",
        description=(
            "Use this when the user wants a personal Chief of Staff/Aide triage brief "
            "based on their saved local context."
        ),
        inputSchema=ChiefBriefToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the Chief brief", "Chief brief ready", read_only=False),
    ),
    types.Tool(
        name="career_watch",
        title="Career Watch",
        description=(
            "Use this when the user wants PME, FitRep, document, and opportunity awareness "
            "for a saved profile."
        ),
        inputSchema=UserKeyToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Reviewing career watch", "Career watch ready", read_only=True),
    ),
    types.Tool(
        name="admin_readiness",
        title="Admin Readiness",
        description="Use this when the user wants S-1/Admin readiness status for a saved local profile.",
        inputSchema=UserKeyToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Reviewing admin readiness", "Admin readiness ready", read_only=True),
    ),
    types.Tool(
        name="build_admin_workflow",
        title="Build Admin Workflow",
        description=(
            "Use this when the user needs an S-1 style GTCC, DTS, orders, awards, or admin-package workflow checklist."
        ),
        inputSchema=AdminWorkflowToolInput.model_json_schema(),
        _meta=_tool_invocation_meta("Building the admin workflow", "Admin workflow ready", read_only=False),
    ),
]


@mcp._mcp_server.list_tools()
async def _list_tools() -> list[types.Tool]:
    return TOOL_SPECS


def _ok_result(message: str, payload: dict[str, Any]) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            structuredContent=payload,
            isError=False,
        )
    )


def _error_result(message: str) -> types.ServerResult:
    return types.ServerResult(
        types.CallToolResult(
            content=[types.TextContent(type="text", text=message)],
            isError=True,
        )
    )


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    name = req.params.name
    arguments = req.params.arguments or {}

    try:
        if name == "build_staff_package":
            payload = StaffPackageToolInput.model_validate(arguments)
            result = await adapter.build_staff_package(payload.model_dump())
            return _ok_result("Built the staff package.", result)

        if name == "draft_staff_product":
            payload = StaffProductToolInput.model_validate(arguments)
            result = await adapter.draft_staff_product(payload.model_dump())
            return _ok_result("Drafted the staff product.", result)

        if name == "list_staff_agents":
            result = await adapter.list_agents()
            return _ok_result("Listed the available staff agents.", result)

        if name == "run_staff_agent":
            payload = AgentRunToolInput.model_validate(arguments)
            result = await adapter.run_staff_agent(
                agent_id=payload.agent_id,
                payload={"input": payload.input, "context": payload.context},
            )
            return _ok_result(f"Ran the {payload.agent_id} agent.", result)

        if name == "build_chief_brief":
            payload = ChiefBriefToolInput.model_validate(arguments)
            result = await adapter.build_chief_brief(payload.model_dump())
            return _ok_result("Built the Chief brief.", result)

        if name == "career_watch":
            payload = UserKeyToolInput.model_validate(arguments)
            result = await adapter.get_career_watch(user_key=payload.user_key)
            return _ok_result("Built the career watch.", result)

        if name == "admin_readiness":
            payload = UserKeyToolInput.model_validate(arguments)
            result = await adapter.get_admin_readiness(user_key=payload.user_key)
            return _ok_result("Built the admin readiness summary.", result)

        if name == "build_admin_workflow":
            payload = AdminWorkflowToolInput.model_validate(arguments)
            result = await adapter.build_admin_workflow(payload.model_dump())
            return _ok_result("Built the admin workflow.", result)

        return _error_result(f"Unknown tool: {name}")
    except ValidationError as exc:
        return _error_result(f"Input validation error: {exc.errors()}")
    except Exception as exc:  # pragma: no cover - transport-facing guardrail
        return _error_result(f"Tool execution failed: {exc}")


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request

app = mcp.streamable_http_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("chatgpt_app.main:app", host="0.0.0.0", port=8001)
