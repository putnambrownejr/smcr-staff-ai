from __future__ import annotations

import importlib.util
from pathlib import Path

_LAUNCHER_PATH = Path(__file__).resolve().parents[1] / "scripts" / "_smcr_launch_lib.py"
_SPEC = importlib.util.spec_from_file_location("smcr_launch_lib", _LAUNCHER_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_LAUNCHER = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_LAUNCHER)


def test_launcher_urls_use_shared_dashboard_origin_and_direct_health_loopback() -> None:
    assert _LAUNCHER.dashboard_url(8123) == "http://localhost:8123/dashboard"
    assert _LAUNCHER.health_url(8123) == "http://127.0.0.1:8123/health"
