from __future__ import annotations

from pathlib import Path

import yaml

from app.schemas.product_templates import ProductTemplateRecord


class SystemTemplateCatalog:
    def __init__(self, records: list[ProductTemplateRecord]) -> None:
        self.records = records

    @classmethod
    def from_yaml(cls, path: str | Path) -> SystemTemplateCatalog:
        with open(path, encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        records = [ProductTemplateRecord.model_validate(item) for item in payload.get("templates", [])]
        return cls(records)

    def list(self) -> list[ProductTemplateRecord]:
        return list(self.records)
