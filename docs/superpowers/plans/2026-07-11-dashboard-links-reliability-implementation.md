# Dashboard Reliability and Links Directory Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make dashboard connection warnings truthful, explain local port collisions, and replace the Links pill wall with an authenticated, searchable, responsive text-link directory.

**Architecture:** Keep the existing FastAPI routes, JSON storage, and vanilla-JavaScript dashboard. Separate transport state from HTTP response handling inside apiFetch, add a small standard-library startup preflight, and replace the Links renderer with a state-driven directory that uses semantic category sections and ordinary hyperlinks.

**Tech Stack:** Python 3.12, FastAPI, Pydantic, vanilla ES modules, CSS Grid, pytest, Playwright for Python, mypy, Ruff, and uv.

## Global Constraints

- Implement only in C:/smcr-staff-ai until the tested project change is published to GitHub.
- Do not edit C:/smcr-staff-ai-personal; update it only by pulling the published origin/main result.
- Preserve the shared local data root, resource-links API, and existing JSON schema.
- Keep the dashboard UNCLASSIFIED-only and retain its draft/current-source warning.
- Do not add analytics, recent-link tracking, favorites storage, external link checking, or unrelated lane refactors.
- Render ordinary text links with visible hostnames: three category columns at 1280px, two at 768px, and one at 375px.
- Run E2E tests against an isolated project server and data root, never the personal server on port 8000.

---

### Task 1: Isolate E2E Targeting and Correct Connection-State Classification

**Files:**
- Modify: tests/e2e/conftest.py
- Modify: tests/e2e/test_dashboard_flows.py
- Modify: app/static/dashboard/dashboard.js

