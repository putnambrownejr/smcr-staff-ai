from pathlib import Path
from typing import Any, cast

import pytest

from app.chatgpt_bridge.adapter import ChatGptBridgeAdapter
from app.main import create_app


@pytest.mark.anyio
async def test_build_staff_package_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_staff_package(
        {
            "title": "Adapter planning test",
            "event_type": "field_training",
            "mission_or_training_goal": "Improve drill-weekend field execution.",
            "product_types": ["warno", "aar"],
            "training_only": True,
        }
    )

    assert "Adapter planning test" in cast(str, result["title"])
    assert "recommended_course_of_action" in result
    assert "xo_vet" in result


@pytest.mark.anyio
async def test_draft_staff_product_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.draft_staff_product(
        {
            "product_type": "warno",
            "topic": "Training-only event",
            "training_or_fictional": True,
        }
    )

    assert result["product_type"] == "warno"
    assert "sections" in result


@pytest.mark.anyio
async def test_build_frago_to_conop_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_frago_to_conop(
        {
            "title": "Adapter FRAGO refinement test",
            "supported_unit": "Civil affairs company",
            "mission_or_training_goal": "Refine higher guidance into an initial subordinate concept.",
            "higher_guidance": ["Battalion directs a one-day field event.", "Company will submit initial concept."],
            "training_only": True,
        }
    )

    assert "FRAGO to CONOP package" in cast(str, result["title"])
    assert "initial_conop" in result
    assert "frago_draft" in result


@pytest.mark.anyio
async def test_build_tdg_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_tdg(
        {
            "title": "Reserve convoy link-up",
            "theme": "small-unit decision-making under time pressure",
            "training_objective": "Practice judgment, branch plans, and risk tradeoffs.",
            "constraints": ["Reserve audience", "45-minute session"],
        }
    )

    assert "TDG / wargaming package" in cast(str, result["title"])
    assert result["decision_points"]
    assert result["discussion_questions"]


@pytest.mark.anyio
async def test_build_infantry_training_package_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_infantry_training_package(
        {
            "title": "AT MOUT familiarization",
            "training_goal": "Take logistics and admin Marines through a modified urban familiarization package.",
            "primary_training_population": "logistics and admin Marines",
            "venue_type": "MOUT town",
            "ammunition_type": "blank ammunition",
            "constraints": ["Keep the package simple and supervised."],
        }
    )

    assert "03 familiarization package" in cast(str, result["title"])
    assert result["training_phases"]
    assert result["blank_fire_controls"]
    assert result["citations"]


@pytest.mark.anyio
async def test_build_staff_update_cycle_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_staff_update_cycle(
        {
            "title": "Adapter update cycle test",
            "supported_unit": "Civil affairs company",
            "mission_or_training_goal": "Refine the next drill training plan.",
            "section_updates": [
                {
                    "section": "S-3",
                    "summary": "The event is supportable if the company cuts to one primary lane.",
                    "decisions_needed": ["Commander decides whether to preserve one lane or push two."],
                },
                {
                    "section": "S-4",
                    "summary": "Transport support exists, but issue timing is still tight.",
                    "risks": ["Late issue will compress movement time."],
                },
            ],
            "training_only": True,
        }
    )

    assert "running_estimate" in result
    assert "cub" in result
    assert "cpb" in result
    cub = cast(dict[str, Any], result["cub"])
    update_brief = cast(dict[str, Any], cub["update_brief"])
    assert update_brief["product_type"] == "command_update_brief"


@pytest.mark.anyio
async def test_build_mission_analysis_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_mission_analysis(
        {
            "title": "Adapter mission analysis test",
            "supported_unit": "Civil affairs company",
            "mission_or_training_goal": "Refine the next drill training plan.",
            "higher_guidance": ["Battalion wants a concise mission analysis before the next sync."],
            "coordinating_sections": ["S-3", "S-4", "S-6"],
            "section_updates": [
                {
                    "section": "S-3",
                    "summary": "The event is supportable if the company cuts to one primary lane.",
                    "assumptions": ["Subordinate elements can rehearse locally."],
                    "decisions_needed": ["Commander decides whether to keep one lane."],
                }
            ],
            "training_only": True,
        }
    )

    assert "mission_statement" in result
    assert result["specified_tasks"]
    assert result["staff_estimate_requirements"]


