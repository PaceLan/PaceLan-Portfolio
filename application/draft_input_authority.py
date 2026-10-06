from __future__ import annotations

from dataclasses import dataclass
from dataclasses import dataclass
from enum import Enum


class DraftInputKind(str, Enum):
    IDEA = "idea"
    DRAFT = "draft"


@dataclass(frozen=True)
class DraftInput:
    content: str
    kind: DraftInputKind = DraftInputKind.DRAFT
    source: str = "local"

    def __post_init__(self) -> None:
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("draft input content must not be empty")
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("draft input source must not be empty")


class DraftInputAuthority:
    """Boundary for non-authoritative development input."""

    def accept(
        self,
        content: str,
        *,
        kind: DraftInputKind = DraftInputKind.DRAFT,
        source: str = "local",
    ) -> DraftInput:
        return DraftInput(
            content=content.strip(),
            kind=kind,
            source=source.strip(),
        )

    @staticmethod
    def can_enter_formal_execution(_: DraftInput) -> bool:
        return False

    @staticmethod
    def requires_goal_confirmation(_: DraftInput) -> bool:
        return True
