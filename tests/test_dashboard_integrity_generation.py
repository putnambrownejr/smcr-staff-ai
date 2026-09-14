from pathlib import Path
from runpy import run_path


def test_integrity_generation_is_repeatable() -> None:
    patch_integrity = run_path(str(Path("scripts/dashboard_integrity_patches.py").resolve()))["patch_integrity"]
    load_bundle = run_path(str(Path("scripts/patch_dashboard_bundle.py").resolve()))["load_bundle"]
    inner = load_bundle(Path("app/static/dashboard/index.html"))[3]
    regenerated = patch_integrity(inner)
    assert regenerated == inner
    assert patch_integrity(regenerated) == regenerated
    assert "static STAFF_LANE_BY_NAME =" in regenerated
    assert "static STAFF_LANES =" in regenerated


def test_method_replacement_preserves_following_static_fields() -> None:
    refresh = run_path(str(Path("scripts/dashboard_integrity_patches.py").resolve()))["refresh_methods"]
    source = 'class Component {\n  _apiHeaders(extra) {\n    return {};\n  }\n  static KEEP = { value: 42 };\n  componentDidMount() {\n  }\n}\n'
    assert "  static KEEP = { value: 42 };" in refresh(source)
