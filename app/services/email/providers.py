"""STUB: Search user-approved email providers for advisory workflow inputs. Not yet connected."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class EmailItem:
    subject: str
    sender: str
    received_at: datetime
    snippet: str
    source_id: str


class EmailProvider(ABC):
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> list[EmailItem]:
        # TODO: implement
        raise NotImplementedError


class EmailProviderStub(EmailProvider):
    def search(self, query: str, limit: int = 10) -> list[EmailItem]:
        # TODO: implement
        raise NotImplementedError("Email integration is planned; no live mailbox access is enabled.")
