from __future__ import annotations

import re

from app.core.security import DEFAULT_WARNINGS, should_limit_to_generic_response
from app.schemas.analysis import TextAnalysisRequest, TextAnalysisResponse

ACTION_PATTERN = re.compile(
    r"\b("
    r"must|need to|should|coordinate|confirm|prepare|submit|review|update|schedule|complete|"
    r"draft|route|verify|send|pack|check|conduct|build|create|finalize|publish|notify"
    r")\b",
    re.IGNORECASE,
)
DUE_PATTERN = re.compile(
    r"\b("
    r"due|deadline|suspense|nlt|no later than|report by|submit by|complete by|"
    r"effective|by\s+\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?"
    r")\b",
    re.IGNORECASE,
)
BULLET_PREFIX = re.compile(r"^\s*(?:[-*•]+|\d+[.)])\s*")
WHITESPACE = re.compile(r"[ \t]+")
SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")

GENERIC_LIMITED_SUMMARY = [
    "Potentially sensitive content was detected, so the system is limiting output to generic handling guidance.",
    "Move detailed operational, classified, CUI, COMSEC, or personally identifying content into an approved workflow.",
]
GENERIC_LIMITED_CHECKLIST = [
    "Confirm the material belongs in an UNCLASSIFIED prototype before proceeding.",
    "Remove exact frequencies, call signs, movement details, keying material, and unnecessary PII.",
    "Restate the request in fictional, training-only, or generalized terms if drafting help is still needed.",
    "Have a qualified human reviewer validate any summary or task list before use.",
]


class TextAnalysisService:
    def analyze(self, request: TextAnalysisRequest) -> TextAnalysisResponse:
        normalized = _normalize_text(request.text)
        if should_limit_to_generic_response(normalized):
            return TextAnalysisResponse(
                title=request.title or "Sensitive Content Review",
                summary_points=GENERIC_LIMITED_SUMMARY,
                action_items=GENERIC_LIMITED_CHECKLIST[: request.max_action_items],
                due_outs=[],
                checklist=GENERIC_LIMITED_CHECKLIST if request.include_checklist else [],
                follow_up_questions=[
                    "Can you restate this with fictional or non-sensitive details only?"
                ][: request.max_follow_up_questions],
                warnings=list(DEFAULT_WARNINGS),
            )

        lines = _extract_lines(normalized)
        sentences = _extract_sentences(normalized)
        due_outs = _extract_due_outs(lines, request.max_action_items) if request.include_due_outs else []
        action_items = _extract_action_items(lines, request.max_action_items)
        checklist = _build_checklist(lines, action_items, request.max_action_items) if request.include_checklist else []
        summary_points = _build_summary(lines, sentences, action_items, due_outs, request.max_summary_points)
        follow_up_questions = _follow_up_questions(
            normalized,
            due_outs,
            action_items,
            request.focus,
            request.max_follow_up_questions,
        )
        return TextAnalysisResponse(
            title=request.title or _infer_title(lines, request.focus),
            summary_points=summary_points,
            action_items=action_items,
            due_outs=due_outs,
            checklist=checklist,
            follow_up_questions=follow_up_questions,
            warnings=list(DEFAULT_WARNINGS),
        )


def _normalize_text(text: str) -> str:
    lines = [WHITESPACE.sub(" ", line).strip() for line in text.replace("\r\n", "\n").split("\n")]
    return "\n".join(line for line in lines if line)


def _extract_lines(text: str) -> list[str]:
    return [_clean_item(line) for line in text.split("\n") if _clean_item(line)]


def _extract_sentences(text: str) -> list[str]:
    parts = [part.strip() for part in SENTENCE_SPLIT.split(text) if part.strip()]
    return [_clean_item(part) for part in parts if _clean_item(part)]


def _extract_due_outs(lines: list[str], limit: int) -> list[str]:
    matches: list[str] = []
    for line in lines:
        if DUE_PATTERN.search(line):
            matches.append(line)
    return _dedupe(matches)[:limit]


def _extract_action_items(lines: list[str], limit: int) -> list[str]:
    matches: list[str] = []
    for line in lines:
        if ACTION_PATTERN.search(line):
            matches.append(line)
            continue
        lowered = line.lower()
        if lowered.startswith(("to ", "ensure ", "follow up", "action:")):
            matches.append(line)
    return _dedupe(matches)[:limit]


def _build_checklist(lines: list[str], action_items: list[str], limit: int) -> list[str]:
    checklist = [line for line in lines if len(line.split()) <= 18]
    checklist.extend(action_items)
    return _dedupe(checklist)[:limit]


def _build_summary(
    lines: list[str],
    sentences: list[str],
    action_items: list[str],
    due_outs: list[str],
    limit: int,
) -> list[str]:
    candidates: list[str] = []
    action_set = set(action_items)
    due_set = set(due_outs)
    for sentence in sentences:
        if sentence in action_set or sentence in due_set:
            continue
        if len(sentence.split()) < 4:
            continue
        candidates.append(sentence)
    if not candidates:
        candidates = [line for line in lines if line not in action_set and line not in due_set]
    if not candidates:
        candidates = lines
    return _dedupe(candidates)[:limit]


def _follow_up_questions(
    text: str,
    due_outs: list[str],
    action_items: list[str],
    focus: str | None,
    limit: int,
) -> list[str]:
    questions: list[str] = []
    lowered = text.lower()
    if not due_outs:
        questions.append("What suspense date or milestone should be attached to these tasks?")
    if action_items and not re.search(r"\b(owner|assigned|responsible|oic|poc)\b", lowered):
        questions.append("Who owns each action item and who needs visibility?")
    if not re.search(r"\b(approve|approval|route|routing|signature)\b", lowered):
        questions.append("What approvals, routing steps, or signatures are still required?")
    if not re.search(r"\b(reference|ref|source|mco|mcdp|mcwp|maradmin|order)\b", lowered):
        questions.append("Which source document or official reference should be cited before using this output?")
    if focus:
        questions.append(f"What decision should this summary support for {focus}?")
    return questions[:limit]


def _infer_title(lines: list[str], focus: str | None) -> str:
    if focus:
        return f"{focus.title()} Summary"
    if lines:
        return f"Text Analysis: {lines[0][:60]}"
    return "Text Analysis"


def _clean_item(value: str) -> str:
    return BULLET_PREFIX.sub("", value).strip(" -")


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result
