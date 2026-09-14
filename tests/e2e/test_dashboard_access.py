import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest


@pytest.mark.e2e
def test_protected_browser_login_and_reload(tmp_path: Path) -> None:
    from playwright.sync_api import expect, sync_playwright

    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]
    env = dict(os.environ, LOCAL_API_KEY="synthetic-browser-passkey", SMCR_STAFF_AI_HOME=str(tmp_path), PROJECTS_DIR=str(tmp_path / "projects"))
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port), "--no-access-log"],
        env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    base = f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            try:
                if httpx.get(base + "/dashboard", timeout=1).status_code == 401:
                    break
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        else:
            pytest.fail("Synthetic protected server did not start")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            page.goto(base + "/dashboard")
            expect(page.get_by_role("heading", name="Unlock SMCR Staff AI", exact=True)).to_be_visible()
            assert "synthetic-browser-passkey" not in page.content()
            page.get_by_label("Local access passkey", exact=True).fill("wrong")
            page.get_by_role("button", name="Unlock dashboard", exact=True).click()
            expect(page.get_by_role("status")).to_contain_text("Passkey not accepted")
            page.get_by_label("Local access passkey", exact=True).fill("synthetic-browser-passkey")
            page.get_by_role("button", name="Unlock dashboard", exact=True).click()
            expect(page.get_by_role("heading", name="SMCR Staff AI", exact=True)).to_be_visible()
            expect(page.get_by_text("Workspace editors ready", exact=True)).to_be_visible()
            page.reload()
            expect(page.get_by_role("heading", name="SMCR Staff AI", exact=True)).to_be_visible()
            assert page.request.get(base + "/dashboard/editors/synthetic").status == 401
            browser.close()
    finally:
        process.terminate()
        process.wait(timeout=15)
