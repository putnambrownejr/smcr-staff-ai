import re

import pytest


PLAYWRIGHT_SETUP_SKIP = "requires: uv add playwright --dev && playwright install chromium && running server"


def _expect(locator):
    from playwright.sync_api import expect

    return expect(locator)


@pytest.mark.e2e
@pytest.mark.skip(reason=PLAYWRIGHT_SETUP_SKIP)
def test_demo_workspace_loads(browser_page):
    page = browser_page

    page.get_by_role("button", name=re.compile(r"open demo workspace", re.I)).first.click()

    _expect(page.get_by_role("heading", name="Act Now")).to_be_visible()
    _expect(page.locator("#readiness-posture")).not_to_be_empty()


@pytest.mark.e2e
@pytest.mark.skip(reason=PLAYWRIGHT_SETUP_SKIP)
def test_lane_tab_navigation(browser_page):
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
@pytest.mark.skip(reason=PLAYWRIGHT_SETUP_SKIP)
def test_bench_section_manage(browser_page):
    page = browser_page

    page.locator("#tab-library").click()

    section_select = page.locator("#bench-section-select")
    _expect(section_select).to_be_visible()
    assert section_select.locator("option").count() > 0

    page.locator("#manage-bench-sections").click()

    _expect(page.locator("#bench-sections-editor")).to_be_visible()


@pytest.mark.e2e
@pytest.mark.skip(reason=PLAYWRIGHT_SETUP_SKIP)
def test_refresh_button_feedback(browser_page):
    page = browser_page

    refresh_button = page.get_by_role("button", name=re.compile(r"refresh", re.I)).first
    refresh_button.click()

    _expect(refresh_button).to_have_text(re.compile(r"refreshing", re.I))
    _expect(refresh_button).not_to_have_text(re.compile(r"refreshing", re.I))


@pytest.mark.e2e
@pytest.mark.skip(reason="manual test: stop server then reload")
def test_server_down_banner(browser_page):
    page = browser_page

    page.reload(wait_until="networkidle")

    _expect(page.locator("#connection-lost-banner")).to_be_visible()
