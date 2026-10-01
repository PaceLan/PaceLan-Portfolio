from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ProductGrowthEvent:
    event_id: str
    date: str
    kind: str
    title: str
    description: str
    version: str = ""

    def __post_init__(self) -> None:
        if not self.event_id.strip():
            raise ValueError("event_id must not be empty")
        if not self.date.strip():
            raise ValueError("date must not be empty")
        if not self.kind.strip():
            raise ValueError("kind must not be empty")
        if not self.title.strip():
            raise ValueError("title must not be empty")
        if not self.description.strip():
            raise ValueError("description must not be empty")

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, object],
    ) -> "ProductGrowthEvent":
        return cls(
            event_id=str(payload["event_id"]),
            date=str(payload["date"]),
            kind=str(payload["kind"]),
            title=str(payload["title"]),
            description=str(payload["description"]),
            version=str(payload.get("version", "")),
        )


@dataclass(frozen=True)
class ProductHistory:
    _events: tuple[ProductGrowthEvent, ...] = ()

    def append(self, event: ProductGrowthEvent) -> "ProductHistory":
        events = tuple(
            item for item in self._events
            if item.event_id != event.event_id
        )
        return ProductHistory(events + (event,))

    def extend(
        self,
        events: Iterable[ProductGrowthEvent],
    ) -> "ProductHistory":
        history = self
        for event in events:
            history = history.append(event)
        return history

    def events(self) -> tuple[ProductGrowthEvent, ...]:
        return self._events

    @classmethod
    def from_events(
        cls,
        events: Iterable[ProductGrowthEvent],
    ) -> "ProductHistory":
        return cls().extend(events)

    def latest(self) -> ProductGrowthEvent | None:
        timeline = self.timeline()
        if not timeline:
            return None
        return timeline[-1]

    def events_for_version(
        self,
        version: str,
    ) -> tuple[ProductGrowthEvent, ...]:
        return tuple(
            event for event in self._events
            if event.version == version
        )

    def timeline(self) -> tuple[ProductGrowthEvent, ...]:
        return tuple(
            sorted(
                self._events,
                key=lambda event: (event.date, event.event_id),
            )
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "version": ProductHistoryStore.SCHEMA_VERSION,
            "events": [event.to_dict() for event in self._events],
        }

    @classmethod
    def from_dict(
        cls,
        payload: dict[str, object],
    ) -> "ProductHistory":
        events = payload.get("events", [])
        if not isinstance(events, list):
            raise ValueError("events must be a list")

        return cls(
            tuple(
                ProductGrowthEvent.from_dict(item)
                for item in events
                if isinstance(item, dict)
            )
        )


class ProductHistoryStore:
    """Persist PacePilot product-growth history independently from run history."""

    SCHEMA_VERSION = 1
    DEFAULT_FILENAME = "product_history.json"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> ProductHistory:
        if not self.path.exists():
            return ProductHistory()

        try:
            payload = json.loads(
                self.path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError, TypeError) as error:
            raise ValueError("invalid product history JSON") from error

        if not isinstance(payload, dict):
            raise ValueError("product history payload must be an object")

        version = payload.get("version")
        if version != self.SCHEMA_VERSION:
            raise ValueError("unsupported product history version")

        return ProductHistory.from_dict(payload)

    def save(self, history: ProductHistory) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                history.to_dict(),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )


def product_history_path(
    base_directory: str | Path,
) -> Path:
    return Path(base_directory) / ProductHistoryStore.DEFAULT_FILENAME



PRODUCT_GROWTH_EVENTS: tuple[ProductGrowthEvent, ...] = (
    ProductGrowthEvent(
        event_id="m16-final-integration",
        date="2026-09-28",
        kind="milestone",
        title="M16 final integration",
        description="Completed the final M16 integration through the execution readiness and decision chain.",
        version="M16",
    ),
    ProductGrowthEvent(
        event_id="m17-agent-context-planner",
        date="2026-09-28",
        kind="milestone",
        title="M17 agent context and planner boundaries",
        description="Locked the agent context integration and execution boundaries, planner context boundary, and planner ordering integrity.",
        version="M17",
    ),
    ProductGrowthEvent(
        event_id="m18-application-architecture",
        date="2026-09-29",
        kind="milestone",
        title="M18 application architecture",
        description="Locked the Application layer separating product UI concerns from Core architecture.",
        version="M18",
    ),
    ProductGrowthEvent(
        event_id="m19-visual-foundation",
        date="2026-09-29",
        kind="milestone",
        title="M19 visual foundation",
        description="Locked the visual tokens and reusable visual components forming the product visual foundation.",
        version="M19",
    ),
    ProductGrowthEvent(
        event_id="m20-workspace-ui",
        date="2026-09-29",
        kind="milestone",
        title="M20 workspace product UI",
        description="Locked the workspace visual product UI.",
        version="M20",
    ),
    ProductGrowthEvent(
        event_id="m21-agent-interaction-ui",
        date="2026-09-30",
        kind="milestone",
        title="M21 agent interaction UI",
        description="Locked the Agent Interaction UI for the product task and execution workflow.",
        version="M21",
    ),
    ProductGrowthEvent(
        event_id="m22-animation-visual-effects",
        date="2026-09-30",
        kind="milestone",
        title="M22 animation and visual effects",
        description="Locked the animation architecture and visual effects system.",
        version="M22",
    ),
    ProductGrowthEvent(
        event_id="m25-visual-system-runtime",
        date="2026-10-01",
        kind="milestone",
        title="M25 visual system and product runtime",
        description="Completed the M25 visual system and release integration, then locked the product runtime.",
        version="M25",
    ),
    ProductGrowthEvent(
        event_id="m26-2-global-ambient",
        date="2026-10-01",
        kind="milestone",
        title="M26.2 global ambient visual system",
        description="Locked the global ambient visual system.",
        version="M26.2",
    ),
    ProductGrowthEvent(
        event_id="m26-3-theme-day-night",
        date="2026-10-01",
        kind="milestone",
        title="M26.3 theme and day-night system",
        description="Locked theme state and day-night visual behavior.",
        version="M26.3",
    ),
    ProductGrowthEvent(
        event_id="m26-4-opening-experience",
        date="2026-10-01",
        kind="milestone",
        title="M26.4 opening experience",
        description="Locked the product opening experience.",
        version="M26.4",
    ),
    ProductGrowthEvent(
        event_id="m26-5-daily-greeting",
        date="2026-10-01",
        kind="milestone",
        title="M26.5 daily greeting system",
        description="Locked the deterministic daily greeting system.",
        version="M26.5",
    ),
    ProductGrowthEvent(
        event_id="m26-6-automatic-loading",
        date="2026-10-01",
        kind="milestone",
        title="M26.6 automatic loading",
        description="Locked automatic loading and startup orchestration.",
        version="M26.6",
    ),
    ProductGrowthEvent(
        event_id="m26-7-unified-transition",
        date="2026-10-02",
        kind="milestone",
        title="M26.7 unified transition system",
        description="Locked the unified transition system.",
        version="M26.7",
    ),
)


__all__ = [
    "ProductGrowthEvent",
    "PRODUCT_GROWTH_EVENTS",
    "ProductHistory",
    "ProductHistoryStore",
    "product_history_path",
]