@pytest.mark.anyio
async def test_build_planning_cell_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_planning_cell(
        {
            "title": "Adapter planning cell test",
            "supported_unit": "Civil affairs company",
            "mission_or_training_goal": "Refine the next drill training plan.",
            "coordinating_sections": ["S-3", "S-4", "S-6"],
            "support_requirements": ["Transport", "Water"],
            "section_updates": [
                {
                    "section": "S-3",
                    "summary": "The event is supportable if the company cuts to one primary lane.",
                    "assumptions": ["Subordinate elements can rehearse locally."],
                    "decisions_needed": ["Commander decides whether to keep one lane."],
                },
                {
                    "section": "S-4",
                    "summary": "Transport support exists, but issue timing is still tight.",
                    "risks": ["Late issue will compress movement time."],
                },
            ],
            "training_only": True,
        }
    )

    assert "planning_approach" in result
    assert "mission_analysis" in result
    assert "update_cycle" in result
    assert result["assumption_log"]


@pytest.mark.anyio
async def test_build_lone_planner_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_lone_planner(
        {
            "title": "Adapter lone planner test",
            "supported_unit": "Civil affairs company",
            "mission_or_training_goal": "Refine the next drill training plan.",
            "coordinating_sections": ["S-3", "S-4"],
            "support_requirements": ["Transport", "Water"],
            "section_updates": [
                {
                    "section": "S-3",
                    "summary": "The event is supportable if the company cuts to one primary lane.",
                    "assumptions": ["Subordinate elements can rehearse locally."],
                    "decisions_needed": ["Commander decides whether to keep one lane."],
                }
            ],
            "training_only": True,
        }
    )

    assert result["posture"]
    assert result["walk_in_brief"]
    assert result["likely_blind_spots"]
    assert result["planning_cell"]["mission_analysis"]["mission_statement"]


