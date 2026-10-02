from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ProductGrowthEvent:
    event_id: str
    date: str
    version: str
    module: str
    category: str
    title: str
    added: str = ""
    changed: str = ""
    fixed: str = ""
    notes: str = ""

    def __post_init__(self) -> None:
        for field_name in (
            "event_id",
            "date",
            "version",
            "module",
            "category",
            "title",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must not be empty")

    @property
    def description(self) -> str:
        parts = [
            value.strip()
            for value in (self.added, self.changed, self.fixed, self.notes)
            if value.strip()
        ]
        return " ".join(parts)

    def to_dict(self) -> dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> "ProductGrowthEvent":
        if not isinstance(payload, dict):
            raise ValueError("product growth event must be an object")

        required_fields = (
            "event_id",
            "date",
            "version",
            "module",
            "category",
            "title",
        )

        missing = [
            field_name
            for field_name in required_fields
            if field_name not in payload
        ]
        if missing:
            raise ValueError(
                "missing product growth event fields: "
                + ", ".join(missing)
            )

        return cls(
            event_id=payload["event_id"],
            date=payload["date"],
            version=payload["version"],
            module=payload["module"],
            category=payload["category"],
            title=payload["title"],
            added=payload.get("added", ""),
            changed=payload.get("changed", ""),
            fixed=payload.get("fixed", ""),
            notes=payload.get("notes", ""),
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
        return timeline[-1] if timeline else None

    def events_for_version(
        self,
        version: str,
    ) -> tuple[ProductGrowthEvent, ...]:
        return tuple(
            event for event in self._events
            if event.version == version
        )

    def events_for_module(
        self,
        module: str,
    ) -> tuple[ProductGrowthEvent, ...]:
        return tuple(
            event for event in self._events
            if event.module == module
        )

    def timeline(self) -> tuple[ProductGrowthEvent, ...]:
        return tuple(
            sorted(
                self._events,
                key=lambda event: (event.date, event.event_id),
            )
        )

    def summary(self) -> str:
        timeline = self.timeline()
        if not timeline:
            return "PacePilot has no recorded product growth yet."

        latest = timeline[-1]
        versions = tuple(dict.fromkeys(event.version for event in timeline))
        return (
            f"PacePilot has recorded {len(timeline)} product milestones "
            f"across {len(versions)} versions. "
            f"The latest recorded milestone is {latest.title} ({latest.version}), "
            f"dated {latest.date}."
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
        if not isinstance(payload, dict):
            raise ValueError("product history payload must be an object")

        events = payload.get("events", [])
        if not isinstance(events, list):
            raise ValueError("events must be a list")

        return cls(
            tuple(
                ProductGrowthEvent.from_dict(item)
                for item in events
            )
        )


class ProductHistoryStore:
    """Persist product-growth history independently from operation history."""

    SCHEMA_VERSION = 2
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

        if payload.get("version") != self.SCHEMA_VERSION:
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
        "m16-final-integration",
        "2026-09-28",
        "M16",
        "M16",
        "execution",
        "M16 final integration",
        added="Completed the final execution readiness and decision chain integration.",
        notes="Locked through M16.10.3.",
    ),
    ProductGrowthEvent(
        "m17-agent-context-planner",
        "2026-09-28",
        "M17",
        "M17",
        "agent architecture",
        "M17 agent context and planner boundaries",
        added="Integrated agent context and planner boundaries.",
        changed="Established execution and planner ordering integrity.",
        notes="Locked through M17.4.",
    ),
    ProductGrowthEvent(
        "m18-application-architecture",
        "2026-09-29",
        "M18",
        "M18",
        "architecture",
        "M18 application architecture",
        added="Introduced the Application layer between product UI and Core.",
        notes="Application architecture locked.",
    ),
    ProductGrowthEvent(
        "m19-visual-foundation",
        "2026-09-29",
        "M19",
        "M19",
        "visual system",
        "M19 visual foundation",
        added="Established visual tokens and reusable visual components.",
        notes="M19.2 and M19.3 locked.",
    ),
    ProductGrowthEvent(
        "m20-workspace-ui",
        "2026-09-29",
        "M20",
        "M20",
        "workspace UI",
        "M20 workspace product UI",
        added="Established the workspace visual product UI.",
        notes="Workspace UI locked.",
    ),
    ProductGrowthEvent(
        "m21-agent-interaction-ui",
        "2026-09-30",
        "M21",
        "M21",
        "agent interaction",
        "M21 Agent Interaction UI",
        added="Established the Agent Interaction UI and task-to-result workflow presentation.",
        notes="Agent Interaction UI locked.",
    ),
    ProductGrowthEvent(
        "m22-animation-visual-effects",
        "2026-09-30",
        "M22",
        "M22",
        "animation",
        "M22 animation and visual effects",
        added="Established animation architecture and visual effects.",
        notes="M22.1 and M22 final integration locked.",
    ),
    ProductGrowthEvent(
        "m25-visual-system-runtime",
        "2026-10-01",
        "M25",
        "M25",
        "runtime",
        "M25 visual system and product runtime",
        added="Completed visual system and release integration.",
        changed="Finalized product runtime behavior.",
        notes="M25 locked.",
    ),
    ProductGrowthEvent(
        "m26-2-global-ambient",
        "2026-10-01",
        "M26.2",
        "M26",
        "ambient visuals",
        "M26.2 global ambient visual system",
        added="Established the global ambient visual system.",
    ),
    ProductGrowthEvent(
        "m26-3-theme-day-night",
        "2026-10-01",
        "M26.3",
        "M26",
        "theme",
        "M26.3 theme and day-night system",
        added="Established theme state and day/night visual behavior.",
    ),
    ProductGrowthEvent(
        "m26-4-opening-experience",
        "2026-10-01",
        "M26.4",
        "M26",
        "opening experience",
        "M26.4 opening experience",
        added="Established the product opening experience.",
    ),
    ProductGrowthEvent(
        "m26-5-daily-greeting",
        "2026-10-01",
        "M26.5",
        "M26",
        "daily greeting",
        "M26.5 daily greeting system",
        added="Established deterministic daily greeting behavior.",
    ),
    ProductGrowthEvent(
        "m26-6-automatic-loading",
        "2026-10-01",
        "M26.6",
        "M26",
        "startup",
        "M26.6 automatic loading",
        added="Established automatic loading and startup orchestration.",
    ),
    ProductGrowthEvent(
        "m26-7-unified-transition",
        "2026-10-02",
        "M26.7",
        "M26",
        "transitions",
        "M26.7 unified transition system",
        added="Established the unified transition system.",
    ),
)


__all__ = [
    "ProductGrowthEvent",
    "PRODUCT_GROWTH_EVENTS",
    "ProductHistory",
    "ProductHistoryStore",
    "product_history_path",
]
