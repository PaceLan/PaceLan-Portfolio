from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)


@dataclass(frozen=True)
class DevelopmentHistoryDay:
    date: str
    modules: tuple[str, ...]
    summaries: tuple[str, ...]


class DevelopmentHistoryView:
    """Read-only date-oriented view over Development Tree nodes."""

    def __init__(self, nodes: tuple[DevelopmentTreeNode, ...]) -> None:
        if not isinstance(nodes, tuple):
            raise TypeError("nodes must be a tuple")
        if not all(isinstance(node, DevelopmentTreeNode) for node in nodes):
            raise TypeError("nodes must contain only DevelopmentTreeNode")
        self._nodes = nodes

    def for_date(self, date: str) -> DevelopmentHistoryDay:
        self._validate_date(date)
        nodes = self._nodes_for_date(date)
        return self._build_day(date, nodes)

    def recent(self, limit: int = 7) -> tuple[DevelopmentHistoryDay, ...]:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
            raise ValueError("limit must be a positive integer")

        dates = sorted(
            {
                date
                for node in self._nodes
                for date in self._node_dates(node)
            },
            reverse=True,
        )
        return tuple(
            self.for_date(date)
            for date in dates[:limit]
        )

    def _nodes_for_date(self, date: str) -> tuple[DevelopmentTreeNode, ...]:
        return tuple(
            node for node in self._nodes
            if date in self._node_dates(node)
            and node.node_type is DevelopmentNodeType.MODULE
        )

    @staticmethod
    def _node_dates(node: DevelopmentTreeNode) -> tuple[str, ...]:
        dates: list[str] = []
        for timestamp in (node.started_at, node.completed_at):
            if timestamp is not None:
                dates.append(
                    datetime.fromisoformat(
                        timestamp.replace("Z", "+00:00")
                    ).date().isoformat()
                )
        return tuple(dict.fromkeys(dates))

    @staticmethod
    def _build_day(
        date: str,
        nodes: tuple[DevelopmentTreeNode, ...],
    ) -> DevelopmentHistoryDay:
        modules = tuple(dict.fromkeys(node.node_key for node in nodes))
        summaries = tuple(
            dict.fromkeys(
                node.summary.strip()
                for node in nodes
                if node.summary.strip()
            )
        )
        return DevelopmentHistoryDay(
            date=date,
            modules=modules,
            summaries=summaries,
        )

    @staticmethod
    def _validate_date(date: str) -> None:
        if not isinstance(date, str) or not date.strip():
            raise ValueError("date must be a non-empty string")
        try:
            datetime.fromisoformat(date)
        except ValueError as exc:
            raise ValueError("date must be ISO-8601 YYYY-MM-DD") from exc


__all__ = [
    "DevelopmentHistoryDay",
    "DevelopmentHistoryView",
]
