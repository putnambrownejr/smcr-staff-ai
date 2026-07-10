import re
import uuid
from typing import Any

import pytest


def _expect(locator: Any) -> Any:
    from playwright.sync_api import expect

    return expect(locator)


@pytest.mark.e2e
def test_demo_workspace_loads(browser_page: Any) -> None:
    page = browser_page

    page.locator("#tab-configure").click()
    page.locator("#load-demo").click()
    page.locator("#tab-overview").click()

    _expect(page.get_by_role("heading", name="Act Now")).to_be_visible()
    _expect(page.locator("#readiness-posture")).not_to_be_empty()


@pytest.mark.e2e
def test_lane_tab_navigation(browser_page: Any) -> None:
    page = browser_page
    lanes = [
        ("overview", "overview"),
        ("watch", "watch"),
        ("bench-files", "library"),
        ("workflows", "draft"),
        ("workspace", "configure"),
    ]

    for _label, lane in lanes:
        page.locator(f"#tab-{lane}").click()
        _expect(page.locator(f"[data-section-group='{lane}']").first).to_be_visible()

        for _other_label, other_lane in lanes:
            if other_lane == lane:
                continue
            _expect(page.locator(f"[data-section-group='{other_lane}']").first).to_be_hidden()


@pytest.mark.e2e
def test_bench_section_manage(browser_page: Any) -> None:
    page = browser_page

    page.locator("#tab-library").click()
    page.locator("summary").filter(has_text="Section Bench Notebook").click()

    section_select = page.locator("#bench-section-select")
    _expect(section_select).to_be_visible()
    assert section_select.locator("option").count() > 0

    page.locator("#manage-bench-sections").click()

    _expect(page.locator("#bench-sections-editor")).to_be_visible()


@pytest.mark.e2e
def test_refresh_button_feedback(browser_page: Any) -> None:
    page = browser_page

    # first-run profile nudge redirects to configure; navigate to overview where refresh buttons live
    page.locator("#tab-overview").click()
    refresh_button = page.get_by_role("button", name=re.compile(r"refresh", re.I)).first
    refresh_button.click()

    # auto-UUID means a workspace is always loaded; refresh produces a "refreshed" status note
    _expect(page.locator("#workspace-note")).to_have_text(re.compile(r"refresh", re.I))
    _expect(refresh_button).to_be_visible()


@pytest.mark.e2e
def test_tracked_action_mark_done_and_undo(browser_page: Any) -> None:
    page = browser_page
    run_id = uuid.uuid4().hex[:8]
    user_key = f"e2e-action-{run_id}"
    title = f"Finalize drill support request {run_id}"
    create_response = page.request.post(
        "http://localhost:8000/actions/track",
        data={
            "actions": [
                {
                    "user_key": user_key,
                    "title": title,
                    "status": "in_progress",
                }
            ]
        },
    )
    assert create_response.ok
    action_id = create_response.json()["tracked"][0]["action_id"]

    try:
        page.locator("#tab-configure").click()
        page.locator("#advanced-workspace-settings > summary").click()
        page.locator("#custom-profile-key").fill(user_key)
        page.locator("#apply-advanced-settings").click()
        page.locator("#load-personal").click()
        page.locator("#tab-watch").click()
        mark_done = page.get_by_role("button", name=f"Mark {title} done")
        _expect(mark_done).to_be_visible()
        action_title = page.locator("#action-watch").get_by_text(title, exact=True)

        mark_done.click()

        _expect(action_title).to_be_hidden()
        undo = page.get_by_role("button", name=f"Undo completion of {title}")
        _expect(undo).to_be_visible()
        closed_response = page.request.get(
            f"http://localhost:8000/actions?user_key={user_key}&include_closed=true"
        )
        assert any(item["status"] == "closed" for item in closed_response.json())

        undo.click()

        _expect(action_title).to_be_visible()
        restored_response = page.request.get(
            f"http://localhost:8000/actions?user_key={user_key}&include_closed=true"
        )
        assert any(item["status"] == "in_progress" for item in restored_response.json())
    finally:
        page.request.delete(f"http://localhost:8000/actions/{action_id}")


