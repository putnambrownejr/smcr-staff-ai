from datetime import UTC, date, datetime

from fastapi import APIRouter, HTTPException

from app.schemas.agents import AgentRunRequest, AgentRunResponse
from app.schemas.analysis import TextAnalysisRequest, TextAnalysisResponse
from app.schemas.actions import ActionCategory, ActionHistoryEntry, ActionPriority, ActionRecord, ActionStatus
from app.schemas.career import CareerWatchResponse
from app.schemas.chatgpt_surface import ChatGptToolSurfaceEntry, ChatGptToolSurfaceResponse
from app.schemas.chief import ChiefBriefResponse
from app.schemas.planning import StaffPlanningPackageRequest, StaffPlanningPackageResponse
from app.schemas.session import DrillDateRecord, FitrepReminder, PmeStatus, RecurringCheck, UserSessionHandoff
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductDraftResponse
from app.services.agents.base import AgentContext
from app.services.agents.registry import agent_registry
from app.services.analysis.summarizer import TextAnalysisService
from app.services.demo.scenarios import DEMO_USER_KEY, build_demo_career_watch, build_demo_chief_brief
from app.services.planning.orchestrator import StaffPlanningOrchestrator
from app.services.staff_products.builder import StaffProductBuilder

router = APIRouter(prefix="/demo", tags=["demo"])
_analysis_service = TextAnalysisService()
_staff_product_builder = StaffProductBuilder()
_planning_orchestrator = StaffPlanningOrchestrator()


@router.get("/status", summary="Show repo-mode demo capabilities")
def demo_status() -> dict[str, object]:
    return {
        "mode": "stateless_demo",
        "user_key": DEMO_USER_KEY,
        "notes": [
            "Demo routes do not depend on user-local storage or prior setup.",
            "They exist to make the repository easier to understand from GitHub and OpenAPI alone.",
            "Private/local workflows still require the non-demo routes and local context storage.",
        ],
        "routes": [
            "/demo/status",
            "/demo/chief/brief",
            "/demo/career/watch",
            "/demo/actions",
            "/demo/handoffs/{user_key}",
            "/demo/planning/staff-package",
            "/demo/analysis/summarize",
            "/demo/staff-products/draft",
            "/demo/agents/{agent_id}/run",
        ],
    }


