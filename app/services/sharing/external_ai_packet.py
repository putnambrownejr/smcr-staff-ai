from __future__ import annotations

from app.schemas.calendar import DrillPrepPlanResponse
from app.schemas.opportunities import OpportunityRecord
from app.schemas.personal_documents import PersonalDocumentSummary
from app.schemas.session import UserSessionHandoff
from app.schemas.sharing import (
    ExternalAiPacketRequest,
    ExternalAiPacketResponse,
    ShareSafeActiveContext,
    ShareSafeDocumentSummary,
    ShareSafeDrillPlan,
    ShareSafeHandoff,
    ShareSafeOpportunity,
)
from app.schemas.user_context import ActiveUserContext


class ExternalAiPacketBuilder:
    def build(
        self,
        request: ExternalAiPacketRequest,
        *,
        handoff: UserSessionHandoff | None = None,
        active_user_context: ActiveUserContext | None = None,
        document_summary: PersonalDocumentSummary | None = None,
        drill_plans: list[DrillPrepPlanResponse] | None = None,
        opportunities: list[OpportunityRecord] | None = None,
    ) -> ExternalAiPacketResponse:
        warnings: list[str] = [
            "Share only the minimum context needed for the external AI task.",
            (
                "Do not share classified, CUI, COMSEC, keying material, real frequencies, "
                "call signs, exact movements, or unnecessary PII."
            ),
            (
                "This packet is scrubbed for external AI use, but the user still owns "
                "final disclosure judgment."
            ),
        ]
        withheld_categories: list[str] = []
        redacted_fields: list[str] = []
        safe_to_share = True

        share_handoff = sanitize_handoff(handoff) if request.include_handoff and handoff is not None else None
        if request.include_handoff and handoff is None:
            withheld_categories.append("handoff_missing")
        if handoff is not None:
            redacted_fields.extend(
                [
                    "handoff.display_name",
                    "handoff.rank",
                    "handoff.rqs_context_id",
                    "handoff.bio_context_id",
                    "handoff.preferences",
                    "handoff.career_opportunities",
                ]
            )

        share_active_context = (
            sanitize_active_user_context(active_user_context)
            if request.include_active_user_context and active_user_context is not None
            else None
        )
        if request.include_active_user_context and active_user_context is None:
            withheld_categories.append("active_user_context_missing")
        if active_user_context is not None:
            redacted_fields.append("active_user_context.preferences")
            warnings.append(
                "Unit and billet context can still be identifying. Keep or remove it "
                "based on what the external AI actually needs."
            )

        share_document_summary = (
            sanitize_document_summary(document_summary)
            if request.include_document_summary and document_summary is not None
            else None
        )
        if request.include_document_summary and document_summary is None:
            withheld_categories.append("document_summary_missing")
        if document_summary is not None:
            redacted_fields.extend(
                [
                    "document_summary.records",
                    "document_summary.context_ids",
                    "document_summary.filenames",
                    "document_text_previews",
                ]
            )
            if document_summary.pii_flagged_count:
                warnings.append(
                    "Local document inventory includes PII-flagged records. Do not share raw "
                    "document contents or filenames with external AI."
                )
                safe_to_share = False

        share_drill_plans = (
            [sanitize_drill_plan(item) for item in (drill_plans or [])]
            if request.include_drill_plans
            else []
        )
        if request.include_drill_plans:
            warnings.append(
                "Drill plans are share-safe summaries only. Exact key-event locations, "
                "uniforms, source context IDs, and notes are withheld."
            )
            redacted_fields.extend(
                [
                    "drill_plans.key_events",
                    "drill_plans.context_ids",
                    "drill_plans.exact_locations",
                    "drill_plans.uniform",
                    "drill_plans.notes",
                ]
            )

        share_opportunities = (
            [sanitize_opportunity(item) for item in (opportunities or [])]
            if request.include_opportunities
            else []
        )
        if request.include_opportunities:
            redacted_fields.extend(["opportunities.source_url", "opportunities.source_name", "opportunities.notes"])

        return ExternalAiPacketResponse(
            user_key=request.user_key,
            purpose=request.purpose,
            safe_to_share=safe_to_share,
            handoff=share_handoff,
            active_user_context=share_active_context,
            document_summary=share_document_summary,
            drill_plans=share_drill_plans,
            opportunities=share_opportunities,
            warnings=warnings,
            withheld_categories=sorted(dict.fromkeys(withheld_categories)),
            redacted_fields=sorted(dict.fromkeys(redacted_fields)),
            recommended_share_prompt=_recommended_prompt(request),
        )


