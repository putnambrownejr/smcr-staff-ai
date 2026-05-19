from pathlib import Path

from fastapi.testclient import TestClient

from app.api.routes.battle_rhythm import get_battle_rhythm_store
from app.main import app
from app.services.staff.battle_rhythm_store import BattleRhythmStore


def test_capture_battle_rhythm_from_planning_cell(tmp_path: Path) -> None:
    def override_store() -> BattleRhythmStore:
        return BattleRhythmStore(tmp_path / "battle-rhythm")

    app.dependency_overrides[get_battle_rhythm_store] = override_store
    client = TestClient(app)
    try:
        response = client.post(
            "/staff/battle-rhythm/capt-board/from-planning-cell",
            json={
                "title": "June drill planning cell",
                "supported_unit": "Civil affairs company",
                "supported_echelon": "company",
                "mission_or_training_goal": "Refine the next drill plan and keep the staff synchronized.",
                "commander_priorities": ["Protect training value", "Keep supportability honest"],
                "higher_guidance": ["One drill weekend only"],
                "coordinating_sections": ["S-3", "S-4", "S-6"],
                "support_requirements": ["Transport timeline", "Water plan"],
                "section_updates": [
                    {"section": "S-3", "summary": "The concept works if the company keeps one primary lane."},
                    {"section": "S-4", "summary": "Transport is supportable if we confirm the final timeline early."},
                ],
                "training_only": True,
            },
        )

        assert response.status_code == 200
        payload = response.json()
        assert payload["user_key"] == "capt-board"
        assert payload["board_title"] == "Planning cell package: June drill planning cell"
        assert payload["focus"]
        assert payload["assumption_log"]
        assert payload["due_out_board"]

        get_response = client.get("/staff/battle-rhythm/capt-board")
        assert get_response.status_code == 200
        stored = get_response.json()
        assert stored["board_title"] == "Planning cell package: June drill planning cell"
    finally:
        app.dependency_overrides.clear()
