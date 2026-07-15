import os
import uuid
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
        user_key = f"e2e-{uuid.uuid4().hex}"
        page.add_init_script(
            f"window.localStorage.setItem('smcr_user_key', '{user_key}')"
        )
        seed_response = page.request.post(f"{e2e_base_url}/demo/workspace/seed")
        assert seed_response.ok
        page.goto(f"{e2e_base_url}/dashboard", wait_until="domcontentloaded")
        page.get_by_role("heading", name="SMCR Staff AI", level=1).wait_for()
        try:
            yield page
        finally:
            page.request.delete(f"{e2e_base_url}/demo/workspace")
            browser.close()
