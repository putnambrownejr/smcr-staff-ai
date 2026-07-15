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
def test_watch_has_sortable_official_career_opportunities(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "Watch")

    career = page.get_by_role("heading", name="Career Opportunities", level=3).locator("xpath=ancestor::section[1]")
    _expect(career).to_contain_text("SMCR / IMA / ADOS")
    _expect(career.get_by_role("link", name=re.compile("Open official source"))).to_have_count(2)
    _expect(career.get_by_label("Sort Career Opportunities by field")).to_be_visible()
    _expect(career.get_by_role("button", name="Clear filters", exact=True)).to_be_visible()


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

    page.get_by_role("button", name="System OPORD system", exact=True).click()
    _expect(page.get_by_role("heading", name="System OPORD", level=3)).to_be_visible()
    _expect(page.get_by_text("data/templates/system/sys-opord.md", exact=False)).to_be_visible()
    _expect(page.get_by_role("button", name="Start new draft", exact=True)).to_be_visible()
    _expect(page.get_by_role("button", name="Open template location", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_fitreps_are_a_first_class_lane_with_counseling_link(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "FitReps")

    _expect(page.get_by_role("heading", name="FitRep Tracker", level=3)).to_be_visible()
    _expect(page.get_by_role("button", name="+ Start linked counseling", exact=True)).to_be_visible()
    _expect(page.get_by_text("(A–G scale, MCO 1610.7)", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_workspace_exposes_unit_pt_and_gtcc_tools(browser_page: Any) -> None:
    page = browser_page
    _open_lane(page, "Workspace")

    _expect(page.get_by_role("heading", name="Travel & GTCC", level=3)).to_be_visible()
    _expect(page.get_by_role("link", name=re.compile("Open CitiManager"))).to_be_visible()
    _expect(page.get_by_role("heading", name="Unit PT Planner & Cadences", level=3)).to_be_visible()
    _expect(page.get_by_role("button", name="Build staff-reviewed plan", exact=True)).to_be_visible()


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
