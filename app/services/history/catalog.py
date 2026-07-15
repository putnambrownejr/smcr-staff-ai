from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_SEED_DIR = _REPO_ROOT / "data" / "seed"

BUNDLED_HISTORY_PATHS = (
    _SEED_DIR / "usmc_history_on_this_day.example.yaml",
    _SEED_DIR / "us_military_history_on_this_day.example.yaml",
)
