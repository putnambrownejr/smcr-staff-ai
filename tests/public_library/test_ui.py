from pathlib import Path

import pytest


@pytest.mark.e2e
@pytest.mark.parametrize("width,height", [(390, 844), (1280, 900)])
def test_library_search_read_copy_download_and_mobile_layout(public_url: str, tmp_path: Path, width: int, height: int) -> None:
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": width, "height": height}, permissions=["clipboard-read", "clipboard-write"])
        page = context.new_page()
        errors: list[str] = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto(public_url)
        expect(page.get_by_role("heading", name="The collection")).to_be_visible()
        expect(page.locator(".result")).to_have_count(8)
        page.get_by_label("Find a topic or product").fill("AAR")
        page.get_by_label("Show", exact=True).select_option("template")
        expect(page.locator(".result").first).to_contain_text("After Action Review")
        page.locator(".result").first.click()
        expect(page.locator("#item-title")).to_have_text("After Action Review (AAR)")
        page.get_by_role("button", name="Copy text", exact=True).click()
        expect(page.locator("#copy-status")).to_contain_text("Copied")
        copied = page.evaluate("navigator.clipboard.readText()")
        assert "DRAFT — Verify" in copied
        assert "Sources:" in copied
        with page.expect_download() as downloaded:
            page.get_by_role("link", name="Download .md").click()
        download = downloaded.value
        assert download.suggested_filename == "sys-aar.md"
        output = tmp_path / download.suggested_filename
        download.save_as(output)
        assert "## Draft scaffold" in output.read_text(encoding="utf-8")
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.get_by_role("button", name="Close selected item").click()
        page.get_by_label("Find a topic or product").fill("no-such-entry-xyz")
        page.get_by_role("button", name="Search", exact=True).click()
        expect(page.locator("#status")).to_contain_text("No matches")
        page.get_by_role("button", name="Copy connection URL").click()
        assert page.evaluate("navigator.clipboard.readText()") == public_url + "/mcp"
        assert errors == []
        browser.close()


@pytest.mark.e2e
def test_library_network_error_is_recoverable(public_url: str) -> None:
    from playwright.sync_api import expect, sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.route("**/api/catalog?*", lambda route: route.fulfill(status=503, body="Unavailable"))
        page.goto(public_url)
        expect(page.locator("#status")).to_contain_text("503")
        expect(page.get_by_role("button", name="Next →")).to_be_disabled()
        page.unroute("**/api/catalog?*")
        page.get_by_role("button", name="Search", exact=True).click()
        expect(page.locator(".result")).to_have_count(8)
        browser.close()
