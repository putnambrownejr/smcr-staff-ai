import json
from pathlib import Path
from typing import cast


def _dashboard_inner_html() -> str:
    html = Path("app/static/dashboard/index.html").read_text(encoding="utf-8")
    marker = '<script type="__bundler/template">'
    start = html.index(marker) + len(marker)
    end = html.rfind("</script>")
    return cast(str, json.loads(html[start:end].strip()))


def test_dashboard_civil_network_brick_removed_from_bench_files() -> None:
    # The Civil Network / Nodal Analysis brick was pulled out of Bench/Files at
    # the user's request; the capability stays available through the
    # actor-network agent and the /civil-networks API (backend untouched).
    html = _dashboard_inner_html()

    assert 'id="civil-network-workspace"' not in html
    assert "Civil Network / Nodal Analysis" not in html
    assert "Public organization, service, forum, group, or role-holder" not in html
