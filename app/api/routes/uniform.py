from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.auth import LocalApiKeyDependency
from app.core.config import get_settings
from app.schemas.uniform_review import UniformPhotoReviewResponse
from app.services.agents.source_refs import UNIFORM_REFERENCES, source_trust_markers, structured_citations
from app.services.storage.local_context_store import LocalContextStore

router = APIRouter(prefix="/uniform", tags=["uniform"], dependencies=[LocalApiKeyDependency])


def get_context_store() -> Iterator[LocalContextStore]:
    settings = get_settings()
    yield LocalContextStore(settings.local_context_storage_dir, settings.max_upload_bytes)


@router.post("/photo-review", response_model=UniformPhotoReviewResponse)
async def review_uniform_photo(
    file: Annotated[UploadFile, File()],
    store: Annotated[LocalContextStore, Depends(get_context_store)],
    uniform_type: Annotated[str, Form()] = "unknown",
    event_context: Annotated[str | None, Form()] = None,
    visible_items: Annotated[str | None, Form()] = None,
    observed_concerns: Annotated[str | None, Form()] = None,
    local_guidance: Annotated[str | None, Form()] = None,
) -> UniformPhotoReviewResponse:
    if not (file.content_type or "").lower().startswith("image/"):
        raise HTTPException(status_code=400, detail="Uniform photo review requires an image upload.")
    content = await file.read(store.max_upload_bytes + 1)
    if len(content) > store.max_upload_bytes:
        raise HTTPException(status_code=413, detail=f"Upload exceeds the {store.max_upload_bytes}-byte limit.")
    try:
        item = store.save(
            filename=file.filename or "uniform_photo_upload",
            content=content,
            content_type=file.content_type or "application/octet-stream",
            document_type="uniform_photo",
            tags=["uniform", "photo", uniform_type.strip().lower().replace(" ", "_")],
            consent_ack=True,
        )
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    visible = _parse_csv_list(visible_items)
    concerns = _parse_lines(observed_concerns)
    guidance_lines = _parse_lines(local_guidance)

    review_lines = [
        "This is a photo-assisted advisory review, not automated visual detection.",
        f"Use the uploaded image to verify visible wear details against {UNIFORM_REFERENCES[0].title}.",
    ]
    if event_context:
        review_lines.append(f"Review is scoped to: {event_context.strip()}.")
    if guidance_lines:
        review_lines.append("Local command guidance or event-specific direction should override unresolved edge cases.")

    what_to_verify = _what_to_verify(uniform_type, visible, concerns)
    grooming_checks = _grooming_checks(visible)
    likely_issue_areas = _likely_issue_areas(uniform_type, visible, concerns)
    follow_up_actions = _follow_up_actions(guidance_lines, concerns, visible)

    warnings = [
        "Current backend workflow stores the photo locally but does not perform computer-vision insignia detection.",
        "Use this as a review framework and route ambiguous wear questions through the chain of command, SEL, or Uniform Board guidance.",
    ]
    if item.contains_pii:
        warnings.append("Photo metadata triggered a conservative PII warning; keep retention local and intentional.")

    return UniformPhotoReviewResponse(
        photo_context_id=item.context_id,
        filename=item.filename,
        uniform_type=uniform_type,
        event_context=event_context.strip() if event_context else None,
        visible_items=visible,
        review_posture="Photo-assisted uniform review",
        summary_lines=review_lines,
        what_to_verify_in_image=what_to_verify,
        grooming_checks=grooming_checks,
        likely_issue_areas=likely_issue_areas,
        follow_up_actions=follow_up_actions,
        warnings=warnings,
        structured_citations=structured_citations(UNIFORM_REFERENCES),
        source_trust=source_trust_markers(
            UNIFORM_REFERENCES,
            notes_prefix=(
                "Use the uploaded image only as local advisory context. Verify current uniform standards and any local command direction before acting."
            ),
        ),
    )


def _parse_csv_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _parse_lines(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _what_to_verify(uniform_type: str, visible: list[str], concerns: list[str]) -> list[str]:
    checks = [
        "Confirm the event uniform before judging fine-detail wear questions from the image.",
        "Use the photo to check serviceability, fit, symmetry, and obvious missing items first.",
    ]
    normalized = {item.lower() for item in visible}
    if "rank insignia" in normalized:
        checks.append("Verify visible rank insignia type, orientation, and placement for the stated uniform.")
    if "ribbons/badges" in normalized:
        checks.append("Verify ribbon, badge, or device alignment, spacing, precedence, and symmetry.")
    if "cover" in normalized:
        checks.append("Check that the cover is the right type for the uniform and sits cleanly with correct insignia placement.")
    if "belt/buckle" in normalized:
        checks.append("Check buckle centering and belt alignment.")
    if "footwear" in normalized:
        checks.append("Check visible footwear for color, condition, and whether the style matches the uniform.")
    lowered_uniform = uniform_type.lower()
    if "cammies" in lowered_uniform or "utility" in lowered_uniform:
        checks.append("Verify name tapes, blouse presentation, and obvious serviceability issues on the utility uniform.")
    if "dress" in lowered_uniform or "service" in lowered_uniform:
        checks.append("Check coat or shirt presentation, gig line, and the overall alignment of front-facing items.")
    checks.extend(f"Investigate user-noted concern from the image: {concern}" for concern in concerns[:3])
    return _unique(checks)


def _grooming_checks(visible: list[str]) -> list[str]:
    normalized = {item.lower() for item in visible}
    checks = ["If the face or hair is visible, verify haircut, shave, and overall grooming against current standards."]
    if "grooming/hair" in normalized:
        checks.append("Look for obvious bulk, sideburn, shave, or stray-hair issues visible in the uploaded image.")
    return _unique(checks)


def _likely_issue_areas(uniform_type: str, visible: list[str], concerns: list[str]) -> list[str]:
    issues = [
        "Wrong event uniform or local command variation not accounted for.",
        "Serviceability problems discovered too late instead of before formation.",
    ]
    normalized = {item.lower() for item in visible}
    if "ribbons/badges" in normalized or "rank insignia" in normalized:
        issues.append("Visible device placement or symmetry issue.")
    if "cover" in normalized:
        issues.append("Cover type, wear, or insignia mismatch.")
    if "grooming/hair" in normalized:
        issues.append("Grooming discrepancy visible in the photo.")
    if concerns:
        issues.extend(concerns[:3])
    if "pt" in uniform_type.lower():
        issues.append("Unit-specific PT uniform expectation may need local verification.")
    return _unique(issues)


def _follow_up_actions(guidance_lines: list[str], concerns: list[str], visible: list[str]) -> list[str]:
    actions = [
        "Compare the uploaded image against the current MCO 1020.34H standard before the event day.",
        "If anything still looks ambiguous, route the question through the chain of command or SEL early.",
    ]
    if guidance_lines:
        actions.append("Reconcile the photo review with local command or event guidance before final wear decisions.")
    if concerns:
        actions.append("Fix the user-noted concern, then retake a quick confirmation photo if needed.")
    if visible:
        actions.append("Use the image as a pre-drill prep check, not as the sole decision authority.")
    return _unique(actions)


def _unique(items: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered
