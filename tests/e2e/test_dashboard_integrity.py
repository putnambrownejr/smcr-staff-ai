import uuid
from collections.abc import Generator
from typing import Any

import pytest


@pytest.fixture()
def personal_page(e2e_base_url: str) -> Generator[Any, None, None]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        user_key = "integrity-" + uuid.uuid4().hex
        page.add_init_script(
            f"localStorage.setItem('smcr_user_key', '{user_key}');"
            "if (!localStorage.getItem('smcr_workspace_mode')) localStorage.setItem('smcr_workspace_mode', 'personal');"
        )
        page.goto(e2e_base_url + "/dashboard")
        page.get_by_role("heading", name="Saved work", exact=True).wait_for()
        try:
            yield page
        finally:
            page.request.delete(e2e_base_url + "/handoffs/" + user_key)
            browser.close()


def _journal(page: Any) -> Any:
    page.get_by_role("button", name="Workspace", exact=True).click()
    return page.get_by_role("heading", name="Session / Drill Handoff", exact=True).locator("xpath=ancestor::section[1]")


@pytest.mark.e2e
def test_personal_overview_is_truthful_after_reload(personal_page: Any) -> None:
    from playwright.sync_api import expect

    page = personal_page
    for _ in range(2):
        expect(page.get_by_text("Next drill · No upcoming date saved", exact=True)).to_be_visible()
        expect(page.get_by_text("No open actions tracked yet. Add an action in Watch.", exact=True)).to_be_visible()
        expect(page.get_by_text("Two must-do items", exact=False)).to_have_count(0)
        expect(page.get_by_text("FitRep input for Sgt Alvarez", exact=True)).to_have_count(0)
        expect(page.get_by_text("Demo mode", exact=True)).to_have_count(0)
        page.reload()
        page.get_by_role("heading", name="Saved work", exact=True).wait_for()


@pytest.mark.e2e
def test_journal_save_and_archive_survive_reload(personal_page: Any) -> None:
    from playwright.sync_api import expect

    page = personal_page
    panel = _journal(page)
    panel.get_by_role("button", name="+ New handoff", exact=True).click()
    panel.get_by_label("Handoff title", exact=True).fill("Synthetic drill continuity")
    panel.get_by_label("Admin watch items (one per line)", exact=True).fill("Review the synthetic draft")
    panel.get_by_label("Recurring drill notes (one per line)", exact=True).fill("Bring a notebook")
    panel.get_by_role("button", name="Save handoff", exact=True).click()
    expect(panel.get_by_role("status")).to_have_text("Handoff saved")
    page.reload()
    panel = _journal(page)
    expect(panel.get_by_label("Handoff title", exact=True)).to_have_value("Synthetic drill continuity")
    expect(panel.get_by_label("Admin watch items (one per line)", exact=True)).to_have_value("Review the synthetic draft")
    panel.get_by_role("button", name="Archive", exact=True).click()
    expect(panel.get_by_role("status")).to_have_text("Handoff saved")
    page.reload()
    panel = _journal(page)
    panel.get_by_role("button", name="Archived", exact=True).click()
    expect(panel.get_by_label("Handoff title", exact=True)).to_have_value("Synthetic drill continuity")
    panel.get_by_role("button", name="Unarchive", exact=True).click()
    expect(panel.get_by_role("status")).to_have_text("Handoff saved")


@pytest.mark.e2e
def test_failed_journal_save_keeps_edits_and_allows_retry(personal_page: Any) -> None:
    from playwright.sync_api import expect

    page = personal_page
    panel = _journal(page)
    panel.get_by_label("Admin watch items (one per line)", exact=True).fill("Keep this unsaved draft")
    page.route("**/handoffs/*/journal", lambda route: route.fulfill(status=500, body="unavailable"))
    panel.get_by_role("button", name="Save handoff", exact=True).click()
    expect(panel.get_by_role("status")).to_contain_text("Could not save handoff")
    expect(panel.get_by_label("Admin watch items (one per line)", exact=True)).to_have_value("Keep this unsaved draft")
    page.unroute("**/handoffs/*/journal")
    panel.get_by_role("button", name="Save handoff", exact=True).click()
    expect(panel.get_by_role("status")).to_have_text("Handoff saved")


@pytest.mark.e2e
def test_demo_to_personal_switch_stays_personal(personal_page: Any) -> None:
    from playwright.sync_api import expect

    page = personal_page
    page.get_by_role("button", name="Profile & preferences", exact=True).click()
    page.get_by_role("checkbox", name="Demo mode Off", exact=True).check(force=True)
    expect(page.get_by_text("FitRep input for Sgt Alvarez", exact=True)).to_be_visible()
    page.get_by_role("checkbox", name="Demo mode On", exact=True).uncheck(force=True)
    expect(page.get_by_text("No open actions tracked yet. Add an action in Watch.", exact=True)).to_be_visible()
    expect(page.get_by_text("FitRep input for Sgt Alvarez", exact=True)).to_have_count(0)
    page.reload()
    page.get_by_role("heading", name="Saved work", exact=True).wait_for()
    expect(page.get_by_text("Demo mode", exact=True)).to_have_count(0)
    expect(page.get_by_text("FitRep input for Sgt Alvarez", exact=True)).to_have_count(0)


