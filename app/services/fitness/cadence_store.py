from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.schemas.cadences import CadenceCreateRequest, CadenceRating, CadenceRecord

_BUILT_IN_CADENCES = (
    CadenceRecord(
        cadence_id="builtin-set-the-pace",
        title="Set the Pace",
        text=("Set the pace and hold the line\nStrong in body, sharp in mind\nEvery Marine, every time"),
        use="formation run",
        tempo="moderate",
        rating=CadenceRating.clean,
        built_in=True,
    ),
    CadenceRecord(
        cadence_id="builtin-reserve-ready",
        title="Reserve Ready",
        text=(
            "Miles may pass and months may turn\nWe stay ready, we still learn\n"
            "Train the skill and earn the trust\nReady when the nation must"
        ),
        use="formation run",
        tempo="moderate",
        rating=CadenceRating.clean,
        built_in=True,
    ),
    CadenceRecord(
        cadence_id="builtin-one-more-rep",
        title="One More Rep",
        text="One more rep, finish strong\nGood form first, then the pace\nDiscipline wins the race",
        use="circuit",
        tempo="fast",
        rating=CadenceRating.clean,
        built_in=True,
    ),
    CadenceRecord(
        cadence_id="builtin-standards-forward",
        title="Standards Forward",
        text=(
            "Standards forward, shoulders square\nLead with purpose everywhere\n"
            "Keep the faith and know the way\nBuild the Corps another day"
        ),
        use="marching or cooldown",
        tempo="steady",
        rating=CadenceRating.clean,
        built_in=True,
    ),
)

# This deliberately conservative boundary is a backstop, not a complete moderation system.
_PROHIBITED_PATTERNS = (
    r"\b(?:rape|raping|sexual assault)\b",
    r"\b(?:lynch|lynching)\b",
    r"\b(?:haze|hazing)\b",
    r"\bkill\s+(?:the\s+)?(?:weak|new|junior)\b",
    r"\b(?:racial|ethnic|religious)\s+slur\b",
)


class CadenceStore:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def list_records(self, user_key: str, *, include_adult: bool = False) -> list[CadenceRecord]:
        private = self._read(user_key)
        records = [*_BUILT_IN_CADENCES, *private]
        if not include_adult:
            records = [record for record in records if record.rating is CadenceRating.clean]
        return sorted(records, key=lambda item: (not item.built_in, item.title.lower()))

    def create(self, request: CadenceCreateRequest) -> CadenceRecord:
        self._validate_content(request.title, request.text)
        now = datetime.now(UTC)
        record = CadenceRecord(
            cadence_id=uuid4().hex,
            title=request.title.strip(),
            text=request.text.strip(),
            use=request.use.strip() or "unit PT",
            tempo=request.tempo.strip() or "moderate",
            rating=request.rating,
            created_at=now,
            updated_at=now,
        )
        records = self._read(request.user_key)
        records.append(record)
        self._write(request.user_key, records)
        return record

    def delete(self, user_key: str, cadence_id: str) -> bool:
        if cadence_id.startswith("builtin-"):
            return False
        records = self._read(user_key)
        remaining = [record for record in records if record.cadence_id != cadence_id]
        if len(remaining) == len(records):
            return False
        self._write(user_key, remaining)
        return True

    @staticmethod
    def _validate_content(title: str, text: str) -> None:
        candidate = f"{title}\n{text}".lower()
        if any(re.search(pattern, candidate) for pattern in _PROHIBITED_PATTERNS):
            raise ValueError(
                "Cadence rejected: adult content cannot include slurs, targeted harassment, hazing, "
                "sexual violence, or targeted degradation."
            )

    def _path(self, user_key: str) -> Path:
        digest = hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]
        return self.root / f"{digest}.json"

    def _read(self, user_key: str) -> list[CadenceRecord]:
        path = self._path(user_key)
        if not path.exists():
            return []
        payload = json.loads(path.read_text(encoding="utf-8"))
        return [CadenceRecord.model_validate(item) for item in payload.get("records", [])]

    def _write(self, user_key: str, records: list[CadenceRecord]) -> None:
        payload = {"records": [record.model_dump(mode="json") for record in records]}
        self._path(user_key).write_text(json.dumps(payload, indent=2), encoding="utf-8")
