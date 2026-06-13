import pytest


@pytest.fixture
def browser_page():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:8000/dashboard")
        page.wait_for_load_state("networkidle")
        try:
            yield page
        finally:
            browser.close()