@router.get(
    "/tool-catalog",
    response_model=ChatGptToolSurfaceResponse,
    summary="Show the recommended ChatGPT-facing tool surface",
)
def demo_tool_catalog() -> ChatGptToolSurfaceResponse:
    return ChatGptToolSurfaceResponse(
        archetype="tool-only",
        mode="stateless_demo_first",
        tool_entries=[
            ChatGptToolSurfaceEntry(
                name="chief_brief_demo",
                route="/demo/chief/brief",
                method="GET",
                purpose="Return a stateless Chief of Staff / Aide de Camp triage brief.",
                use_when=(
                    "Use this when the user wants a high-level digest of drill, admin, docs, "
                    "and career priorities."
                ),
                notes=["Read-only", "Best first surface for dashboard-style summaries"],
            ),
            ChatGptToolSurfaceEntry(
                name="career_watch_demo",
                route="/demo/career/watch",
                method="GET",
                purpose="Return a stateless career-maintenance view.",
                use_when="Use this when the user wants PME, FitRep, opportunity, or self-development nudges.",
                notes=["Read-only", "Career-centric companion to the Chief brief"],
            ),
            ChatGptToolSurfaceEntry(
                name="summarize_text_demo",
                route="/demo/analysis/summarize",
                method="POST",
                purpose="Turn pasted text into summary points, due-outs, checklist items, and follow-up questions.",
                use_when="Use this when the user pastes notes, emails, orders, or working text and wants structure.",
                notes=["Read-only", "Does not store submitted text"],
            ),
            ChatGptToolSurfaceEntry(
                name="actions_demo",
                route="/demo/actions",
                method="GET",
                purpose="Return stateless example action items with owner, suspense, priority, status, and history.",
                use_when="Use this when the user wants to understand the local action tracker shape.",
                notes=["Read-only", "No local action records are created"],
            ),
            ChatGptToolSurfaceEntry(
                name="handoff_demo",
                route="/demo/handoffs/{user_key}",
                method="GET",
                purpose="Return a stateless example session handoff.",
                use_when="Use this when the user wants to understand what continuity context can look like.",
                notes=["Read-only", "Does not read local handoff storage"],
            ),
            ChatGptToolSurfaceEntry(
                name="staff_package_demo",
                route="/demo/planning/staff-package",
                method="GET",
                purpose="Return a stateless cross-staff planning package example.",
                use_when="Use this when the user wants a broad planning-package shape without local setup.",
                notes=["Read-only", "Training-only sample"],
            ),
            ChatGptToolSurfaceEntry(
                name="draft_staff_product_demo",
                route="/demo/staff-products/draft",
                method="POST",
                purpose="Draft an advisory OPORD, WARNO, FRAGO, SITREP, AAR, memo, or letter scaffold.",
                use_when="Use this when the user needs a staff-product starting point or review checklist.",
                notes=["Read-only", "Training-only and human-review guardrails apply"],
            ),
            ChatGptToolSurfaceEntry(
                name="run_staff_agent_demo",
                route="/demo/agents/{agent_id}/run",
                method="POST",
                purpose="Run a stateless agent such as CommO, OSINT, leadership, MARADMIN, or Chief/Aide.",
                use_when=(
                    "Use this when the user wants targeted advisory help from one specific "
                    "staff role or specialty."
                ),
                notes=["Read-only", "Maps cleanly to a future MCP tool layer"],
            ),
        ],
        future_private_tools=[
            "chief_brief_personal",
            "career_watch_personal",
            "handoff_draft_update",
            "handoff_apply_update",
            "personal_document_organizer",
            "opportunity_tracker_personal",
        ],
        warnings=[
            (
                "This catalog is the recommended first-pass ChatGPT tool surface, "
                "not a full exposure of private/local workflows."
            ),
            (
                "Private user data, local context, and mutating routes should stay behind "
                "explicit runtime boundaries until an auth model is in place."
            ),
        ],
    )


@router.get("/chief/brief", response_model=ChiefBriefResponse, summary="Get a stateless demo Chief/Aide brief")
def demo_chief_brief() -> ChiefBriefResponse:
    return build_demo_chief_brief()


@router.get("/career/watch", response_model=CareerWatchResponse, summary="Get a stateless demo career watch")
def demo_career_watch() -> CareerWatchResponse:
    return build_demo_career_watch()


@router.get("/actions", response_model=list[ActionRecord], summary="Get stateless demo action records")
def demo_actions() -> list[ActionRecord]:
    return [
        ActionRecord(
            action_id="demo-action-dts-voucher",
            user_key=DEMO_USER_KEY,
            title="Close post-drill DTS voucher",
            description="Collect receipts, confirm authorization status, and route the voucher before the suspense.",
            owner="Capt Demo Smith",
            category=ActionCategory.travel,
            priority=ActionPriority.high,
            status=ActionStatus.in_progress,
            suspense_date=date(2026, 6, 10),
            source_ref="Demo Chief/Aide brief",
            notes="Read-only demo action. No local record was created.",
            history=[
                ActionHistoryEntry(
                    changed_at=datetime(2026, 6, 2, 15, 0, tzinfo=UTC),
                    event="created",
                    detail="Demo action created from a sample drill-prep brief.",
                ),
                ActionHistoryEntry(
                    changed_at=datetime(2026, 6, 3, 9, 30, tzinfo=UTC),
                    event="update",
                    detail="status: in_progress",
                ),
            ],
        ),
        ActionRecord(
            action_id="demo-action-medical-readiness",
            user_key=DEMO_USER_KEY,
            title="Confirm medical readiness follow-up",
            description="Check whether the medical readiness gap affects the next drill or AT support plan.",
            owner="S-1/Admin",
            category=ActionCategory.readiness,
            priority=ActionPriority.medium,
            status=ActionStatus.waiting,
            suspense_date=date(2026, 6, 14),
            source_ref="Demo admin readiness",
            notes="Waiting on updated local readiness confirmation.",
            history=[
                ActionHistoryEntry(
                    changed_at=datetime(2026, 6, 2, 15, 5, tzinfo=UTC),
                    event="created",
                    detail="Demo action created from sample admin readiness.",
                )
            ],
        ),
    ]


