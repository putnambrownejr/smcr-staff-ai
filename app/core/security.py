import re

SENSITIVE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\b(classified|secret|top secret|ts/sci|noforn|cui)\b", re.IGNORECASE),
    re.compile(r"\b(comsec|keymat|crypto key|fill device|skl|kik|kek)\b", re.IGNORECASE),
    re.compile(r"\b(freq(?:uency)?|mhz|khz)\s*[:=]?\s*\d{2,5}(?:\.\d+)?\b", re.IGNORECASE),
    re.compile(r"\b(call ?sign|current movement|convoy route|grid coordinate|mgrs)\b", re.IGNORECASE),
)

# Detection and redaction share this table so preview redaction stays aligned with PII flags.
PII_REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED-SSN]"),
    (re.compile(r"\b(?:ssn|social security)\b", re.IGNORECASE), "[REDACTED-SSN]"),
    (
        re.compile(r"\b(?:dob|date of birth)\b(?:\s*[:=]?\s*\d{1,2}[/-]\d{1,2}[/-]\d{2,4})?", re.IGNORECASE),
        "[REDACTED-DOB]",
    ),
    (
        re.compile(
            r"\b(?:phone|mobile|cell)\s*[:=]?\s*(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
            re.IGNORECASE,
        ),
        "[REDACTED-PHONE]",
    ),
    (re.compile(r"\b\d{5}-\d{4}\b"), "[REDACTED-ZIP]"),
    (re.compile(r"(?:zip\s*(?:code)?\s*[:=]?\s*)\d{5}\b", re.IGNORECASE), "[REDACTED-ZIP]"),
)
PII_PATTERNS: tuple[re.Pattern[str], ...] = tuple(pattern for pattern, _replacement in PII_REDACTION_PATTERNS)

DEFAULT_WARNINGS = [
    (
        "UNCLASSIFIED prototype: do not submit classified, CUI, secrets, PII, COMSEC, keying material, "
        "real frequencies, or sensitive operational details."
    ),
    "Outputs are advisory drafts for human review and are not official Marine Corps guidance.",
]


def detect_sensitive_input(text: str) -> list[str]:
    warnings: list[str] = []
    for pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            warnings.append(
                "Potentially classified, controlled, or operationally sensitive content detected. "
                "The system will only provide generic training checklists and safety guidance."
            )
            break
    if detect_pii_input(text):
        warnings.append(
            "Potential PII detected. Keep only the minimum required local context, avoid sharing this with "
            "external providers, and redact before using in prompts."
        )
    return warnings


def should_limit_to_generic_response(text: str) -> bool:
    return bool(detect_sensitive_input(text))


def detect_pii_input(text: str) -> bool:
    return any(pattern.search(text) for pattern in PII_PATTERNS)


def redact_pii(text: str) -> str:
    redacted = text
    for pattern, replacement in PII_REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted
