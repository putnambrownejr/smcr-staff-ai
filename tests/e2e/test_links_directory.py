from typing import Any

import pytest


def _expect(locator: Any) -> Any:
    from playwright.sync_api import expect

    return expect(locator)


@pytest.mark.e2e
def test_links_page_is_a_semantic_resource_directory(browser_page: Any) -> None:
    page = browser_page
    page.get_by_role("button", name="A Few Good...Links", exact=True).click()

    _expect(page.get_by_role("heading", name="A Few Good Links", level=2)).to_be_visible()
    for category in ("Admin & pay", "Benefits", "IT & access", "Reference", "Training & PME"):
        _expect(page.get_by_role("heading", name=category, level=3)).to_be_visible()
    _expect(page.get_by_role("link", name="Marine Online (MOL) mol.usmc.mil", exact=True)).to_be_visible()
    _expect(page.get_by_role("link", name="MCO 1020.34H (uniforms) marines.mil", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_links_page_has_no_horizontal_overflow_at_desktop_width(browser_page: Any) -> None:
    page = browser_page
    page.set_viewport_size({"width": 1280, "height": 800})
    page.get_by_role("button", name="A Few Good...Links", exact=True).click()
    _expect(page.get_by_role("heading", name="A Few Good Links", level=2)).to_be_visible()

    overflow = page.evaluate(
        """() => ({
          clientWidth: document.documentElement.clientWidth,
          scrollWidth: document.documentElement.scrollWidth,
        })"""
    )
    assert overflow["scrollWidth"] <= overflow["clientWidth"]