**Interfaces:**
- Produces fixture dashboard_base_url() -> str from SMCR_E2E_BASE_URL, with http://localhost:8000 as the compatibility default.
- Produces JavaScript helpers recordTransportSuccess() and recordTransportFailure().
- Preserves apiFetch(path, options), including status, responseText, and isNetworkError on thrown errors.
- Uses Playwright route.abort(error_code="connectionfailed") for transport rejection and route.fulfill(status=...) for HTTP responses, per the [official Route API](https://playwright.dev/python/docs/api/class-route).

- [ ] **Step 1: Make the E2E origin configurable**

Replace tests/e2e/conftest.py with:

    import os
    from collections.abc import Generator
    from typing import Any

    import pytest


    @pytest.fixture
    def dashboard_base_url() -> str:
        return os.getenv("SMCR_E2E_BASE_URL", "http://localhost:8000").rstrip("/")


    @pytest.fixture
    def browser_page(dashboard_base_url: str) -> Generator[Any, None, None]:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(f"{dashboard_base_url}/dashboard")
            page.wait_for_load_state("networkidle")
            try:
                yield page
            finally:
                browser.close()

Update action tests to accept dashboard_base_url and replace every hard-coded http://localhost:8000 request with f"{dashboard_base_url}/...".

- [ ] **Step 2: Start an isolated project server for all browser cycles**

In a dedicated background terminal rooted at C:/smcr-staff-ai:

    $env:SMCR_STAFF_AI_HOME = "$env:TEMP\smcr-staff-ai-dashboard-links-e2e"
    uv run uvicorn app.main:app --host 127.0.0.1 --port 8001

In the test terminal:

    $env:SMCR_E2E_BASE_URL = "http://127.0.0.1:8001"

Verify the listener command line points at C:/smcr-staff-ai/.venv before running tests.

- [ ] **Step 3: Replace the skipped manual banner test with deterministic tests**

Add this helper below _expect:

    def _attempt_personal_workspace_load(page: Any) -> None:
        note = page.locator("#workspace-note")
        marker = f"e2e-waiting-{uuid.uuid4().hex}"
        note.evaluate("(element, value) => { element.textContent = value; }", marker)
        with page.expect_request("**/dashboard/data/**"):
            page.locator("#load-personal").click()
        _expect(note).not_to_have_text(marker)

Replace the skipped test with:

    @pytest.mark.e2e
    def test_three_transport_failures_show_connection_lost_banner(browser_page: Any) -> None:
        page = browser_page
        page.locator("#tab-configure").click()
        page.route(
            "**/dashboard/data/**",
            lambda route: route.abort(error_code="connectionfailed"),
        )
        for _ in range(3):
            _attempt_personal_workspace_load(page)
        _expect(page.locator("#server-unavailable-banner")).to_be_visible()
        _expect(page.locator("#connection-lost-banner")).to_be_visible()

Add the RED regression:

    @pytest.mark.e2e
    def test_http_error_response_clears_prior_transport_failures(browser_page: Any) -> None:
        page = browser_page
        page.locator("#tab-configure").click()
        outcomes = ["transport", "transport", "http"]

        def handle_workspace_request(route: Any) -> None:
            outcome = outcomes.pop(0)
            if outcome == "transport":
                route.abort(error_code="connectionfailed")
                return
            route.fulfill(
                status=500,
                content_type="application/json",
                body='{"detail":"expected application error"}',
            )

        page.route("**/dashboard/data/**", handle_workspace_request)
        for _ in range(3):
            _attempt_personal_workspace_load(page)

        _expect(page.locator("#workspace-note")).to_contain_text("Request failed (500)")
        _expect(page.locator("#server-unavailable-banner")).to_be_hidden()
        _expect(page.locator("#connection-lost-banner")).to_be_hidden()

- [ ] **Step 4: Run the focused test and confirm RED**

    uv run pytest -m e2e tests/e2e/test_dashboard_flows.py::test_http_error_response_clears_prior_transport_failures -q

Expected: connection-lost remains visible because the 500 is incorrectly counted as the third connection failure.

- [ ] **Step 5: Implement transport-only bookkeeping**

Rename state.consecutiveFetchFailures to state.consecutiveTransportFailures. Refactor apiFetch and the counter helpers to:

    async function apiFetch(path, options = {}) {
      const headers = { "Content-Type": "application/json" };
      if (options.auth && state.apiKey) {
        headers["X-Local-API-Key"] = state.apiKey;
      }
      let response;
      try {
        response = await fetch(state.apiBase + path, {
          method: options.method || "GET",
          headers,
          body: options.body,
        });
      } catch (error) {
        recordTransportFailure();
        const networkError = new Error("Cannot reach local server.");
        networkError.isNetworkError = true;
        networkError.cause = error;
        throw networkError;
      }

      recordTransportSuccess();
      if (!response.ok) {
        const text = await response.text();
        const httpError = new Error("Request failed (" + response.status + "): " + text);
        httpError.status = response.status;
        httpError.responseText = text;
        throw httpError;
      }
      if (response.status === 204) return null;
      if (options.text) return response.text();
      if (options.blob) return response.blob();
      return response.json();
    }

    function recordTransportSuccess() {
      state.consecutiveTransportFailures = 0;
      setConnectionLostVisible(false);
      setServerUnavailableVisible(false);
    }

    function recordTransportFailure() {
      state.consecutiveTransportFailures += 1;
      if (state.consecutiveTransportFailures >= 3 && !state.connectionLostDismissed) {
        setConnectionLostVisible(true);
      }
    }

- [ ] **Step 6: Add HTTP-status and invalid-JSON coverage**

Add:

    @pytest.mark.e2e
    @pytest.mark.parametrize("status", [401, 404, 422, 500])
    def test_repeated_http_errors_never_show_connection_banners(
        browser_page: Any,
        status: int,
    ) -> None:
        page = browser_page
        page.locator("#tab-configure").click()
        page.route(
            "**/dashboard/data/**",
            lambda route: route.fulfill(
                status=status,
                content_type="application/json",
                body='{"detail":"expected application error"}',
            ),
        )
        for _ in range(3):
            _attempt_personal_workspace_load(page)
        _expect(page.locator("#server-unavailable-banner")).to_be_hidden()
        _expect(page.locator("#connection-lost-banner")).to_be_hidden()


    @pytest.mark.e2e
    def test_invalid_json_does_not_count_as_transport_failure(browser_page: Any) -> None:
        page = browser_page
        page.locator("#tab-configure").click()
        outcomes = ["invalid-json", "transport", "transport"]

        def handle_workspace_request(route: Any) -> None:
            outcome = outcomes.pop(0)
            if outcome == "invalid-json":
                route.fulfill(status=200, content_type="application/json", body="{")
                return
            route.abort(error_code="connectionfailed")

        page.route("**/dashboard/data/**", handle_workspace_request)
        for _ in range(3):
            _attempt_personal_workspace_load(page)
        _expect(page.locator("#server-unavailable-banner")).to_be_visible()
        _expect(page.locator("#connection-lost-banner")).to_be_hidden()

- [ ] **Step 7: Run Task 1 verification**

    uv run pytest -m e2e tests/e2e/test_dashboard_flows.py -q
    uv run pytest tests/test_dashboard.py -q
    uv run ruff check tests/e2e
    git diff --check

Expected: all selected tests pass and no whitespace issue is reported.

- [ ] **Step 8: Commit Task 1**

    git add app/static/dashboard/dashboard.js tests/e2e/conftest.py tests/e2e/test_dashboard_flows.py
    git commit -m "fix: separate transport and HTTP dashboard errors"

---

### Task 2: Add Safe Startup Port Preflight

**Files:**
- Create: app/startup_preflight.py
- Create: tests/test_startup_preflight.py
- Modify: start.bat
- Modify: start.sh

**Interfaces:**
- Produces parse_port(value: str) -> int.
- Produces is_loopback_port_accepting_connections(port: int, *, timeout: float = 0.25) -> bool.
- Produces occupied_port_message(port: int, checkout: Path) -> str.
- Produces main(argv: Sequence[str] | None = None) -> int, returning 0 for available, 1 for occupied, and 2 for invalid.
- Uses Python’s documented [socket.create_connection](https://docs.python.org/3/library/socket.html#socket.create_connection) and Uvicorn’s documented [host and port settings](https://www.uvicorn.org/settings/).

- [ ] **Step 1: Write failing preflight tests**

Create tests/test_startup_preflight.py:

    from __future__ import annotations

    import socket
    from pathlib import Path

    import pytest

    from app import startup_preflight


    def test_occupied_port_reports_checkout_and_leaves_listener_running(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        monkeypatch.chdir(tmp_path)
        with socket.create_server((startup_preflight.LOOPBACK_HOST, 0)) as listener:
            port = int(listener.getsockname()[1])
            result = startup_preflight.main(["--port", str(port)])
            captured = capsys.readouterr()
            assert result == startup_preflight.EXIT_OCCUPIED
            assert captured.out == ""
            assert str(port) in captured.err
            assert str(tmp_path.resolve()) in captured.err
            assert "Another SMCR Staff AI checkout may already be running" in captured.err
            assert "SMCR_PORT" in captured.err
            assert listener.fileno() >= 0


    def test_available_port_exits_silently(capsys: pytest.CaptureFixture[str]) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as candidate:
            candidate.bind((startup_preflight.LOOPBACK_HOST, 0))
            port = int(candidate.getsockname()[1])
        assert startup_preflight.main(["--port", str(port)]) == startup_preflight.EXIT_AVAILABLE
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""


    @pytest.mark.parametrize(
        "value",
        ["", "0", "65536", "not-a-port", " 8001", "+8001", "8001.0", "８００１"],
    )
    def test_invalid_ports_fail_safely(
        value: str,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        assert startup_preflight.main(["--port", value]) == startup_preflight.EXIT_INVALID_PORT
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err.strip() == (
            "Cannot start SMCR Staff AI: SMCR_PORT must be a whole number from 1 through 65535."
        )


    def test_valid_port_boundaries() -> None:
        assert startup_preflight.parse_port("1") == 1
        assert startup_preflight.parse_port("65535") == 65_535
        assert startup_preflight.parse_port("08000") == 8_000

- [ ] **Step 2: Run the focused tests and confirm RED**

    uv run pytest tests/test_startup_preflight.py -q

Expected: collection fails because app.startup_preflight does not exist.

- [ ] **Step 3: Implement the preflight module**

Create app/startup_preflight.py:

    from __future__ import annotations

    import argparse
    import socket
    import sys
    from collections.abc import Sequence
    from pathlib import Path

    LOOPBACK_HOST = "127.0.0.1"
    CONNECT_TIMEOUT_SECONDS = 0.25
    EXIT_AVAILABLE = 0
    EXIT_OCCUPIED = 1
    EXIT_INVALID_PORT = 2
    _INVALID_PORT_MESSAGE = "SMCR_PORT must be a whole number from 1 through 65535."


    def parse_port(value: str) -> int:
        if not value.isascii() or not value.isdecimal():
            raise ValueError(_INVALID_PORT_MESSAGE)
        port = int(value, 10)
        if not 1 <= port <= 65_535:
            raise ValueError(_INVALID_PORT_MESSAGE)
        return port


    def is_loopback_port_accepting_connections(
        port: int,
        *,
        timeout: float = CONNECT_TIMEOUT_SECONDS,
    ) -> bool:
        try:
            with socket.create_connection((LOOPBACK_HOST, port), timeout=timeout):
                return True
        except OSError:
            return False


    def occupied_port_message(port: int, checkout: Path) -> str:
        return "\n".join(
            [
                f"Cannot start SMCR Staff AI: local port {port} is already in use.",
                f"Current checkout: {checkout.resolve()}",
                "Another SMCR Staff AI checkout may already be running.",
                "Stop the other instance, or choose another local port:",
                '  PowerShell: $env:SMCR_PORT="8001"; ./start.bat',
                "  Command Prompt: set SMCR_PORT=8001 && start.bat",
                "  macOS/Linux: SMCR_PORT=8001 ./start.sh",
            ]
        )


    def main(argv: Sequence[str] | None = None) -> int:
        parser = argparse.ArgumentParser(description="Check the local SMCR Staff AI startup port.")
        parser.add_argument("--port", required=True, metavar="PORT")
        args = parser.parse_args(argv)
        try:
            port = parse_port(str(args.port))
        except ValueError as exc:
            print(f"Cannot start SMCR Staff AI: {exc}", file=sys.stderr)
            return EXIT_INVALID_PORT
        if not is_loopback_port_accepting_connections(port):
            return EXIT_AVAILABLE
        print(occupied_port_message(port, Path.cwd()), file=sys.stderr)
        return EXIT_OCCUPIED


    if __name__ == "__main__":
        raise SystemExit(main())

- [ ] **Step 4: Run unit, type, and lint checks**

    uv run pytest tests/test_startup_preflight.py -q
    uv run mypy app/startup_preflight.py tests/test_startup_preflight.py
    uv run ruff check app/startup_preflight.py tests/test_startup_preflight.py

Expected: all commands pass.

- [ ] **Step 5: Wire SMCR_PORT through start.bat**

Add after cd:

    if not defined SMCR_PORT set "SMCR_PORT=8000"

After dependency sync:

    uv run python -m app.startup_preflight --port "%SMCR_PORT%"
    if errorlevel 1 exit /b 1

Replace the hard-coded launch lines with:

    echo Starting smcr-staff-ai at http://127.0.0.1:%SMCR_PORT%
    uv run uvicorn app.main:app --host 127.0.0.1 --port "%SMCR_PORT%" --reload

- [ ] **Step 6: Wire SMCR_PORT through start.sh**

Add after cd:

    SMCR_PORT="${SMCR_PORT:-8000}"

After dependency sync:

    if ! uv run python -m app.startup_preflight --port "$SMCR_PORT"; then
      exit 1
    fi

Replace the hard-coded launch lines with:

    echo "Starting smcr-staff-ai at http://127.0.0.1:${SMCR_PORT}"
    exec uv run uvicorn app.main:app --host 127.0.0.1 --port "$SMCR_PORT" --reload

- [ ] **Step 7: Add launcher contract tests**

Add:

    @pytest.mark.parametrize("script_name", ["start.bat", "start.sh"])
    def test_launchers_use_the_same_port_contract(script_name: str) -> None:
        script = Path(script_name).read_text(encoding="utf-8")
        assert "SMCR_PORT" in script
        assert "app.startup_preflight" in script
        assert "--host 127.0.0.1" in script
        assert "--port" in script

Manually execute the launcher with a known temporary listener during Task 5. The preflight unit tests own port detection; this source contract owns cross-shell argument consistency.

- [ ] **Step 8: Commit Task 2**

    git add app/startup_preflight.py tests/test_startup_preflight.py start.bat start.sh
    git commit -m "fix: explain startup port collisions"

---

### Task 3: Build the Multi-Column Text-Link Directory

**Files:**
- Modify: app/static/dashboard/index.html
- Modify: app/static/dashboard/dashboard.js
- Modify: app/static/dashboard/dashboard.css
- Modify: tests/test_dashboard.py
- Modify: tests/e2e/test_dashboard_flows.py

**Interfaces:**
- Adds state.goodLinks = { items: [], categories: {}, query: "", category: "" }.
- Produces goodLinkHostname(rawUrl), filterGoodLinks(items, query, category), renderGoodLinkItem(link), renderGoodLinksCategory(category, links), renderGoodLinks(), and populateGoodLinksCategorySelects(categories).
- Keeps loadGoodLinks() and initGoodLinksForm() as data-loading and mutation entry points.
- Separates personal items from built-in resources without duplication.

- [ ] **Step 1: Add failing HTML-shell assertions**

Add to test_dashboard_route_serves_html_shell:

    assert 'id="good-links-search"' in response.text
    assert 'id="good-links-filter-category"' in response.text
    assert 'id="good-links-my-section"' in response.text
    assert 'id="good-links-my-grid"' in response.text
    assert 'id="good-links-resource-grid"' in response.text
    assert 'id="good-links-state"' in response.text
    assert 'id="good-links-retry"' in response.text
    assert 'id="good-links-open-workspace"' in response.text
    assert 'id="good-links-action-status"' in response.text

Run the focused test and confirm RED.

- [ ] **Step 2: Replace the Links shell with one directory panel**

Use this structure in the Links section:

    <article class="panel full-span good-links-panel">
      <div class="good-links-header">
        <div>
          <h2>A Few Good Links</h2>
          <p>Open common staff resources quickly, or add a local unit link.</p>
        </div>
        <button type="button" class="secondary" id="good-links-open-add">Add link</button>
      </div>

      <div class="good-links-controls">
        <label>
          <span>Search links</span>
          <input id="good-links-search" type="search" autocomplete="off"
                 placeholder="Search by name, site, or purpose" />
        </label>
        <label>
          <span>Category</span>
          <select id="good-links-filter-category">
            <option value="">All categories</option>
          </select>
        </label>
        <button type="button" class="link-button" id="good-links-clear">Clear filters</button>
      </div>

      <details class="panel-drawer" id="good-links-add-drawer">
        <summary><span class="drawer-label">Add a local link</span></summary>
        <div class="panel-drawer-body">
          <form id="good-links-add-form" class="tool-form">
            <div class="form-row">
              <label><span>Link title</span><input name="title" required maxlength="80" /></label>
              <label><span>URL</span><input name="url" type="url" required maxlength="500" /></label>
            </div>
            <div class="form-row">
              <label><span>Short description</span><input name="description" maxlength="200" /></label>
              <label><span>Category</span><select name="category" id="good-links-category-select"></select></label>
            </div>
            <div class="button-row">
              <button type="submit">Save link</button>
              <button type="button" class="secondary" id="good-links-cancel">Cancel</button>
            </div>
            <p id="good-links-form-status" class="helper-text" aria-live="polite"></p>
          </form>
        </div>
      </details>

      <div id="good-links-state" role="status" aria-live="polite" aria-busy="true">
        <p>Loading links…</p>
        <button type="button" class="secondary is-hidden" id="good-links-retry">Retry</button>
        <button type="button" class="secondary is-hidden" id="good-links-open-workspace">
          Open Workspace
        </button>
      </div>
      <div id="good-links-results" class="is-hidden">
        <section id="good-links-my-section" aria-labelledby="good-links-my-heading">
          <h3 id="good-links-my-heading">My links</h3>
          <ul id="good-links-my-grid" class="good-links-personal-grid"></ul>
        </section>
        <section aria-labelledby="good-links-resources-heading">
          <div class="good-links-results-heading">
            <h3 id="good-links-resources-heading">All resources</h3>
            <span id="good-links-result-count" aria-live="polite"></span>
          </div>
          <div id="good-links-resource-grid" class="good-links-category-grid"></div>
        </section>
      </div>
      <p id="good-links-action-status" class="helper-text" aria-live="polite"></p>
    </article>

- [ ] **Step 3: Add failing directory and filter E2E tests**

Add this fixture constant:

    LINKS_RESPONSE = {
        "links": [
            {
                "id": "mol",
                "title": "Marine Online",
                "url": "https://www.mol.usmc.mil",
                "category": "admin_pay",
                "description": "Personnel and administrative access.",
                "is_seed": True,
                "tags": [],
            },
            {
                "id": "jko",
                "title": "Joint Knowledge Online",
                "url": "https://jko.jten.mil",
                "category": "training_pme",
                "description": "Joint distributed learning.",
                "is_seed": True,
                "tags": [],
            },
            {
                "id": "unit",
                "title": "Unit SharePoint",
                "url": "https://unit.example.test",
                "category": "unit",
                "description": "Local unit workspace.",
                "is_seed": False,
                "tags": [],
            },
        ],
        "total": 3,
        "categories": {
            "admin_pay": "Admin & pay",
            "training_pme": "Training & PME",
            "unit": "Unit-specific",
        },
    }

Add:

    @pytest.mark.e2e
    def test_links_directory_search_and_category_filter(browser_page: Any) -> None:
        page = browser_page
        page.route(
            "**/resource-links/**",
            lambda route: route.fulfill(status=200, json=LINKS_RESPONSE),
        )
        page.reload(wait_until="networkidle")
        page.locator("#tab-links").click()

        _expect(page.get_by_role("link", name=re.compile("Marine Online"))).to_be_visible()
        _expect(page.get_by_text("mol.usmc.mil", exact=True)).to_be_visible()
        _expect(
            page.locator("#good-links-my-grid").get_by_role(
                "link", name=re.compile("Unit SharePoint")
            )
        ).to_be_visible()

        page.locator("#good-links-search").fill("marine")
        _expect(page.get_by_role("link", name=re.compile("Marine Online"))).to_be_visible()
        _expect(page.get_by_role("link", name=re.compile("Joint Knowledge"))).to_be_hidden()

        page.locator("#good-links-search").fill("")
        page.locator("#good-links-filter-category").select_option("training_pme")
        _expect(page.get_by_role("link", name=re.compile("Joint Knowledge"))).to_be_visible()
        _expect(page.get_by_role("link", name=re.compile("Marine Online"))).to_be_hidden()

- [ ] **Step 4: Implement state, filtering, and semantic entries**

Add:

    goodLinks: {
      items: [],
      categories: {},
      query: "",
      category: "",
    },

    function goodLinkHostname(rawUrl) {
      try {
        return new URL(rawUrl).hostname.replace(/^www\./i, "") || "External site";
      } catch (_error) {
        return "External site";
      }
    }

    function filterGoodLinks(items, query, category) {
      const needle = query.trim().toLowerCase();
      return items.filter((link) => {
        if (category && link.category !== category) return false;
        if (!needle) return true;
        const searchable = [
          link.title,
          link.description,
          goodLinkHostname(link.url),
          state.goodLinks.categories[link.category],
          ...(Array.isArray(link.tags) ? link.tags : []),
        ].filter(Boolean).join(" ").toLowerCase();
        return searchable.includes(needle);
      });
    }

    function renderGoodLinkItem(link) {
      const hostname = goodLinkHostname(link.url);
      return '<li class="good-link-item">' +
        '<a class="good-link-anchor" href="' + escapeHtml(link.url) + '" target="_blank" ' +
        'rel="noopener noreferrer" aria-label="' + escapeHtml(link.title) + ' (opens in a new tab)">' +
        '<span class="good-link-name">' + escapeHtml(link.title) + '</span>' +
        '<span class="good-link-hostname">' + escapeHtml(hostname) + '</span>' +
        (link.description ? '<span class="good-link-description">' + escapeHtml(link.description) + '</span>' : '') +
        '</a>' +
        (link.is_seed ? '' : '<button type="button" class="link-button good-link-delete" ' +
          'data-link-id="' + escapeHtml(link.id) + '" aria-label="Remove ' + escapeHtml(link.title) + '">Remove</button>') +
        '</li>';
    }

    function renderGoodLinksCategory(category, links) {
      const label = state.goodLinks.categories[category] || category.replaceAll("_", " ");
      return '<section class="good-links-category" aria-labelledby="good-links-category-' +
        escapeHtml(category) + '">' +
        '<h4 id="good-links-category-' + escapeHtml(category) + '">' + escapeHtml(label) + '</h4>' +
        '<ul class="good-links-list">' + links.map(renderGoodLinkItem).join("") + '</ul>' +
        '</section>';
    }

    function renderGoodLinks() {
      const visible = filterGoodLinks(
        state.goodLinks.items,
        state.goodLinks.query,
        state.goodLinks.category,
      );
      const personal = visible.filter((link) => !link.is_seed);
      const resources = visible.filter((link) => link.is_seed);
      const personalSection = document.getElementById("good-links-my-section");
      const personalGrid = document.getElementById("good-links-my-grid");
      const resourceGrid = document.getElementById("good-links-resource-grid");
      const count = document.getElementById("good-links-result-count");

      personalSection.classList.toggle("is-hidden", personal.length === 0);
      personalGrid.innerHTML = personal.map(renderGoodLinkItem).join("");

      const grouped = {};
      for (const link of resources) {
        (grouped[link.category] ||= []).push(link);
      }
      resourceGrid.innerHTML = CATEGORY_ORDER
        .filter((category) => grouped[category]?.length)
        .map((category) => renderGoodLinksCategory(category, grouped[category]))
        .join("");
      count.textContent = visible.length + (visible.length === 1 ? " link" : " links");

      if (!visible.length) {
        resourceGrid.innerHTML =
          '<p class="good-links-no-results">No links match your search and category.</p>';
      }
    }

- [ ] **Step 5: Implement Search, category, Clear, Add, and Retry controls**

Add:

    function populateGoodLinksCategorySelects(categories) {
      const filterSelect = document.getElementById("good-links-filter-category");
      const addSelect = document.getElementById("good-links-category-select");
      const options = CATEGORY_ORDER
        .filter((category) => categories[category])
        .map((category) =>
          '<option value="' + escapeHtml(category) + '">' +
          escapeHtml(categories[category]) + '</option>',
        )
        .join("");
      filterSelect.innerHTML = '<option value="">All categories</option>' + options;
      filterSelect.value = state.goodLinks.category;
      addSelect.innerHTML = options;
      addSelect.value = "unit";
    }

    function initGoodLinksControls() {
      const search = document.getElementById("good-links-search");
      const category = document.getElementById("good-links-filter-category");
      const drawer = document.getElementById("good-links-add-drawer");
      search.addEventListener("input", () => {
        state.goodLinks.query = search.value;
        renderGoodLinks();
      });
      category.addEventListener("change", () => {
        state.goodLinks.category = category.value;
        renderGoodLinks();
      });
      document.getElementById("good-links-clear").addEventListener("click", () => {
        state.goodLinks.query = "";
        state.goodLinks.category = "";
        search.value = "";
        category.value = "";
        renderGoodLinks();
      });
      document.getElementById("good-links-open-add").addEventListener("click", () => {
        drawer.open = true;
        drawer.querySelector('input[name="title"]').focus();
      });
      document.getElementById("good-links-retry").addEventListener("click", loadGoodLinks);
      document.getElementById("good-links-open-workspace").addEventListener("click", () => {
        openLane("configure", "Opened Workspace settings.");
      });
    }

Call initGoodLinksControls() once beside initGoodLinksForm() during module initialization.

- [ ] **Step 6: Add ordinary-link and responsive CSS**

Add:

    .good-links-controls {
      display: grid;
      grid-template-columns: minmax(220px, 2fr) minmax(180px, 1fr) auto;
      align-items: end;
      gap: 12px;
      margin: 18px 0;
    }

    .good-links-category-grid,
    .good-links-personal-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px 24px;
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .good-links-category {
      min-width: 0;
      border-top: 1px solid var(--line);
      padding-top: 10px;
    }

    .good-links-list {
      margin: 0;
      padding: 0;
      list-style: none;
    }

    .good-link-item {
      min-width: 0;
      padding: 9px 0;
      border-bottom: 1px solid var(--line);
    }

    .good-link-anchor {
      display: grid;
      gap: 2px;
      color: var(--text);
      text-decoration: none;
    }

    .good-link-name {
      color: var(--accent);
      font-weight: 700;
      text-decoration: underline;
      text-underline-offset: 3px;
    }

    .good-link-hostname,
    .good-link-description {
      color: var(--muted);
      overflow-wrap: anywhere;
    }

    .good-link-hostname { font-size: 0.82rem; }
    .good-link-description { font-size: 0.9rem; }

    .layout,
    .panel,
    .command-grid,
    .strip,
    [data-section-group],
    .bullet-list,
    .bullet-list li {
      min-width: 0;
      overflow-wrap: anywhere;
    }

    @media (max-width: 1099px) {
      .good-links-category-grid,
      .good-links-personal-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
      }
    }

    @media (max-width: 699px) {
      .good-links-controls,
      .good-links-category-grid,
      .good-links-personal-grid {
        grid-template-columns: minmax(0, 1fr);
      }
    }

Remove the old ql chip styles and all inline quick-link layout declarations.

- [ ] **Step 7: Add 3/2/1 layout tests**

Add:

    @pytest.mark.e2e
    @pytest.mark.parametrize(
        ("width", "expected_columns"),
        [(1280, 3), (768, 2), (375, 1)],
    )
    def test_links_directory_reflows_without_page_overflow(
        browser_page: Any,
        width: int,
        expected_columns: int,
    ) -> None:
        page = browser_page
        page.route(
            "**/resource-links/**",
            lambda route: route.fulfill(status=200, json=LINKS_RESPONSE),
        )
        page.set_viewport_size({"width": width, "height": 800})
        page.reload(wait_until="networkidle")
        page.locator("#tab-links").click()
        columns = page.locator("#good-links-resource-grid").evaluate(
            """element => getComputedStyle(element).gridTemplateColumns
              .split(" ").filter(Boolean).length"""
        )
        assert columns == expected_columns
        assert page.evaluate(
            "document.documentElement.scrollWidth <= document.documentElement.clientWidth"
        )

- [ ] **Step 8: Run Task 3 tests and commit**

    uv run pytest tests/test_dashboard.py -q
    uv run pytest -m e2e tests/e2e/test_dashboard_flows.py -q
    git diff --check
    git add app/static/dashboard/index.html app/static/dashboard/dashboard.js app/static/dashboard/dashboard.css tests/test_dashboard.py tests/e2e/test_dashboard_flows.py
    git commit -m "feat: add responsive links directory"

---

### Task 4: Authenticate Links and Add Recoverable States

**Files:**
- Modify: app/static/dashboard/dashboard.js
- Modify: tests/e2e/test_dashboard_flows.py
- Create: tests/test_resource_links.py

**Interfaces:**
- setGoodLinksLoadState(kind, message) manages loading, ready, empty, and error.
- Every Links GET, POST, and DELETE passes auth: true.
- Save and remove feedback uses the Links live regions and preserves Search/category state.

- [ ] **Step 1: Add authenticated route tests**

Create tests/test_resource_links.py:

    from __future__ import annotations

    from collections.abc import Generator
    from pathlib import Path

    import pytest
    from fastapi.testclient import TestClient

    from app.core.config import get_settings
    from app.main import app


    @pytest.fixture
    def client(
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> Generator[TestClient, None, None]:
        monkeypatch.setenv("LOCAL_API_KEY", "links-secret")
        monkeypatch.setenv("RESOURCE_LINKS_STORAGE_DIR", str(tmp_path / "links"))
        get_settings.cache_clear()
        try:
            yield TestClient(app)
        finally:
            get_settings.cache_clear()


    def test_authenticated_resource_links_crud(client: TestClient) -> None:
        headers = {"X-Local-API-Key": "links-secret"}
        assert client.get("/resource-links/e2e-links").status_code == 401

        initial = client.get("/resource-links/e2e-links", headers=headers)
        assert initial.status_code == 200

        created = client.post(
            "/resource-links/e2e-links",
            headers=headers,
            json={
                "title": "Unit SharePoint",
                "url": "https://unit.example.test",
                "category": "unit",
                "description": "Local unit workspace.",
                "tags": [],
            },
        )
        assert created.status_code == 201
        assert created.json()["is_seed"] is False

        deleted = client.delete(
            f"/resource-links/e2e-links/{created.json()['id']}",
            headers=headers,
        )
        assert deleted.status_code == 204

- [ ] **Step 2: Add a failing frontend-header E2E test**

Add:

    @pytest.mark.e2e
    def test_links_requests_include_configured_passkey(browser_page: Any) -> None:
        page = browser_page
        captured_headers: list[dict[str, str]] = []
        personal_link = LINKS_RESPONSE["links"][2]

        def handle_links(route: Any) -> None:
            captured_headers.append(route.request.headers)
            if route.request.method == "GET":
                route.fulfill(status=200, json=LINKS_RESPONSE)
            elif route.request.method == "POST":
                route.fulfill(status=201, json=personal_link)
            else:
                route.fulfill(status=204)

        page.route("**/resource-links/**", handle_links)
        page.locator("#tab-configure").click()
        page.locator("#advanced-workspace-settings").evaluate(
            "(element) => { element.open = true; }"
        )
        page.locator("#api-key").fill("links-secret")
        page.locator("#apply-advanced-settings").click()
        page.locator("#tab-links").click()
        page.locator("#good-links-open-add").click()
        page.locator('#good-links-add-form input[name="title"]').fill("Unit SharePoint")
        page.locator('#good-links-add-form input[name="url"]').fill("https://unit.example.test")
        page.locator("#good-links-add-form button[type='submit']").click()
        page.get_by_role("button", name="Remove Unit SharePoint").click()

        assert captured_headers
        assert all(
            headers.get("x-local-api-key") == "links-secret"
            for headers in captured_headers
        )

Confirm RED before adding auth: true to the frontend calls.

- [ ] **Step 3: Authenticate all Links requests**

Use these options:

    await apiFetch("/resource-links/" + encodeURIComponent(state.userKey), { auth: true });

    await apiFetch("/resource-links/" + encodeURIComponent(state.userKey), {
      method: "POST",
      auth: true,
      body: JSON.stringify({ title, url, description, category, tags: [] }),
    });

    await apiFetch("/resource-links/" + encodeURIComponent(state.userKey) + "/" + encodeURIComponent(id), {
      method: "DELETE",
      auth: true,
    });

- [ ] **Step 4: Implement explicit load states**

Add:

    function setGoodLinksLoadState(kind, message = "") {
      const stateRegion = document.getElementById("good-links-state");
      const results = document.getElementById("good-links-results");
      const retry = document.getElementById("good-links-retry");
      const workspace = document.getElementById("good-links-open-workspace");
      stateRegion.dataset.state = kind;
      stateRegion.setAttribute("aria-busy", kind === "loading" ? "true" : "false");
      stateRegion.querySelector("p").textContent = message;
      stateRegion.classList.toggle("is-hidden", kind === "ready");
      results.classList.toggle("is-hidden", kind !== "ready");
      retry.classList.toggle("is-hidden", kind !== "error");
      workspace.classList.toggle("is-hidden", kind !== "empty");
    }

Refactor loadGoodLinks():

    async function loadGoodLinks() {
      if (!state.userKey) {
        setGoodLinksLoadState("empty", "Open a personal workspace to load links.");
        return;
      }
      setGoodLinksLoadState("loading", "Loading links…");
      try {
        const data = await apiFetch(
          "/resource-links/" + encodeURIComponent(state.userKey),
          { auth: true },
        );
        state.goodLinks.items = data.links || [];
        state.goodLinks.categories = data.categories || {};
        populateGoodLinksCategorySelects(state.goodLinks.categories);
        renderGoodLinks();
        setGoodLinksLoadState("ready");
      } catch (error) {
        console.error("Failed to load resource links", error);
        const message = error.status === 401
          ? "Could not load links. Check the workspace passkey in Workspace settings."
          : "Could not load links.";
        setGoodLinksLoadState("error", message);
      }
    }

- [ ] **Step 5: Make save and remove recoverable**

Add:

    function bindGoodLinkDeleteButtons() {
      for (const button of document.querySelectorAll(".good-link-delete")) {
        button.addEventListener("click", async () => {
          const status = document.getElementById("good-links-action-status");
          try {
            await apiFetch(
              "/resource-links/" + encodeURIComponent(state.userKey) + "/" +
                encodeURIComponent(button.dataset.linkId),
              { method: "DELETE", auth: true },
            );
            status.textContent = "Link removed.";
            await loadGoodLinks();
          } catch (error) {
            console.error("Failed to remove resource link", error);
            status.textContent = "Could not remove that link. Try again.";
          }
        });
      }
    }

Call bindGoodLinkDeleteButtons() at the end of renderGoodLinks() after the lists are inserted.

In the existing form submit handler use:

    const formStatus = document.getElementById("good-links-form-status");
    try {
      await apiFetch("/resource-links/" + encodeURIComponent(state.userKey), {
        method: "POST",
        auth: true,
        body: JSON.stringify({ title, url, description, category, tags: [] }),
      });
      formStatus.textContent = "Link saved.";
      drawer.open = false;
      form.reset();
      catSelect.value = "unit";
      await loadGoodLinks();
    } catch (error) {
      console.error("Failed to save resource link", error);
      formStatus.textContent = "Could not save that link. Check the values and try again.";
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Save link";
    }

Do not reset the form or close the drawer in the catch branch. loadGoodLinks() must not change state.goodLinks.query or state.goodLinks.category.

- [ ] **Step 6: Add route-driven state tests**

Add:

    @pytest.mark.e2e
    def test_links_load_error_can_retry(browser_page: Any) -> None:
        page = browser_page
        outcomes = ["error", "success"]

        def handle_links(route: Any) -> None:
            if outcomes.pop(0) == "error":
                route.fulfill(status=500, json={"detail": "expected failure"})
            else:
                route.fulfill(status=200, json=LINKS_RESPONSE)

        page.route("**/resource-links/**", handle_links)
        page.reload(wait_until="networkidle")
        page.locator("#tab-links").click()
        _expect(page.locator("#good-links-state")).to_contain_text("Could not load links")
        page.locator("#good-links-retry").click()
        _expect(page.get_by_role("link", name=re.compile("Marine Online"))).to_be_visible()

Extend the directory test to assert “No personal links yet” when the personal fixture is removed and “No links match your search and category” for an unmatched query. Add save/delete failure handlers returning 500; assert the save drawer retains its entered title and the delete target remains visible while the appropriate live region announces failure.

- [ ] **Step 7: Bump asset versions and remove obsolete code**

Replace 20260710a with 20260711a in the asset loader and actions.js import. Confirm renderQuickLinks, ql-filter-chip, ql-link-chip, and inline quick-link layout styles are absent.

- [ ] **Step 8: Run Task 4 tests and commit**

    uv run pytest tests/test_resource_links.py tests/test_dashboard.py -q
    uv run pytest -m e2e tests/e2e/test_dashboard_flows.py -q
    uv run mypy app tests
    uv run ruff check app tests
    git diff --check
    git add app/static/dashboard/index.html app/static/dashboard/dashboard.js tests/test_resource_links.py tests/e2e/test_dashboard_flows.py
    git commit -m "fix: make resource links recoverable and authenticated"

---

### Task 5: Full Verification, GitHub Publication, and Personal Pull

**Files:**
- Verify all branch changes in C:/smcr-staff-ai.
- Update C:/smcr-staff-ai-personal only after the published change is present on origin/main.

**Interfaces:**
- E2E base: SMCR_E2E_BASE_URL=http://127.0.0.1:8001.
- E2E data: temporary SMCR_STAFF_AI_HOME, not the shared personal root.
- Publication target: putnambrownejr/smcr-staff-ai main via the GitHub publish workflow.

- [ ] **Step 1: Run the full project matrix**

With the isolated project server on 8001:

    $env:SMCR_E2E_BASE_URL = "http://127.0.0.1:8001"
    uv run pytest tests/ -q
    uv run mypy app tests
    $trackedPython = @(git ls-files -- '*.py')
    uv run ruff check -- $trackedPython
    git diff --check

Expected: zero failures, errors, type issues, tracked-file lint issues, or whitespace issues.

- [ ] **Step 2: Perform visual browser QA**

At http://127.0.0.1:8001/dashboard verify normal startup has no false banner; Links Search/category/Add/Remove work; names look like hyperlinks rather than buttons; hostname and optional description are visible; layouts are 3/2/1 columns at 1280/768/375; compact view has no horizontal overflow; and focus is visible.

- [ ] **Step 3: Review branch scope**

    git status --short --branch
    git diff origin/main...HEAD --stat
    git log --oneline origin/main..HEAD

Expected: only the committed spec/plan, dashboard reliability/UI, startup preflight, launch scripts, and tests are present.

- [ ] **Step 4: Commit this plan**

    git add docs/superpowers/plans/2026-07-11-dashboard-links-reliability-implementation.md
    git commit -m "docs: plan dashboard links reliability implementation"

- [ ] **Step 5: Publish through GitHub**

Use the github:yeet workflow to push codex/dashboard-links-reliability, create a ready pull request against main, verify the remote patch, and wait for required checks. Merge with a merge commit, not a squash, only after checks pass so the tested local commits remain ancestors of origin/main. The user has explicitly authorized publication as the prerequisite for the personal update.

- [ ] **Step 6: Confirm origin/main contains the merge**

    git fetch --prune origin
    git merge-base --is-ancestor HEAD origin/main

Expected: exit 0 after the pull request merges.

- [ ] **Step 7: Pull the published result into the personal copy**

In C:/smcr-staff-ai-personal:

    git status --short --branch
    git fetch --prune origin
    git merge --no-edit origin/main
    git rev-list --left-right --count main...origin/main

Expected: untracked personal files remain untouched, merge succeeds, and the personal main is zero commits behind.

- [ ] **Step 8: Verify published assets in the personal runtime**

Reload only after the merge. Confirm the served dashboard.js uses asset version 20260711a, the Links directory matches the project behavior, and no temporary E2E data entered the personal state root.
