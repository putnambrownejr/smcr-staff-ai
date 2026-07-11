import os
from collections.abc import Generator
from typing import Any

import pytest


@pytest.fixture(scope="session")
def e2e_base_url() -> str:
    return os.getenv("SMCR_E2E_BASE_URL", "http://localhost:8000").rstrip("/")


@pytest.fixture
def browser_page(e2e_base_url: str) -> Generator[Any, None, None]:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{e2e_base_url}/dashboard")
        page.wait_for_load_state("networkidle")
        try:
            yield page
        finally:
            browser.close()