@pytest.mark.anyio
async def test_run_opt_facilitator_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_opt_facilitator(
        {
            "input": "Help me run mission analysis with assumptions and due-outs visible.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "opt-facilitator"
    assert "OPT facilitator advisory" in cast(str, result["answer"])


@pytest.mark.anyio
async def test_run_sja_military_justice_advisor_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_sja_military_justice_advisor(
        {
            "input": "Help me issue-spot an NJP question before I route it.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "jag-legal-advisor"
    assert "SJA / military justice advisory" in cast(str, result["answer"])


@pytest.mark.anyio
async def test_run_infantry_03xx_advisor_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_infantry_03xx_advisor(
        {
            "input": "Help me shape infantry-flavored training for support Marines at AT.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "infantry-03xx-advisor"
    assert "Infantry / 03XX advisory draft under the S-3 family." in cast(str, result["answer"])


@pytest.mark.anyio
async def test_run_patrolling_refresher_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_patrolling_refresher(
        {
            "input": "Refresh the basics for a simple training patrol lane.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "infantry-03xx-advisor"
    assert "patrolling" in cast(str, result["answer"]).lower()


@pytest.mark.anyio
async def test_run_blank_fire_urban_lane_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_blank_fire_urban_lane(
        {
            "input": "Help me control a blank-fire MOUT lane for non-03 Marines.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "infantry-03xx-advisor"
    answer = cast(str, result["answer"]).lower()
    assert "blank" in answer
    assert "urban" in answer


@pytest.mark.anyio
async def test_run_leader_rehearsal_oic_worksheet_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_leader_rehearsal_oic_worksheet(
        {
            "input": "Build me an OIC worksheet for a modified urban training lane.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "infantry-03xx-advisor"
    answer = cast(str, result["answer"]).lower()
    assert "oic" in answer or "leader" in answer
    assert "safety" in answer


@pytest.mark.anyio
async def test_run_njp_issue_spotting_worksheet_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_njp_issue_spotting_worksheet(
        {
            "input": "Walk me through a reserve NJP issue.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "jag-legal-advisor"
    answer = cast(str, result["answer"])
    assert "NJP / Article 15 issue-spotting" in answer
    assert "Reserve" in answer


@pytest.mark.anyio
async def test_run_military_justice_routing_checklist_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_military_justice_routing_checklist(
        {
            "input": "Help me route a possible military justice matter correctly.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "jag-legal-advisor"
    answer = cast(str, result["answer"])
    assert "proper legal handoff lane" in answer
    assert "SJA" in answer
    assert "defense" in answer
    assert "VLC" in answer
    assert "trial services" in answer


@pytest.mark.anyio
async def test_run_red_team_assumptions_challenge_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_red_team_assumptions_challenge(
        {
            "input": "Pressure-test this concept before the commander brief.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "red-team-assumptions-challenge"
    assert "Red-team / assumptions challenge advisory" in cast(str, result["answer"])


@pytest.mark.anyio
async def test_run_assessment_learning_advisor_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_assessment_learning_advisor(
        {
            "input": "Help me turn this AAR into real next-drill follow-through.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "assessment-learning-advisor"
    assert "Assessment / learning advisory" in cast(str, result["answer"])


@pytest.mark.anyio
async def test_run_writing_briefing_coach_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_writing_briefing_coach(
        {
            "input": "Help me tighten this decision brief before the commander sees it.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "writing-briefing-coach"
    assert "Writing / briefing coach advisory" in cast(str, result["answer"])


@pytest.mark.anyio
async def test_run_joint_interagency_frame_advisor_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.run_joint_interagency_frame_advisor(
        {
            "input": "Help me think through command relationships and outside stakeholders for this problem.",
            "context": {"request_is_training_or_fictional": True, "user_role": "SMCR officer"},
        }
    )

    assert result["agent_id"] == "joint-interagency-frame-advisor"
    assert "Joint / interagency frame advisory" in cast(str, result["answer"])


@pytest.mark.anyio
async def test_list_agents_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.list_agents()

    assert "agents" in result
    assert any(agent["id"] == "s3-opso" for agent in result["agents"])


@pytest.mark.anyio
async def test_build_next_drill_readiness_via_adapter() -> None:
    adapter = ChatGptBridgeAdapter(app=create_app())

    result = await adapter.build_next_drill_readiness(
        {
            "user_key": "capt-example",
            "include_personal_documents": True,
            "include_drill_plans": True,
        }
    )

    assert cast(str, result["title"]) == "Chief of Staff / Aide de Camp triage brief"
    assert "next_drill_readiness" in result
    assert "readiness_posture" in cast(dict[str, object], result["next_drill_readiness"])


@pytest.mark.anyio
async def test_build_handoff_reminder_plans_via_adapter(tmp_path: Path) -> None:
    from datetime import date

    from app.api.routes.calendar import get_handoff_store, get_plan_store
    from app.main import app
    from app.schemas.session import DrillDateRecord, RecurringCheck, UserSessionHandoff
    from app.services.calendar.plan_store import DrillPrepPlanStore
    from app.services.session.handoff_store import SessionHandoffStore

    adapter = ChatGptBridgeAdapter(app=app)
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    plan_store = DrillPrepPlanStore(tmp_path / "plans")
    handoff_store.upsert(
        UserSessionHandoff(
            user_key="adapter-rhythm",
            unit_id="example-unit",
            drill_dates=[DrillDateRecord(drill_date=date(2026, 6, 6), label="June drill")],
            recurring_checks=[
                RecurringCheck(
                    title="Review DTS voucher after drill.",
                    cadence="post_drill",
                    category="travel",
                    due_offset_days=2,
                )
            ],
        )
    )

    def override_handoff_store() -> SessionHandoffStore:
        return handoff_store

    def override_plan_store() -> DrillPrepPlanStore:
        return plan_store

    app.dependency_overrides[get_handoff_store] = override_handoff_store
    app.dependency_overrides[get_plan_store] = override_plan_store
    try:
        result = await adapter.build_handoff_reminder_plans(user_key="adapter-rhythm")
    finally:
        app.dependency_overrides.clear()

    assert result["generated_plan_ids"]
    assert result["plans"]


@pytest.mark.anyio
async def test_active_user_context_round_trip_via_adapter(tmp_path: Path) -> None:
    from app.api.routes.user_context import get_active_context_store
    from app.main import app
    from app.services.session.active_context_store import ActiveUserContextStore

    adapter = ChatGptBridgeAdapter(app=app)
    active_context_store = ActiveUserContextStore(tmp_path / "active-context")

    def override_active_context_store() -> ActiveUserContextStore:
        return active_context_store

    app.dependency_overrides[get_active_context_store] = override_active_context_store
    try:
        saved = await adapter.set_active_user_context(
            user_key="capt-bridge",
            payload={
                "user_key": "capt-bridge",
                "unit_name": "Civil Affairs Company",
                "unit_type": "civil affairs",
                "staff_bias": ["Bias planning toward civil reconnaissance and partner continuity."],
            },
        )
        loaded = await adapter.get_active_user_context(user_key="capt-bridge")
    finally:
        app.dependency_overrides.clear()

    saved_context = cast(dict[str, object], saved["active_user_context"])
    assert saved_context["unit_name"] == "Civil Affairs Company"
    assert loaded["unit_type"] == "civil affairs"


@pytest.mark.anyio
async def test_build_external_ai_packet_via_adapter(tmp_path: Path) -> None:
    from datetime import UTC, datetime

    from app.api.routes.sharing import (
        get_active_context_store,
        get_context_store,
        get_handoff_store,
        get_opportunity_tracker,
        get_plan_store,
    )
    from app.main import app
    from app.schemas.session import UserSessionHandoff
    from app.schemas.user_context import ActiveUserContext
    from app.services.calendar.plan_store import DrillPrepPlanStore
    from app.services.opportunities.tracker import OpportunityTracker
    from app.services.session.active_context_store import ActiveUserContextStore
    from app.services.session.handoff_store import SessionHandoffStore
    from app.services.storage.local_context_store import LocalContextStore

    adapter = ChatGptBridgeAdapter(app=app)
    handoff_store = SessionHandoffStore(tmp_path / "handoffs")
    active_context_store = ActiveUserContextStore(tmp_path / "active-context")
    context_store = LocalContextStore(tmp_path / "context")
    plan_store = DrillPrepPlanStore(tmp_path / "plans")
    opportunity_tracker = OpportunityTracker(tmp_path / "opportunities")

    handoff_store.upsert(
        UserSessionHandoff(
            user_key="capt-external",
            display_name="Capt Example",
            rank="Capt",
            mos="1702",
            billet="Plans Officer",
            updated_at=datetime.now(UTC),
        )
    )
    active_context_store.upsert(
        ActiveUserContext(
            user_key="capt-external",
            unit_name="Civil Affairs Company",
            unit_type="civil affairs",
        )
    )
    context_store.save(
        filename="bio.txt",
        content=b"BIO draft with phone: 555-123-4567",
        content_type="text/plain",
        document_type="bio",
    )

    app.dependency_overrides[get_handoff_store] = lambda: handoff_store
    app.dependency_overrides[get_active_context_store] = lambda: active_context_store
    app.dependency_overrides[get_context_store] = lambda: context_store
    app.dependency_overrides[get_plan_store] = lambda: plan_store
    app.dependency_overrides[get_opportunity_tracker] = lambda: opportunity_tracker
    try:
        result = await adapter.build_external_ai_packet(
            {
                "user_key": "capt-external",
                "target_platform": "genai",
                "include_document_summary": True,
                "purpose": "an advisory training review",
            }
        )
    finally:
        app.dependency_overrides.clear()

    assert result["target_platform"] == "genai"
    handoff = cast(dict[str, object], result["handoff"])
    document_summary = cast(dict[str, object], result["document_summary"])
    assert handoff["mos"] == "1702"
    assert document_summary["total_documents"] == 1
    assert result["recommended_share_format"] == "json-plus-brief"
    assert "UNCLASSIFIED" in cast(str, result["recommended_share_prompt"])