@pytest.mark.e2e
def test_tracked_action_restores_row_when_patch_fails(browser_page: Any) -> None:
    page = browser_page
    run_id = uuid.uuid4().hex[:8]
    user_key = f"e2e-action-failure-{run_id}"
    title = f"Action failure recovery {run_id}"
    create_response = page.request.post(
        "http://localhost:8000/actions/track",
        data={"actions": [{"user_key": user_key, "title": title, "status": "open"}]},
    )
    assert create_response.ok
    action_id = create_response.json()["tracked"][0]["action_id"]

    try:
        page.locator("#tab-configure").click()
        page.locator("#advanced-workspace-settings > summary").click()
        page.locator("#custom-profile-key").fill(user_key)
        page.locator("#apply-advanced-settings").click()
        page.locator("#load-personal").click()
        page.locator("#tab-watch").click()
        action_title = page.locator("#action-watch").get_by_text(title, exact=True)
        _expect(action_title).to_be_visible()
        page.route(
            f"**/actions/{action_id}",
            lambda route: route.fulfill(status=500, content_type="application/json", body='{"detail":"test failure"}'),
        )

        page.get_by_role("button", name=f"Mark {title} done").click()

        _expect(action_title).to_be_visible()
        _expect(page.get_by_role("button", name=f"Undo completion of {title}")).to_be_hidden()
        _expect(page.locator("#workspace-note")).to_have_text(re.compile(r"request failed", re.I))
    finally:
        page.request.delete(f"http://localhost:8000/actions/{action_id}")


@pytest.mark.e2e
def test_external_preview_local_choice_submits_local_only(browser_page: Any) -> None:
    page = browser_page
    submitted_requests: list[dict[str, Any]] = []

    page.route(
        "**/agents/writing-briefing-coach/external-processing-preview",
        lambda route: route.fulfill(
            status=200,
            content_type="application/json",
            json={
                "required": True,
                "external_available": True,
                "provider": "provider.example",
                "model": "example-model",
                "expected_call_count": 1,
                "scope_label": "agent:writing-briefing-coach",
                "original_preview": [{"role": "user", "content": "Original exercise text"}],
                "sanitized_preview": [{"role": "user", "content": "Sanitized exercise text"}],
                "findings": [],
                "finding_categories": [],
                "redacted_fields": [],
                "approval_digest": "a" * 64,
                "payload_digest": "a" * 64,
                "warnings": ["Review before sending."],
            },
        ),
    )

    def capture_run(route: Any) -> None:
        submitted_requests.append(route.request.post_data_json)
        route.fulfill(
            status=200,
            content_type="application/json",
            json={
                "agent_id": "writing-briefing-coach",
                "answer": "Local template response",
                "citations": [],
                "structured_citations": [],
                "source_trust": [],
                "warnings": [],
                "human_review_required": True,
                "confidence": "low",
                "follow_up_questions": [],
                "scenario_output": None,
                "scenario_output_status": "template_only",
            },
        )

    page.route("**/agents/writing-briefing-coach/run", capture_run)
    page.locator("#tab-draft").click()
    page.locator("#drawer-brief-clinic > summary").click()
    page.locator("#brief-clinic-form textarea[name='current_brief']").fill("Training brief draft")
    page.locator("#brief-clinic-form button[type='submit']").click()

    dialog = page.locator("#external-processing-dialog")
    _expect(dialog).to_be_visible()
    _expect(page.locator("#external-processing-sanitized-send")).to_be_disabled()
    _expect(page.locator("#external-processing-original-send")).to_be_disabled()
    page.locator("#external-processing-local").click()

    _expect(dialog).to_be_hidden()
    _expect(page.locator("#brief-clinic-output")).to_contain_text("Local template response")
    assert submitted_requests[0]["external_processing_approval"] == {
        "disclosure_mode": "local_only",
        "acknowledged_finding_categories": [],
        "acknowledged": False,
    }


@pytest.mark.e2e
@pytest.mark.skip(reason="manual test: stop server then reload")
def test_server_down_banner(browser_page: Any) -> None:
    page = browser_page

    page.reload(wait_until="networkidle")

    _expect(page.locator("#connection-lost-banner")).to_be_visible()
