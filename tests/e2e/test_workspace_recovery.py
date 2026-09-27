import uuid

import pytest
from playwright.sync_api import sync_playwright


@pytest.mark.e2e
def test_workspace_id_recovery_between_loopback_origins(e2e_base_url: str) -> None:
    port = e2e_base_url.rsplit(":", 1)[-1]
    old_url = f"http://127.0.0.1:{port}/dashboard/workspace-recovery"
    key = f"e2e-recovery-{uuid.uuid4().hex}"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(old_url)
            page.evaluate("key => localStorage.setItem('smcr_user_key', key)", key)
            page.reload()
            assert page.locator("#current-key").inner_text() == key
            page.locator("#new-address-link").click()
            page.get_by_label("Workspace ID").fill(key)
            page.get_by_role("button", name="Open recovered workspace").click()
            page.wait_for_url("**/dashboard")
            assert page.evaluate("localStorage.getItem('smcr_user_key')") == key
            assert page.evaluate("localStorage.getItem('smcr_workspace_mode')") == "personal"
        finally:
            browser.close()
