from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.core.auth import LocalApiKeyDependency

router = APIRouter(prefix="/git", tags=["git"], dependencies=[LocalApiKeyDependency])

_REPO_ROOT = Path(__file__).resolve().parents[3]


class GitPullResult(BaseModel):
    success: bool
    stdout: str
    stderr: str
    message: str


def _get_repo_root() -> Path:
    return _REPO_ROOT


@router.post("/pull", response_model=GitPullResult)
def git_pull(repo_root: Annotated[Path, Depends(_get_repo_root)]) -> GitPullResult:
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "pull", "--ff-only"],  # noqa: S607
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=30,
        )
        success = result.returncode == 0
        message = "Modules updated successfully." if success else "git pull failed — see output for details."
        return GitPullResult(
            success=success,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
            message=message,
        )
    except subprocess.TimeoutExpired:
        return GitPullResult(success=False, stdout="", stderr="", message="git pull timed out after 30 seconds.")
    except FileNotFoundError:
        return GitPullResult(success=False, stdout="", stderr="", message="git not found in PATH.")
