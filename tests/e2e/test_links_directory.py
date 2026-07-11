import re
from typing import Any

import pytest

LINK_CATEGORIES: dict[str, str] = {
    "usmc_official": "USMC official",
    "admin_pay": "Admin & pay",
    "training_pme": "Training & PME",
    "benefits": "Benefits",
    "reference": "Reference",
    "unit": "Unit-specific",
}

LINKS: list[dict[str, Any]] = [
    {
        "id": "seed-mol",
        "title": "Marine Online",
        "url": "https://www.mol.usmc.mil/",
        "category": "admin_pay",
        "description": "Personnel and administrative services.",
        "is_seed": True,
        "tags": ["marine", "admin"],
    },
    {
        "id": "seed-jko",
        "title": "Joint Knowledge Online",
        "url": "https://jkodirect.jten.mil/",
        "category": "training_pme",
        "description": "Joint training and professional military education.",
        "is_seed": True,
        "tags": ["training"],
    },
    {
        "id": "seed-pubs",
        "title": "Marine Corps Publications",
        "url": "https://www.marines.mil/News/Publications/",
        "category": "reference",
        "description": "Official Marine Corps publications.",
        "is_seed": True,
        "tags": ["doctrine"],
    },
    {
        "id": "seed-benefits",
        "title": "Military OneSource Benefits and Support for Reserve Component Families",
        "url": "https://military-family-readiness-resources-and-support.example.mil/portal/reserve-component-families",
        "category": "benefits",
        "description": None,
        "is_seed": True,
        "tags": ["support"],
    },
    {
        "id": "personal-unit",
        "title": "Unit SharePoint",
        "url": "https://unit.example.mil/sites/staff",
        "category": "unit",
        "description": "Working files for the unit staff.",
        "is_seed": False,
        "tags": [],
    },
]


def _expect(locator: Any) -> Any:
    from playwright.sync_api import expect

    return expect(locator)


