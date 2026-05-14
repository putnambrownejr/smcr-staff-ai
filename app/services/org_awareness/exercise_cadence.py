import json
from pathlib import Path

from app.schemas.exercises import ExerciseCadence


def load_exercise_cadence(path: str | Path) -> list[ExerciseCadence]:
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)
    return [ExerciseCadence.model_validate(item) for item in payload["exercises"]]
