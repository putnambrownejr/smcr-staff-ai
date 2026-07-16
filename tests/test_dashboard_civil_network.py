import json
from pathlib import Path
from typing import cast


def _dashboard_inner_html() -> str:
    html = Path("app/static/dashboard/index.html").read_text(encoding="utf-8")
    marker = '<script type="__bundler/template">'
    start = html.index(marker) + len(marker)
    end = html.rfind("</script>")
    return cast(str, json.loads(html[start:end].strip()))


def test_dashboard_has_data_first_civil_network_workspace() -> None:
    html = _dashboard_inner_html()

    assert 'id="civil-network-workspace"' in html
    assert "/civil-networks" in html
    assert "civilNetworkMap" in html
    assert "civil-network-agent-run" not in html
    assert "centrality" not in html.lower()
    assert "vulnerability score" not in html.lower()
    assert "public_role_holder" in html
    assert "Public role (required)" in html
    assert "Sourced relationships require a title and excerpt." in html
    assert "review_state: edge.review_state" in html
    assert "edge.review_state === civilNetworkFilters.review" in html
    for relationship_kind in (
        "coordination",
        "dependency",
        "influence",
        "information_flow",
        "authority_approval",
        "resource_support",
        "legitimacy_trust",
    ):
        assert relationship_kind in html
    assert "fetch(\"/civil-networks" in html