def _links_response(links: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    items = LINKS if links is None else links
    return {"links": items, "total": len(items), "categories": LINK_CATEGORIES}


def _open_personal_workspace(page: Any, api_key: str = "") -> None:
    page.locator("#tab-configure").click()
    page.locator("#advanced-workspace-settings").evaluate("element => { element.open = true; }")
    page.locator("#custom-profile-key").fill("links-e2e")
    page.locator("#api-key").fill(api_key)
    page.locator("#apply-advanced-settings").click()
    page.locator("#tab-links").click()


@pytest.mark.e2e
def test_links_render_as_searchable_semantic_directory_with_auth(browser_page: Any) -> None:
    page = browser_page
    request_headers: list[dict[str, str]] = []

    def handle_links(route: Any) -> None:
        request_headers.append(route.request.headers)
        route.fulfill(status=200, content_type="application/json", json=_links_response())

    page.route("**/resource-links/**", handle_links)
    _open_personal_workspace(page, api_key="links-secret")

    _expect(page.locator(".command-panel > .panel-header")).to_be_hidden()
    _expect(page.locator(".command-grid")).to_be_hidden()
    _expect(page.locator(".command-panel > .quick-actions")).to_be_hidden()
    _expect(page.get_by_role("heading", name="My links")).to_be_visible()
    _expect(page.get_by_role("heading", name="All resources")).to_be_visible()
    _expect(page.locator("#good-links-results-summary")).to_have_text("4 links shown")
    _expect(page.get_by_role("link", name=re.compile("Unit SharePoint"))).to_be_visible()
    _expect(page.get_by_text("unit.example.mil", exact=True)).to_be_visible()
    _expect(page.get_by_text("Personnel and administrative services.", exact=True)).to_be_visible()
    no_description_item = page.get_by_role("link", name=re.compile("Military OneSource")).locator("xpath=..")
    _expect(no_description_item.locator(".good-link-description")).to_have_count(0)
    _expect(page.get_by_role("link", name=re.compile("Unit SharePoint"))).to_have_count(1)
    _expect(page.locator("#good-links-my-grid > li")).to_have_count(1)
    _expect(page.locator("#good-links-resource-grid a")).to_have_count(4)
    assert request_headers
    assert all(headers["x-local-api-key"] == "links-secret" for headers in request_headers)

    personal_urls = set(page.locator("#good-links-my-grid a").evaluate_all("links => links.map(link => link.href)"))
    resource_urls = set(page.locator("#good-links-resource-grid a").evaluate_all("links => links.map(link => link.href)"))
    expected_personal_urls = {link["url"] for link in LINKS if not link["is_seed"]}
    expected_resource_urls = {link["url"] for link in LINKS if link["is_seed"]}
    assert personal_urls == expected_personal_urls
    assert resource_urls == expected_resource_urls
    all_urls = page.locator("#good-links-results a").evaluate_all("links => links.map(link => link.href)")
    assert len(all_urls) == len(set(all_urls)) == len(LINKS)

    _expect(page.locator("#good-links-resource-grid .good-links-category")).to_have_count(4)
    for category_name in ("Admin & pay", "Training & PME", "Benefits", "Reference"):
        category = page.locator(".good-links-category").filter(has=page.get_by_role("heading", name=category_name))
        _expect(category).to_have_count(1)
        _expect(category.locator("ul > li")).to_have_count(1)

    page.locator("#good-links-search").fill("marine online")
    _expect(page.get_by_role("link", name=re.compile("Marine Online"))).to_be_visible()
    _expect(page.get_by_role("link", name=re.compile("Joint Knowledge Online"))).to_be_hidden()

    page.locator("#good-links-clear-filters").click()
    _expect(page.get_by_role("link", name=re.compile("Joint Knowledge Online"))).to_be_visible()

    page.locator("#good-links-filter-category").select_option("training_pme")
    _expect(page.get_by_role("link", name=re.compile("Joint Knowledge Online"))).to_be_visible()
    _expect(page.get_by_role("link", name=re.compile("Marine Online"))).to_be_hidden()

    page.locator("#good-links-search").fill("no-such-dashboard-link")
    _expect(page.locator("#good-links-resource-empty")).to_contain_text("No links match")


@pytest.mark.e2e
def test_links_directory_uses_three_two_one_columns_without_page_overflow(browser_page: Any) -> None:
    page = browser_page
    page.route(
        "**/resource-links/**",
        lambda route: route.fulfill(status=200, content_type="application/json", json=_links_response()),
    )
    page.reload(wait_until="networkidle")
    page.locator("#tab-links").click()
    _expect(page.locator("#good-links-resource-grid .good-links-category").first).to_be_visible()

    for width, expected_columns in ((1280, 3), (900, 2), (500, 1), (375, 1), (320, 1)):
        page.set_viewport_size({"width": width, "height": 800})
        columns = page.locator("#good-links-resource-grid").evaluate(
            """element => getComputedStyle(element).gridTemplateColumns.split(" ").filter(Boolean).length"""
        )
        assert columns == expected_columns
        overflow = page.evaluate(
            """() => ({
              clientWidth: document.documentElement.clientWidth,
              scrollWidth: document.documentElement.scrollWidth,
              offenders: [...document.querySelectorAll("body *")]
                .filter(element => element.getBoundingClientRect().right > document.documentElement.clientWidth + 1)
                .slice(0, 8)
                .map(element => ({
                  id: element.id,
                  className: typeof element.className === "string" ? element.className : "",
                  right: Math.round(element.getBoundingClientRect().right),
                })),
            })"""
        )
        assert overflow["scrollWidth"] <= overflow["clientWidth"], f"{width}px overflow: {overflow}"


@pytest.mark.e2e
def test_links_load_error_can_retry(browser_page: Any) -> None:
    page = browser_page
    attempts = 0

    def handle_links(route: Any) -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            route.fulfill(status=500, content_type="application/json", json={"detail": "test failure"})
            return
        route.fulfill(status=200, content_type="application/json", json=_links_response())

    page.route("**/resource-links/**", handle_links)
    page.reload(wait_until="networkidle")
    page.locator("#tab-links").click()

    _expect(page.locator("#good-links-state")).to_contain_text("Could not load links")
    _expect(page.locator("#good-links-retry")).to_be_visible()
    page.locator("#good-links-retry").focus()
    page.keyboard.press("Enter")

    _expect(page.get_by_role("link", name=re.compile("Marine Online"))).to_be_visible()
    _expect(page.locator("#good-links-state")).to_be_hidden()
    _expect(page.locator("#good-links-search")).to_be_focused()


@pytest.mark.e2e
def test_links_auth_error_routes_to_workspace_settings(browser_page: Any) -> None:
    page = browser_page
    page.route(
        "**/resource-links/**",
        lambda route: route.fulfill(status=401, content_type="application/json", json={"detail": "Unauthorized"}),
    )
    page.reload(wait_until="networkidle")
    page.locator("#tab-links").click()

    _expect(page.locator("#good-links-state")).to_contain_text("passkey")
    _expect(page.locator("#good-links-open-workspace")).to_be_visible()
    page.locator("#good-links-open-workspace").click()
    _expect(page.locator("#tab-configure")).to_have_attribute("aria-selected", "true")


@pytest.mark.e2e
def test_links_failed_mutations_preserve_user_input_and_entries(browser_page: Any) -> None:
    page = browser_page
    mutations: list[tuple[str, dict[str, str]]] = []

    def handle_links(route: Any) -> None:
        if route.request.method == "GET":
            route.fulfill(status=200, content_type="application/json", json=_links_response())
            return
        mutations.append((route.request.method, route.request.headers))
        route.fulfill(status=500, content_type="application/json", json={"detail": "test failure"})

    page.route("**/resource-links/**", handle_links)
    _open_personal_workspace(page, api_key="links-secret")
    _expect(page.get_by_role("link", name=re.compile("Unit SharePoint"))).to_be_visible()

    drawer = page.locator("#good-links-add-drawer")
    drawer.locator("> summary").click()
    _expect(drawer).to_have_attribute("open", "")
    page.keyboard.press("Tab")
    _expect(page.locator("#good-links-add-form input[name='title']")).to_be_focused()
    page.locator("#good-links-add-form input[name='title']").fill("Squadron portal")
    page.locator("#good-links-add-form input[name='url']").fill("https://portal.example.mil/")
    page.locator("#good-links-add-form button[type='submit']").click()

    _expect(drawer).to_have_attribute("open", "")
    _expect(page.locator("#good-links-add-form input[name='title']")).to_have_value("Squadron portal")
    _expect(page.locator("#good-links-form-status")).to_contain_text(re.compile("could not save", re.I))

    page.get_by_role("button", name="Remove Unit SharePoint").click()
    _expect(page.get_by_role("link", name=re.compile("Unit SharePoint"))).to_be_visible()
    _expect(page.locator("#good-links-action-status")).to_contain_text(re.compile("could not remove", re.I))
    assert [method for method, _headers in mutations] == ["POST", "DELETE"]
    assert all(headers["x-local-api-key"] == "links-secret" for _method, headers in mutations)


@pytest.mark.e2e
def test_links_empty_and_no_workspace_states_are_actionable(browser_page: Any) -> None:
    page = browser_page
    page.route(
        "**/resource-links/**",
        lambda route: route.fulfill(status=200, content_type="application/json", json=_links_response([])),
    )
    page.reload(wait_until="networkidle")
    page.locator("#tab-links").click()

    _expect(page.locator("#good-links-results")).to_be_visible()
    _expect(page.locator("#good-links-my-empty")).to_have_text("No personal links yet.")
    _expect(page.locator("#good-links-resource-empty")).to_have_text("No resource links are available.")
    _expect(page.locator("#good-links-resource-grid .good-links-category")).to_have_count(0)

    page.locator("#tab-configure").click()
    page.locator("#load-demo").click()
    page.locator("#tab-links").click()

    _expect(page.locator("#good-links-state")).to_contain_text("Open a personal workspace")
    _expect(page.locator("#good-links-open-workspace")).to_be_visible()
    _expect(page.locator("#good-links-add-drawer")).to_be_hidden()
    page.locator("#good-links-open-workspace").click()
    _expect(page.locator("#tab-configure")).to_have_attribute("aria-selected", "true")


@pytest.mark.e2e
def test_links_successful_mutations_preserve_filters_and_reset_form(browser_page: Any) -> None:
    page = browser_page
    mutations: list[tuple[str, dict[str, str]]] = []

    def handle_links(route: Any) -> None:
        if route.request.method == "GET":
            route.fulfill(status=200, content_type="application/json", json=_links_response())
            return
        mutations.append((route.request.method, route.request.headers))
        if route.request.method == "POST":
            body = route.request.post_data_json
            route.fulfill(
                status=201,
                content_type="application/json",
                json={"id": "personal-new", "is_seed": False, **body},
            )
            return
        route.fulfill(status=204)

    page.route("**/resource-links/**", handle_links)
    _open_personal_workspace(page, api_key="links-secret")
    _expect(page.get_by_role("link", name=re.compile("Unit SharePoint"))).to_be_visible()

    page.locator("#good-links-search").fill("portal")
    page.locator("#good-links-filter-category").select_option("unit")
    drawer = page.locator("#good-links-add-drawer")
    drawer.locator("> summary").click()
    page.locator("#good-links-add-form input[name='title']").fill("Squadron portal")
    page.locator("#good-links-add-form input[name='url']").fill("https://portal.example.mil/")
    page.locator("#good-links-add-form input[name='description']").fill("Shared squadron workspace")
    page.locator("#good-links-add-form button[type='submit']").click()

    _expect(drawer).not_to_have_attribute("open", "")
    _expect(page.get_by_role("link", name=re.compile("Squadron portal"))).to_be_visible()
    _expect(page.locator("#good-links-action-status")).to_have_text("Squadron portal saved.")
    _expect(page.locator("#good-links-search")).to_have_value("portal")
    _expect(page.locator("#good-links-filter-category")).to_have_value("unit")

    drawer.locator("> summary").click()
    _expect(page.locator("#good-links-category-select")).to_have_value("unit")
    drawer.locator("> summary").click()
    page.get_by_role("button", name="Remove Squadron portal").click()

    _expect(page.get_by_role("link", name=re.compile("Squadron portal"))).to_be_hidden()
    _expect(page.locator("#good-links-action-status")).to_have_text("Squadron portal removed.")
    _expect(page.locator("#good-links-my-heading")).to_be_focused()
    _expect(page.locator("#good-links-search")).to_have_value("portal")
    _expect(page.locator("#good-links-filter-category")).to_have_value("unit")
    assert [method for method, _headers in mutations] == ["POST", "DELETE"]
    assert all(headers["x-local-api-key"] == "links-secret" for _method, headers in mutations)
