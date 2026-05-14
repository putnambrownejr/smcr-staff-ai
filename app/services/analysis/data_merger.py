from __future__ import annotations

from difflib import SequenceMatcher

from app.core.security import DEFAULT_WARNINGS
from app.schemas.data_tools import DataMatchCandidate, DataMergeRequest, DataMergeResponse


class DataMergeService:
    def analyze(self, request: DataMergeRequest) -> DataMergeResponse:
        compare_fields = request.compare_fields or _infer_fields(request)
        candidates = _match_candidates(request, compare_fields, request.similarity_threshold)
        merged_rows = _merged_rows(request, candidates)
        return DataMergeResponse(
            summary_lines=[
                (
                    f"Compared {len(request.left_records)} left record(s) against "
                    f"{len(request.right_records)} right record(s)."
                ),
                f"Using fields: {', '.join(compare_fields) if compare_fields else 'all shared fields'}.",
                "Human validation is still required before treating similarity matches as authoritative merges.",
            ],
            merged_rows=merged_rows[: request.max_matches],
            match_candidates=candidates[: request.max_matches],
            warnings=[
                *DEFAULT_WARNINGS,
                "Data merge/commonality output is advisory only and should be validated before reuse.",
            ],
        )


def _infer_fields(request: DataMergeRequest) -> list[str]:
    left_fields = {field for record in request.left_records for field in record.fields}
    right_fields = {field for record in request.right_records for field in record.fields}
    return sorted(left_fields & right_fields)


def _match_candidates(
    request: DataMergeRequest,
    compare_fields: list[str],
    threshold: float,
) -> list[DataMatchCandidate]:
    matches: list[DataMatchCandidate] = []
    for left in request.left_records:
        for right in request.right_records:
            scores: list[float] = []
            matched_fields: list[str] = []
            for field in compare_fields:
                left_value = left.fields.get(field, "")
                right_value = right.fields.get(field, "")
                if not left_value and not right_value:
                    continue
                ratio = SequenceMatcher(None, left_value.lower(), right_value.lower()).ratio()
                scores.append(ratio)
                if ratio >= threshold:
                    matched_fields.append(field)
            if not scores:
                continue
            similarity = round(sum(scores) / len(scores), 3)
            if similarity < threshold:
                continue
            matches.append(
                DataMatchCandidate(
                    left_record_id=left.record_id,
                    right_record_id=right.record_id,
                    similarity=similarity,
                    matched_fields=matched_fields,
                    notes=_match_notes(left.fields, right.fields, matched_fields),
                )
            )
    return sorted(matches, key=lambda item: item.similarity, reverse=True)


def _match_notes(left_fields: dict[str, str], right_fields: dict[str, str], matched_fields: list[str]) -> list[str]:
    notes: list[str] = []
    for field in matched_fields:
        if left_fields.get(field) != right_fields.get(field):
            notes.append(f"{field} is similar but not identical across the two records.")
    return notes


def _merged_rows(request: DataMergeRequest, candidates: list[DataMatchCandidate]) -> list[dict[str, str]]:
    right_lookup = {record.record_id: record.fields for record in request.right_records}
    left_lookup = {record.record_id: record.fields for record in request.left_records}
    rows: list[dict[str, str]] = []
    for candidate in candidates:
        merged = {
            "left_record_id": candidate.left_record_id,
            "right_record_id": candidate.right_record_id,
            "similarity": str(candidate.similarity),
        }
        left_fields = left_lookup.get(candidate.left_record_id, {})
        right_fields = right_lookup.get(candidate.right_record_id, {})
        for key in sorted(set(left_fields) | set(right_fields)):
            merged[f"left.{key}"] = left_fields.get(key, "")
            merged[f"right.{key}"] = right_fields.get(key, "")
        rows.append(merged)
    return rows
