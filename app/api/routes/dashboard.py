from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter(tags=["dashboard"])
_DASHBOARD_HTML = Path(__file__).resolve().parents[2] / "static" / "dashboard" / "index.html"


@router.get("/dashboard", summary="Open the lightweight SMCR Staff AI dashboard")
def get_dashboard() -> FileResponse:
    return FileResponse(_DASHBOARD_HTML)
