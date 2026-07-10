from __future__ import annotations

import json
from dataclasses import dataclass
from typing import TypeVar

from pydantic import BaseModel, ValidationError

ScenarioModelT = TypeVar("ScenarioModelT", bound=BaseModel)
_CODE_FENCE = chr(96) * 3


@dataclass(frozen=True)
class ParsedScenarioEnvelope:
    answer: str
    scenario_output: dict[str, object]


class ScenarioEnvelopeValidationError(ValueError):
    def __init__(self, reason: str, *, answer: str | None = None) -> None:
        super().__init__(reason)
        self.reason = reason
        self.answer = answer


class ScenarioEnvelopeParser:
    def parse(
        self,
        content: str,
        *,
        output_model: type[ScenarioModelT],
        expected_role: str,
    ) -> ParsedScenarioEnvelope:
        raw = _strip_code_fence(content)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ScenarioEnvelopeValidationError("The external response was not valid JSON.") from exc
        if not isinstance(data, dict):
            raise ScenarioEnvelopeValidationError("The external response must be a JSON object.")

        answer_value = data.get("answer")
        answer = answer_value.strip() if isinstance(answer_value, str) else ""
        if not answer:
            raise ScenarioEnvelopeValidationError("The external response did not include a readable answer.")

        output_value = data.get("scenario_output")
        if not isinstance(output_value, dict):
            raise ScenarioEnvelopeValidationError(
                "The external response did not include a structured scenario_output object.",
                answer=answer,
            )
        try:
            output = output_model.model_validate(output_value)
        except ValidationError as exc:
            raise ScenarioEnvelopeValidationError(
                "The structured scenario output did not match the expected schema.",
                answer=answer,
            ) from exc

        dumped = output.model_dump()
        if dumped.get("role") != expected_role:
            raise ScenarioEnvelopeValidationError(
                f"The structured scenario output used the wrong role; expected {expected_role}.",
                answer=answer,
            )
        if not _contains_meaningful_content(dumped):
            raise ScenarioEnvelopeValidationError(
                "The structured scenario output was valid in shape but contained no assessment data.",
                answer=answer,
            )
        return ParsedScenarioEnvelope(answer=answer, scenario_output=dumped)


def build_envelope_template(template: str, output_model: type[BaseModel]) -> str:
    envelope_schema = {
        "type": "object",
        "required": ["answer", "scenario_output"],
        "additionalProperties": False,
        "properties": {
            "answer": {"type": "string", "minLength": 1},
            "scenario_output": output_model.model_json_schema(),
        },
    }
    return (
        f"{template}\n\n"
        "RESPONSE CONTRACT:\n"
        "Return exactly one JSON object matching this schema. The answer must be a readable "
        "assessment, and scenario_output must contain the same assessment as structured data.\n"
        f"{json.dumps(envelope_schema, indent=2)}"
    )


def _strip_code_fence(content: str) -> str:
    stripped = content.strip()
    if not stripped.startswith(_CODE_FENCE) or not stripped.endswith(_CODE_FENCE):
        return stripped
    lines = stripped.splitlines()
    if len(lines) < 3:
        return stripped
    return "\n".join(lines[1:-1]).strip()


def _contains_meaningful_content(value: object, *, key: str | None = None) -> bool:
    if key in {"role", "tempo"}:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_contains_meaningful_content(item) for item in value)
    if isinstance(value, dict):
        return any(_contains_meaningful_content(item, key=item_key) for item_key, item in value.items())
    return value is not None
