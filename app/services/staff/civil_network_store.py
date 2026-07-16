from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

from app.schemas.civil_network import CivilNetwork, CivilNetworkSnapshot
from app.services.session.handoff_store import is_valid_user_key


class CivilNetworkStore:
    """Owner-scoped storage for event-specific civil-network records and snapshots."""

    def __init__(self, storage_dir: str | Path) -> None:
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def create(self, user_key: str, network: CivilNetwork) -> CivilNetwork:
        self._require_user_key(user_key)
        if self._path(user_key, network.id).exists():
            raise ValueError("Civil network already exists.")
        return self.save(user_key, network)

    def get(self, user_key: str, network_id: str) -> CivilNetwork:
        self._require_user_key(user_key)
        path = self._path(user_key, network_id)
        if not path.exists():
            raise KeyError(network_id)
        return CivilNetwork.model_validate_json(path.read_text(encoding="utf-8"))

    def save(self, user_key: str, network: CivilNetwork) -> CivilNetwork:
        self._require_user_key(user_key)
        path = self._path(user_key, network.id)
        existing_snapshots: list[CivilNetworkSnapshot] = []
        if path.exists():
            existing = CivilNetwork.model_validate_json(path.read_text(encoding="utf-8"))
            existing_snapshots = existing.snapshots
        supplied_snapshot_ids = {snapshot.snapshot_id for snapshot in network.snapshots}
        retained_snapshots = [
            snapshot for snapshot in existing_snapshots if snapshot.snapshot_id not in supplied_snapshot_ids
        ]
        saved = network.model_copy(
            update={
                "updated_at": datetime.now(UTC),
                "snapshots": [*retained_snapshots, *network.snapshots],
            },
            deep=True,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(saved.model_dump_json(indent=2), encoding="utf-8")
        return saved

    def list(self, user_key: str) -> list[CivilNetwork]:
        if not is_valid_user_key(user_key):
            return []
        user_dir = self._user_dir(user_key)
        if not user_dir.exists():
            return []
        networks: list[CivilNetwork] = []
        for path in user_dir.glob("*.json"):
            try:
                networks.append(CivilNetwork.model_validate_json(path.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
        return sorted(networks, key=lambda network: network.updated_at, reverse=True)

    def delete(self, user_key: str, network_id: str) -> bool:
        if not is_valid_user_key(user_key):
            return False
        path = self._path(user_key, network_id)
        if not path.exists():
            return False
        path.unlink()
        user_dir = path.parent
        if not any(user_dir.iterdir()):
            user_dir.rmdir()
        return True

    def snapshot(self, user_key: str, network_id: str, label: str) -> CivilNetworkSnapshot:
        network = self.get(user_key, network_id)
        snapshot_network = network.model_copy(update={"snapshots": []}, deep=True)
        snapshot = CivilNetworkSnapshot(label=label, network=snapshot_network)
        network.snapshots.append(snapshot)
        self.save(user_key, network)
        return snapshot

    @staticmethod
    def user_key_digest(user_key: str) -> str:
        return hashlib.sha256(user_key.encode("utf-8")).hexdigest()[:24]

    def _user_dir(self, user_key: str) -> Path:
        return self.storage_dir / self.user_key_digest(user_key)

    def _path(self, user_key: str, network_id: str) -> Path:
        if not network_id or any(part in network_id for part in ("/", "\\", "..")):
            raise ValueError("Invalid civil-network id.")
        return self._user_dir(user_key) / f"{network_id}.json"

    @staticmethod
    def _require_user_key(user_key: str) -> None:
        if not is_valid_user_key(user_key):
            raise ValueError("Invalid user_key.")
