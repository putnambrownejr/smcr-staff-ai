from fastapi.testclient import TestClient

from app.main import app
from app.schemas.product_templates import ProductTemplateRecord, ProductTemplateType
from app.schemas.staff_products import StaffProductDraftRequest, StaffProductType
from app.services.staff_products.builder import StaffProductBuilder


def test_staff_product_builder_creates_opord_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.opord,
            topic="Training-only field exercise",
            facts=["Annual training timeline is tentative."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Situation" in headings
    assert "5. Command and Signal" in headings
    assert response.review_checklist
    assert response.structured_citations
    assert any("MCWP 5-10" in citation.title for citation in response.structured_citations)
    assert any("3150.05F" in citation.title for citation in response.structured_citations)


def test_staff_products_draft_route_supports_correspondence() -> None:
    client = TestClient(app)

    response = client.post(
        "/staff-products/draft",
        json={
            "product_type": "memorandum",
            "topic": "Training-only staff package routing",
            "audience": "Battalion staff",
            "facts": ["Use current correspondence manual."],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_type"] == "memorandum"
    assert any("5216.5" in citation["title"] for citation in payload["structured_citations"])
    assert payload["formatting_notes"]
    assert any("MCWP 5-10" in citation["title"] for citation in payload["structured_citations"])


def test_staff_product_builder_cites_sitrep_reporting_reference() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.sitrep,
            topic="Training-only battalion status update",
        )
    )

    assert any("3150.05F" in citation.title for citation in response.structured_citations)


def test_staff_product_builder_creates_running_estimate_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.running_estimate,
            topic="Battalion S-4 running estimate for drill support",
            facts=["Transport support is still tentative."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Current Situation" in headings
    assert "5. Decisions Needed And Next 24-72 Hours" in headings
    assert any("what changed" in note.lower() for note in response.formatting_notes)
    assert any("owner" in item.lower() for item in response.review_checklist)
    assert any("MCWP 5-10" in citation.title for citation in response.structured_citations)


def test_staff_product_builder_creates_synchronization_matrix_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.synchronization_matrix,
            topic="Battalion drill synchronization matrix",
            facts=["The XO needs owners and review points by the end of drill."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Event Frame And Command Focus" in headings
    assert "4. Decision Points And Friction" in headings
    assert any("owner" in item.lower() for item in response.review_checklist)
    assert any("timing" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_admin_estimate_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.admin_estimate,
            topic="S-1 admin estimate for pre-drill routing and travel readiness",
            facts=["Orders coverage and DTS status remain the critical friction points."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Admin Frame And Supported Event" in headings
    assert "3. Travel, DTS, GTCC, And Records" in headings
    assert any("execution" in item.lower() for item in response.review_checklist)
    assert any("travel-admin" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_admin_task_tracker_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.admin_task_tracker,
            topic="S-1 admin task tracker for next drill",
            facts=["Late travel claims and stale roster actions need visible owners."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "2. Critical Admin Tasks" in headings
    assert "4. Continuity And Turnover" in headings
    assert any("owner" in item.lower() for item in response.review_checklist)
    assert any("battle board" in note.lower() or "to-do list" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_admin_routing_matrix_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.routing_matrix,
            topic="S-1 routing matrix for orders and travel documents",
            facts=["Reviewer chain and signatures must be visible before drill closeout."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Routing Frame" in headings
    assert "5. Closeout Criteria" in headings
    assert any("routing chain" in item.lower() for item in response.review_checklist)
    assert any("signature authority" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_pre_drill_admin_readiness_check_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.pre_drill_admin_readiness_check,
            topic="Pre-drill admin readiness check for reserve field event",
            facts=["Roster truth and DTS status must be settled before Marines disperse."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Pre-Drill Admin Posture" in headings
    assert "5. No-Surprise Standard" in headings
    assert any("failed check" in item.lower() for item in response.review_checklist)
    assert any("roster truth" in note.lower() or "no-surprise" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_decision_support_matrix_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.decision_support_matrix,
            topic="XO decision support matrix for battalion drill scope cuts",
            facts=["The command team needs a clean cut-versus-risk decision."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Decision Frame" in headings
    assert "4. Recommendation And Decision Triggers" in headings
    assert any("decision" in item.lower() for item in response.review_checklist)
    assert any("tradeoffs" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_due_out_tracker_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.due_out_tracker,
            topic="Chief due-out tracker for command post turnover",
            facts=["The tracker must show slippage before the commander update brief."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "2. Critical Due-Outs" in headings
    assert "4. Turnover And Continuity" in headings
    assert any("owner" in item.lower() for item in response.review_checklist)
    assert any("watchboard" in note.lower() or "turnover" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_collection_matrix_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.collection_matrix,
            topic="Training-only PIR/IR collection matrix for a field exercise",
            facts=["The matrix must support the commander's next decision."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "2. PIR, IR, And Indicators" in headings
    assert "5. Decision Support And Refresh" in headings
    assert any("MCDP 2" in citation.title for citation in response.structured_citations)
    assert any("source caveat" in item.lower() or "caveat" in item.lower() for item in response.review_checklist)


def test_staff_product_builder_creates_sustainment_matrix_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.sustainment_matrix,
            topic="Training-only sustainment matrix for distributed drill support",
            facts=["Vehicle and chow assumptions are still tentative."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "2. Movement And Distribution" in headings
    assert "5. Recovery, Reset, And Follow-Through" in headings
    assert any("MCDP 4" in citation.title or "3502.8A" in citation.title for citation in response.structured_citations)
    assert any("recovery" in note.lower() for note in response.formatting_notes)


def test_staff_product_builder_creates_medical_estimate_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.medical_estimate,
            topic="Training-only medical estimate for one-day field event",
            facts=["Heat injury and vehicle rollover are planning drivers."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Medical Support Frame" in headings
    assert "4. Command Decisions And Rehearsal Checks" in headings
    assert any("Health Service Support" in citation.title for citation in response.structured_citations)
    assert any("qualified medical review" in item.lower() for item in response.review_checklist)


def test_staff_product_builder_creates_public_affairs_plan_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.public_affairs_plan,
            topic="Training-only public affairs plan for battalion family day and media visit",
            facts=["Release authority and visitor flow need to be explicit."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Command Frame And Release Authority" in headings
    assert "4. OPSEC, Imagery, And Approval Controls" in headings
    assert any("who may speak" in item.lower() for item in response.review_checklist)
    assert any("release authority" in note.lower() for note in response.formatting_notes)
    assert any(
        "MCDP 8" in citation.title or "Communication Strategy" in citation.title
        for citation in response.structured_citations
    )


def test_staff_product_builder_creates_security_annex_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.security_annex,
            topic="Training-only security annex for a battalion formal event with guest access",
            facts=["Access control and parking flow are the main friction points."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "2. Access Control And Visitor Management" in headings
    assert "4. Force Protection And Emergency Actions" in headings
    assert any("access control" in item.lower() for item in response.review_checklist)
    assert any("traffic" in note.lower() for note in response.formatting_notes)
    assert any(
        "5530.14A" in citation.title or "Access Control Policy" in citation.title
        for citation in response.structured_citations
    )


def test_staff_product_builder_creates_resource_estimate_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.resource_estimate,
            topic="Reserve resource estimate for a constrained drill-support package",
            facts=["Transportation and visitor support cannot both be fully funded."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Resource Frame And Supported Decision" in headings
    assert "3. Prioritization And Tradeoffs" in headings
    assert any("funded, cut, deferred, or rephased" in item.lower() for item in response.review_checklist)
    assert any("tradeoff" in note.lower() for note in response.formatting_notes)
    assert any("7300.21B" in citation.title or "G-8" in citation.title for citation in response.structured_citations)


def test_staff_product_builder_creates_inspection_readiness_plan_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.inspection_readiness_plan,
            topic="Inspection readiness plan for recurring DTS and records-management friction",
            facts=["The command needs evidence and referral boundaries, not a complaint pile."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Inspection Frame And Scope" in headings
    assert "3. Gaps, Trends, And Boundary Notes" in headings
    assert any("ig independence" in item.lower() for item in response.review_checklist)
    assert any(
        "referral boundaries" in note.lower() or "independence" in note.lower()
        for note in response.formatting_notes
    )
    assert any(
        "5430.1A" in citation.title or "Inspector General" in citation.title
        for citation in response.structured_citations
    )


def test_staff_product_builder_creates_conop_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.conop,
            topic="Initial company concept for field training",
            facts=["Subordinate elements must refine local concepts."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Purpose and End State" in headings
    assert "2. Unit and Sub-Unit Relationships" in headings
    assert response.review_checklist


def test_staff_product_builder_adds_navmac_style_notes_for_naval_letter() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.naval_letter,
            topic="Training-only command package routing",
            facts=["Use current correspondence guidance."],
        )
    )

    assert response.formatting_notes
    assert any("From/To/Via/Subj" in note for note in response.formatting_notes)


def test_staff_product_builder_strengthens_aar_sections_and_notes() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.aar,
            topic="Training-only field exercise AAR",
            facts=["Unit measured reporting discipline and accountability under friction."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Event and Command Frame" in headings
    assert "3. Sustains and What Held" in headings
    assert "5. Corrective Actions for the Next Event" in headings
    assert any("XO or S-3 would keep" in note for note in response.formatting_notes)
    assert any("named owner" in item for item in response.review_checklist)
    assert any("1553.3C" in citation.title for citation in response.structured_citations)


def test_staff_product_builder_creates_baseline_ipb_sections() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.ipb,
            topic="Training-only public-source IPB for a field exercise",
            facts=["Scenario actors and injects are fictional."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "1. Define The Operational Environment" in headings
    assert "4. Determine Threat COAs And Indicators" in headings
    assert any("MCRP 2-10B.1" in citation.title for citation in response.structured_citations)
    assert any("USGS" in citation.title for citation in response.structured_citations)
    assert any("S-2/G-2" in warning for warning in response.warnings)
    assert any("assumptions" in item.lower() for item in response.review_checklist)
    assert any("generic terrain" in note for note in response.formatting_notes)


def test_staff_product_builder_creates_decision_brief_slide_structure() -> None:
    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.decision_brief,
            topic="Decision brief for reserve field training scope reduction",
            facts=["Commander must decide whether to keep two lanes or cut to one."],
        )
    )

    headings = [section.heading for section in response.sections]
    assert "Slide 1. Commander Problem and Decision Required" in headings
    assert "Slide 4. Options or COAs" in headings
    assert any("one decision problem" in note for note in response.formatting_notes)
    assert any("Cut any slide" in item for item in response.review_checklist)


def test_staff_product_builder_applies_local_template_guidance() -> None:
    template = ProductTemplateRecord(
        template_id="abc12345def67890",
        template_name="Example CUB",
        template_type=ProductTemplateType.cub_brief,
        reusable_headings=["Executive Snapshot", "Friction", "Decision Required"],
        reusable_guidance=["Keep the brief to five slides and lead with friction."],
        audience_hint="Battalion commander",
    )

    response = StaffProductBuilder().build(
        StaffProductDraftRequest(
            product_type=StaffProductType.command_update_brief,
            topic="Weekly reserve readiness update",
        ),
        templates=[template],
    )

    assert response.applied_templates == ["Example CUB"]
    assert any("local example template was applied" in note.lower() for note in response.formatting_notes)
    assert any("stale names" in item for item in response.review_checklist)
    assert any("Local template reference" in prompt for prompt in response.sections[0].prompts)


def test_staff_products_agent_defaults_slide_requests_to_decision_brief() -> None:
    from app.services.agents.base import AgentContext
    from app.services.agents.staff_products_agent import build_staff_products_agent

    agent = build_staff_products_agent()
    response = agent.run(
        "Build me a short slide deck for a commander decision on drill weekend field training scope.",
        context=AgentContext(),
    )

    assert "DECISION_BRIEF draft scaffold" in response.answer


def test_staff_products_agent_detects_ipb_requests() -> None:
    from app.services.agents.base import AgentContext
    from app.services.agents.staff_products_agent import build_staff_products_agent

    agent = build_staff_products_agent()
    response = agent.run(
        "Build a baseline IPB for a training-only field exercise.",
        context=AgentContext(),
    )

    assert "IPB draft scaffold" in response.answer
    assert "1. Define The Operational Environment" in response.answer


def test_staff_products_agent_detects_running_estimate_requests() -> None:
    from app.services.agents.base import AgentContext
    from app.services.agents.staff_products_agent import build_staff_products_agent

    agent = build_staff_products_agent()
    response = agent.run(
        "Build a running estimate for battalion staff support to next drill.",
        context=AgentContext(),
    )

    assert "RUNNING_ESTIMATE draft scaffold" in response.answer
    assert "1. Current Situation" in response.answer


def test_staff_products_agent_detects_new_matrix_and_estimate_requests() -> None:
    from app.services.agents.base import AgentContext
    from app.services.agents.staff_products_agent import build_staff_products_agent

    agent = build_staff_products_agent()
    sync_response = agent.run("Build a synchronization matrix for battalion drill planning.", context=AgentContext())
    admin_estimate_response = agent.run("Build an admin estimate for S-1 pre-drill readiness.", context=AgentContext())
    admin_task_response = agent.run("Build an admin task tracker for orders and DTS due-outs.", context=AgentContext())
    routing_response = agent.run(
        "Build an admin routing matrix for orders and travel packages.",
        context=AgentContext(),
    )
    pre_drill_admin_response = agent.run(
        "Build a pre-drill admin readiness check for the battalion S-1 lane.",
        context=AgentContext(),
    )
    decision_response = agent.run("Build a decision support matrix for the XO.", context=AgentContext())
    due_out_response = agent.run("Build a due-out tracker for the battalion chief.", context=AgentContext())
    collection_response = agent.run(
        "Build a PIR/IR collection matrix for this training-only estimate.",
        context=AgentContext(),
    )
    sustainment_response = agent.run(
        "Build a sustainment matrix and movement table for next drill.",
        context=AgentContext(),
    )
    medical_response = agent.run(
        "Build a medical estimate for a field exercise.",
        context=AgentContext(),
    )

    assert "SYNCHRONIZATION_MATRIX draft scaffold" in sync_response.answer
    assert "ADMIN_ESTIMATE draft scaffold" in admin_estimate_response.answer
    assert "ADMIN_TASK_TRACKER draft scaffold" in admin_task_response.answer
    assert "ROUTING_MATRIX draft scaffold" in routing_response.answer
    assert "PRE_DRILL_ADMIN_READINESS_CHECK draft scaffold" in pre_drill_admin_response.answer
    assert "DECISION_SUPPORT_MATRIX draft scaffold" in decision_response.answer
    assert "DUE_OUT_TRACKER draft scaffold" in due_out_response.answer
    assert "COLLECTION_MATRIX draft scaffold" in collection_response.answer
    assert "SUSTAINMENT_MATRIX draft scaffold" in sustainment_response.answer
    assert "MEDICAL_ESTIMATE draft scaffold" in medical_response.answer


def test_staff_products_agent_detects_public_affairs_and_security_annex_requests() -> None:
    from app.services.agents.base import AgentContext
    from app.services.agents.staff_products_agent import build_staff_products_agent

    agent = build_staff_products_agent()
    pao_response = agent.run(
        "Build a public affairs plan with release approval matrix and response-to-query lines for the event.",
        context=AgentContext(),
    )
    provost_response = agent.run(
        "Build a security annex and access control plan for guest and media entry.",
        context=AgentContext(),
    )

    assert "PUBLIC_AFFAIRS_PLAN draft scaffold" in pao_response.answer
    assert "SECURITY_ANNEX draft scaffold" in provost_response.answer


def test_staff_products_agent_detects_resource_and_inspection_readiness_requests() -> None:
    from app.services.agents.base import AgentContext
    from app.services.agents.staff_products_agent import build_staff_products_agent

    agent = build_staff_products_agent()
    g8_response = agent.run(
        "Build a resource estimate and priority tradeoff brief for a constrained reserve event.",
        context=AgentContext(),
    )
    ig_response = agent.run(
        "Build an inspection readiness plan and IG inquiry boundary note for this command issue.",
        context=AgentContext(),
    )

    assert "RESOURCE_ESTIMATE draft scaffold" in g8_response.answer
    assert "INSPECTION_READINESS_PLAN draft scaffold" in ig_response.answer