@router.get("/handoffs/{user_key}", response_model=UserSessionHandoff, summary="Get a stateless demo handoff")
def demo_handoff(user_key: str) -> UserSessionHandoff:
    return UserSessionHandoff(
        user_key=user_key or DEMO_USER_KEY,
        display_name="Capt Demo Smith",
        rank="Capt",
        mos="0602",
        billet="CommO",
        pme=[PmeStatus(program="EWSDEP", status="incomplete", due_date=date(2026, 6, 1))],
        fitreps=[FitrepReminder(occasion="Annual", due_date=date(2026, 6, 15), role="MRO")],
        drill_dates=[
            DrillDateRecord(drill_date=date(2026, 6, 6), label="June drill"),
            DrillDateRecord(drill_date=date(2026, 7, 11), label="July drill"),
        ],
        recurring_drill_notes=["Every drill confirm uniform, haircut, CAC, laptop, and travel admin status."],
        recurring_checks=[
            RecurringCheck(title="Confirm gear and uniform readiness.", category="readiness"),
            RecurringCheck(title="Review DTS voucher status after drill.", category="travel", due_offset_days=3),
        ],
        admin_watch_items=["DTS voucher after drill", "Confirm annual medical readiness status"],
        recommended_books=["MCDP 1 Warfighting"],
        recommended_courses=["Reserve admin fundamentals"],
        preferences={"demo_mode": "stateless_read_only"},
        warnings=["Demo handoff is synthetic and was not read from local storage."],
    )


@router.get(
    "/planning/staff-package",
    response_model=StaffPlanningPackageResponse,
    summary="Get a stateless demo staff planning package",
)
def demo_staff_planning_package() -> StaffPlanningPackageResponse:
    return _planning_orchestrator.build(
        StaffPlanningPackageRequest(
            title="Demo reserve field training package",
            event_type="field_training",
            mission_or_training_goal="Build a one-day field event that improves staff and small-unit readiness.",
            audience="Civil affairs company",
            timeframe="Next drill weekend",
            constraints=["One field day", "Distributed Marines", "Travel required"],
            coordinating_sections=["S-1", "S-4", "S-6", "Safety / ORM"],
            support_requirements=["Billeting", "Movement accountability", "Medical support"],
            partner_types=["Community partner"],
            civil_considerations=["Limited local familiarity between drills"],
            medical_risk_context=["Heat injury risk"],
            casualty_scenarios=["Vehicle rollover"],
            product_types=["warno", "frago", "aar"],
            training_only=True,
        )
    )


@router.post(
    "/analysis/summarize",
    response_model=TextAnalysisResponse,
    summary="Run stateless demo text analysis",
)
def demo_summarize_text(request: TextAnalysisRequest) -> TextAnalysisResponse:
    return _analysis_service.analyze(request)


@router.post(
    "/staff-products/draft",
    response_model=StaffProductDraftResponse,
    summary="Draft a staff product in stateless demo mode",
)
def demo_draft_staff_product(request: StaffProductDraftRequest) -> StaffProductDraftResponse:
    return _staff_product_builder.build(request)


@router.post(
    "/agents/{agent_id}/run",
    response_model=AgentRunResponse,
    summary="Run an agent in stateless demo mode",
)
def demo_run_agent(agent_id: str, request: AgentRunRequest) -> AgentRunResponse:
    agent = agent_registry.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    context_payload = dict(request.context)
    known_keys = {"user_role", "unit_id", "request_is_training_or_fictional", "extra"}
    unknown_context = {key: value for key, value in context_payload.items() if key not in known_keys}
    if unknown_context:
        extra = dict(context_payload.get("extra") or {})
        extra.update(unknown_context)
        context_payload["extra"] = extra
    return agent.run(request.input, AgentContext.model_validate(context_payload))