@pytest.mark.e2e
def test_overview_uses_saved_actions_and_drill_date(personal_page: Any, e2e_base_url: str) -> None:
    from playwright.sync_api import expect

    page = personal_page
    user_key = page.evaluate("localStorage.getItem('smcr_user_key')")
    response = page.request.post(e2e_base_url + "/actions/track", data={"actions": [{"user_key": user_key, "title": "Synthetic planning task"}]})
    assert response.ok
    action_id = response.json()["tracked"][0]["action_id"]
    try:
        assert page.request.put(e2e_base_url + "/handoffs/" + user_key, data={"user_key": user_key, "drill_dates": [{"drill_date": "2099-12-01"}]}).ok
        page.reload()
        expect(page.get_by_text("Next drill · 2099-12-01", exact=True)).to_be_visible()
        expect(page.get_by_text("Synthetic planning task", exact=True).first).to_be_visible()
        page.get_by_role("button", name="Review tracked actions", exact=True).click()
        expect(page.get_by_role("heading", name="Watch", exact=True, level=2)).to_be_visible()
        assert page.request.patch(e2e_base_url + "/actions/" + action_id, data={"status": "complete"}).ok
        page.reload()
        expect(page.get_by_text("No open actions tracked yet. Add an action in Watch.", exact=True)).to_be_visible()
    finally:
        page.request.delete(e2e_base_url + "/actions/" + action_id)


@pytest.mark.e2e
@pytest.mark.parametrize("save_succeeds", [True, False])
def test_project_move_requires_successful_draft_save(personal_page: Any, e2e_base_url: str, save_succeeds: bool) -> None:
    from playwright.sync_api import expect

    page = personal_page
    user_key = page.evaluate("localStorage.getItem('smcr_user_key')")
    response = page.request.post(e2e_base_url + "/user-docs/generations/" + user_key, data={
        "title": "Synthetic move check", "fields": {"templateType": "aar", "data": {"event": "Synthetic event"}},
    })
    assert response.ok
    doc_id = response.json()["id"]
    endpoint = "/user-docs/generations/" + user_key + "/" + doc_id
    calls: list[str] = []

    def intercept(route: Any) -> None:
        if route.request.method == "PATCH":
            calls.append("save")
            assert route.request.post_data_json["fields"]["data"]["event"] == "Synthetic event"
            route.fulfill(status=200 if save_succeeds else 500, json={})
        elif route.request.url.endswith("/save-to-project"):
            calls.append("move")
            route.fulfill(status=200, json={"message": "Saved"})
        else:
            route.continue_()

    alerts: list[str] = []

    def dismiss(dialog: Any) -> None:
        alerts.append(dialog.message)
        dialog.accept()

    try:
        page.route("**" + endpoint + "**", intercept)
        page.on("dialog", dismiss)
        page.reload()
        page.get_by_role("button", name="Bench / Files", exact=True).click()
        folder = page.get_by_label("Project folder for Synthetic move check", exact=True)
        folder.fill("synthetic-move-check")
        row = folder.locator("xpath=..")
        row.get_by_role("button", name="Save to project", exact=True).click()
        if save_succeeds:
            expect(folder).to_have_count(0)
            assert calls == ["save", "move"]
        else:
            expect(folder).to_be_visible()
            assert calls == ["save"]
            assert alerts and "has not been moved" in alerts[0]
    finally:
        page.request.delete(e2e_base_url + endpoint)


@pytest.mark.e2e
def test_mobile_lanes_do_not_overflow(personal_page: Any) -> None:
    page = personal_page
    page.set_viewport_size({"width": 390, "height": 844})
    for lane in ("Overview", "Watch", "Bench / Files", "Workspace", "FitReps", "AI", "A Few Good...Links"):
        page.get_by_role("button", name=lane, exact=True).click()
        width = page.evaluate("document.documentElement.scrollWidth")
        assert width <= 391, (lane, width)


@pytest.mark.e2e
def test_staff_notes_persist_and_retry(personal_page: Any) -> None:
    from playwright.sync_api import expect

    page = personal_page
    status = page.get_by_label("Workspace save status", exact=True).get_by_role("status")
    expect(status).to_have_text("Workspace editors ready")
    page.get_by_role("button", name="Bench / Files", exact=True).click()
    page.get_by_text("S-1 / Administration", exact=True).first.click()
    page.get_by_role("button", name="Notes", exact=True).click()
    notes = page.get_by_placeholder("Local how-tos, gotchas, POCs, anything worth remembering…", exact=True)
    page.route("**/dashboard/editors/*", lambda route: route.fulfill(status=500, body="unavailable") if route.request.method == "PUT" else route.continue_())
    notes.fill("Synthetic continuity note")
    expect(status).to_contain_text("Could not save workspace edits")
    expect(notes).to_have_value("Synthetic continuity note")
    page.unroute("**/dashboard/editors/*")
    page.get_by_label("Staff editor save status", exact=True).get_by_role("button", name="Retry workspace save / load", exact=True).click()
    expect(status).to_have_text("Workspace edits saved")
    page.reload()
    expect(status).to_have_text("Workspace editors ready")
    page.get_by_role("button", name="Bench / Files", exact=True).click()
    page.get_by_text("S-1 / Administration", exact=True).first.click()
    page.get_by_role("button", name="Notes", exact=True).click()
    expect(notes).to_have_value("Synthetic continuity note")
