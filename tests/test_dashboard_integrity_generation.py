from pathlib import Path
from runpy import run_path


def test_integrity_generation_is_repeatable() -> None:
    patch_integrity = run_path(str(Path("scripts/dashboard_integrity_patches.py").resolve()))["patch_integrity"]
    load_bundle = run_path(str(Path("scripts/patch_dashboard_bundle.py").resolve()))["load_bundle"]
    inner = load_bundle(Path("app/static/dashboard/index.html"))[3]
    regenerated = patch_integrity(inner)
    assert regenerated == inner
    assert patch_integrity(regenerated) == regenerated
