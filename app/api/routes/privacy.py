from pathlib import Path

from fastapi import APIRouter

from app.core.auth import LocalApiKeyDependency
from app.schemas.privacy_review import RepoPrivacySweepRequest, RepoPrivacySweepResponse
from app.services.privacy.repo_privacy_sweeper import RepoPrivacySweeper

router = APIRouter(prefix="/privacy", tags=["privacy"], dependencies=[LocalApiKeyDependency])


@router.post("/pre-push-review", response_model=RepoPrivacySweepResponse)
def pre_push_privacy_review(request: RepoPrivacySweepRequest) -> RepoPrivacySweepResponse:
    repo_root = Path(request.repo_root) if request.repo_root else Path(__file__).resolve().parents[3]
    sweeper = RepoPrivacySweeper(repo_root)
    return sweeper.sweep(
        include_untracked=request.include_untracked,
        include_ignored_status=request.include_ignored_status,
    )
