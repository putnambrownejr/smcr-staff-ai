import re
from typing import Any

import pytest


def _expect(locator: Any) -> Any:
    from playwright.sync_api import expect

    return expect(locator)


def _open_lane(page: Any, button_name: str, heading_name: str | None = None) -> None:
    page.get_by_role("button", name=button_name, exact=True).click()
    _expect(page.get_by_role("heading", name=heading_name or button_name, level=2)).to_be_visible()


@pytest.mark.e2e
def test_current_dashboard_lane_navigation(browser_page: Any) -> None:
    page = browser_page
    lanes = [
        ("Overview", "Good evening, Capt Schmuckatelli"),
        ("Watch", "Watch"),
        ("Bench / Files", "Bench / Files"),
        ("Workspace", "Workspace"),
        ("FitReps", "FitReps"),
        ("AI", "AI"),
        ("A Few Good...Links", "A Few Good Links"),
    ]

    for button_name, heading_name in lanes:
        _open_lane(page, button_name, heading_name)


@pytest.mark.e2e
def test_watch_shows_per_feed_actions_and_dated_source_updates(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "Watch")

    _expect(page.get_by_role("heading", name="Connected feeds", level=3)).to_be_visible()
    connected_feeds = page.get_by_role("heading", name="Connected feeds", level=3).locator("xpath=..")
    _expect(connected_feeds.get_by_role("button", name="Refresh", exact=True)).to_have_count(2)
    _expect(page.get_by_role("button", name="Open source", exact=True)).to_have_count(1)
    _expect(page.get_by_role("button", name="Manual", exact=True)).to_be_disabled()
    source_updates = page.get_by_role("heading", name="Source updates", level=3).locator("xpath=..")
    _expect(source_updates).to_contain_text(re.compile(r"(?:Published|Detected) [A-Z]{3} \d{1,2}, \d{4}"))


@pytest.mark.e2e
def test_watch_links_out_to_official_career_sources(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "Watch")

    # The in-dashboard listing/filter UI was retired: billets live in
    # browser-based portals, so this panel links out to the official sources
    # rather than restating listings the dashboard cannot authenticate.
    career = page.get_by_role("heading", name="Career Opportunities", level=3).locator("xpath=ancestor::section[1]")
    _expect(career).to_contain_text("SMCR / IMA / ADOS")
    _expect(career.get_by_role("link", name=re.compile("Open official source"))).to_have_count(2)


@pytest.mark.e2e
def test_bench_opens_family_readiness_and_creates_named_event(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "Bench / Files")

    tile = page.get_by_text("Family & Deployment Readiness", exact=True).first.locator("xpath=ancestor::section[1]")
    tile.get_by_role("button", name="Start", exact=True).click()
    dialog = page.get_by_role("dialog", name="Family and Deployment Readiness")
    _expect(dialog).to_be_visible()
    dialog.get_by_label("Event title").fill("Extended AT 2027")
    dialog.get_by_role("button", name="Build checklist", exact=True).click()
    _expect(dialog.get_by_text("Extended AT 2027", exact=True).last).to_be_visible()
    _expect(dialog.get_by_role("button", name="Download generic calendar", exact=True)).to_be_visible()
    _expect(dialog.get_by_role("button", name="Generate spouse-friendly summary", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_template_library_opens_a_real_template(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "Bench / Files")

    page.get_by_role("button", name="Operations Order (OPORD) system", exact=True).click()
    _expect(page.get_by_role("heading", name="Operations Order (OPORD)", level=3)).to_be_visible()
    _expect(page.get_by_role("button", name="Start new draft", exact=True)).to_be_visible()

    # The viewer opens the curated template: annotated scaffold by default,
    # with a toggle that swaps every section over to its worked example.
    page.get_by_role("button", name="View template", exact=True).click()
    _expect(page.get_by_text("Showing the annotated scaffold", exact=False)).to_be_visible()
    # exact=True: the phrase also appears inside another section's scaffold text.
    _expect(page.get_by_text("Task Organization", exact=True)).to_be_visible()

    page.get_by_role("button", name="Show worked example", exact=True).click()
    _expect(page.get_by_text("Showing a worked example", exact=False)).to_be_visible()
    _expect(page.get_by_role("button", name="Show annotated scaffold", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_fitreps_are_a_first_class_lane_with_counseling_link(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "FitReps")

    _expect(page.get_by_role("heading", name="FitRep Tracker", level=3)).to_be_visible()
    _expect(page.get_by_role("button", name="+ Start linked counseling", exact=True)).to_be_visible()
    _expect(page.get_by_text("(A–G, or H for not observed · MCO 1610.7)", exact=True)).to_be_visible()

    # The tracker grades the 14 real MCO 1610.7 attributes, grouped under the
    # report's own sections -- not the five section headings themselves.
    _expect(page.get_by_text("D. Mission Accomplishment", exact=True)).to_be_visible()
    _expect(page.get_by_text("H. Fulfillment of Evaluation Responsibilities", exact=True)).to_be_visible()
    _expect(page.get_by_text("Effectiveness Under Stress", exact=True)).to_be_visible()
    _expect(page.get_by_text("Ensuring Well-being of Subordinates", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_workspace_exposes_gtcc_tools(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "Workspace")

    _expect(page.get_by_role("heading", name="Travel & GTCC", level=3)).to_be_visible()
    _expect(page.get_by_role("link", name=re.compile("Open CitiManager"))).to_be_visible()
    # The Unit PT Planner card was retired; the agent builds that plan in chat.
    _expect(page.get_by_role("heading", name="Logbook", level=3)).to_be_visible()
    _expect(page.get_by_role("heading", name="Session / Drill Handoff", level=3)).to_be_visible()


@pytest.mark.e2e
def test_ai_agent_cards_show_stable_agent_ids(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "AI")

    assert page.get_by_text("Agent ID:", exact=True).count() > 1
    _expect(page.get_by_text("chief-of-staff", exact=True)).to_be_visible()
    _expect(page.get_by_text("planning-advisor", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_demo_mode_hides_demo_project_but_keeps_personal_files_card(
    browser_page: Any,
    demo_project_name: str,
) -> None:
    page = browser_page
    project_button_name = f"{demo_project_name} project folder"
    _open_lane(page, "Bench / Files")
    _expect(page.get_by_role("button", name=project_button_name, exact=True)).to_be_visible()

    page.get_by_role("button", name="Profile & preferences", exact=True).click()
    page.get_by_role("checkbox", name="Demo mode On", exact=True).click(force=True)
    _expect(page.get_by_role("checkbox", name="Demo mode Off", exact=True)).to_be_visible()

    _expect(page.get_by_role("heading", name="Personal files", level=3)).to_be_visible()
    _expect(page.get_by_role("button", name=project_button_name, exact=True)).to_have_count(0)


@pytest.mark.e2e
def test_browser_identity_uses_crt_ega_assets(browser_page: Any) -> None:
    page = browser_page

    assert page.title() == "SMCR Staff AI"
    favicon = page.locator("link[rel='icon'][sizes='32x32']")
    _expect(favicon).to_have_attribute("href", re.compile(r"/static/dashboard/icons/icon-32\.png"))