def sanitize_handoff(handoff: UserSessionHandoff | None) -> ShareSafeHandoff | None:
    if handoff is None:
        return None
    return ShareSafeHandoff(
        mos=handoff.mos,
        billet=handoff.billet,
        unit_id=handoff.unit_id,
        pme=[
            {
                "program": item.program,
                "status": item.status,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "notes": item.notes,
            }
            for item in handoff.pme
        ],
        fitreps=[
            {
                "occasion": item.occasion,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "role": item.role,
                "notes": item.notes,
            }
            for item in handoff.fitreps
        ],
        drill_dates=[{"drill_date": item.drill_date, "label": item.label} for item in handoff.drill_dates],
        recurring_drill_notes=handoff.recurring_drill_notes,
        recurring_checks=[
            {
                "title": item.title,
                "cadence": item.cadence,
                "category": item.category,
                "due_offset_days": item.due_offset_days,
                "notes": item.notes,
            }
            for item in handoff.recurring_checks
        ],
        admin_watch_items=handoff.admin_watch_items,
        career_trends=[
            {
                "label": item.label,
                "direction": item.direction,
                "evidence": item.evidence,
                "recommended_action": item.recommended_action,
            }
            for item in handoff.career_trends
        ],
        recommended_books=handoff.recommended_books,
        recommended_courses=handoff.recommended_courses,
        warnings=[
            (
                "Display name, rank, linked local document IDs, preferences, and stored "
                "opportunity details were withheld."
            ),
        ],
    )


def sanitize_active_user_context(context: ActiveUserContext | None) -> ShareSafeActiveContext | None:
    if context is None:
        return None
    return ShareSafeActiveContext(
        unit_name=context.unit_name,
        unit_type=context.unit_type,
        unit_family=context.unit_family,
        billet_override=context.billet_override,
        mos_override=context.mos_override,
        current_focus=context.current_focus,
        staff_bias=context.staff_bias,
        temporary_notes=context.temporary_notes,
        expires_at=context.expires_at,
        warnings=[
            (
                "Preferences were withheld. Keep only the unit and billet detail an "
                "external AI actually needs."
            ),
        ],
    )


def sanitize_document_summary(summary: PersonalDocumentSummary | None) -> ShareSafeDocumentSummary | None:
    if summary is None:
        return None
    return ShareSafeDocumentSummary(
        total_documents=summary.total_documents,
        by_type=summary.by_type,
        pii_flagged_count=summary.pii_flagged_count,
        missing_recommended_types=summary.missing_recommended_types,
        review_due_count=summary.review_due_count,
        expired_count=summary.expired_count,
        warnings=[
            *summary.warnings,
            "Raw filenames, context IDs, and previews were withheld for external AI sharing.",
        ],
    )


def sanitize_drill_plan(plan: DrillPrepPlanResponse) -> ShareSafeDrillPlan:
    return ShareSafeDrillPlan(
        id=plan.id,
        drill_date=plan.drill_date,
        tasks=[
            {
                "title": item.title,
                "due_offset_days": item.due_offset_days,
                "due_date": item.due_date,
                "category": item.category,
                "advisory": item.advisory,
            }
            for item in plan.tasks
        ],
        warnings=[
            *plan.warnings,
            "Key-event locations, notes, uniforms, and local context IDs were withheld.",
        ],
    )


def sanitize_opportunity(opportunity: OpportunityRecord) -> ShareSafeOpportunity:
    return ShareSafeOpportunity(
        title=opportunity.title,
        opportunity_type=opportunity.opportunity_type.value,
        unit=opportunity.unit,
        location=opportunity.location,
        mos=opportunity.mos,
        rank=opportunity.rank,
        due_date=opportunity.due_date,
        warnings=opportunity.warnings,
    )


def _recommended_prompt(request: ExternalAiPacketRequest) -> str:
    purpose = request.purpose or "an advisory Reserve staff-planning task"
    return (
        "Use this share-safe packet as local context only. Treat it as advisory, "
        "not authoritative command guidance. "
        f"The user wants help with {purpose}. Do not infer hidden personal data, exact locations, "
        "or sensitive unit details."
    )
