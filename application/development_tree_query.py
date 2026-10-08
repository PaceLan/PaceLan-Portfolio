from __future__ import annotations

from datetime import datetime

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentTreeNode,
)


class DevelopmentTreeQuery:
    """Read-only query service for Development Tree nodes."""

    def __init__(self, nodes: tuple[DevelopmentTreeNode, ...]) -> None:
        if not isinstance(nodes, tuple):
            raise TypeError("nodes must be a tuple")
        if not all(isinstance(node, DevelopmentTreeNode) for node in nodes):
            raise TypeError("nodes must contain only DevelopmentTreeNode")
        self._nodes = nodes

    def by_date(self, date: str) -> tuple[DevelopmentTreeNode, ...]:
        self._validate_date(date)
        return tuple(
            node
            for node in self._nodes
            if date in self._node_dates(node)
        )

    def by_module(self, module_key: str) -> tuple[DevelopmentTreeNode, ...]:
        self._validate_text(module_key, "module_key")
        key = module_key.strip()
        return tuple(
            node
            for node in self._nodes
            if node.node_key == key
            or node.node_key.startswith(key + ".")
        )

    def by_project(self, project_id: str) -> tuple[DevelopmentTreeNode, ...]:
        self._validate_text(project_id, "project_id")
        project = project_id.strip()
        return tuple(
            node for node in self._nodes
            if node.project_id == project
        )

    def in_progress(self) -> tuple[DevelopmentTreeNode, ...]:
        return self._by_status(DevelopmentNodeStatus.IN_PROGRESS)

    def completed(self) -> tuple[DevelopmentTreeNode, ...]:
        return self._by_status(DevelopmentNodeStatus.COMPLETED)

    def blocked(self) -> tuple[DevelopmentTreeNode, ...]:
        return self._by_status(DevelopmentNodeStatus.BLOCKED)

    def remaining(self) -> tuple[DevelopmentTreeNode, ...]:
        return tuple(
            node
            for node in self._nodes
            if node.status not in {
                DevelopmentNodeStatus.COMPLETED,
                DevelopmentNodeStatus.CANCELLED,
            }
        )

    def _by_status(
        self,
        status: DevelopmentNodeStatus,
    ) -> tuple[DevelopmentTreeNode, ...]:
        return tuple(node for node in self._nodes if node.status is status)

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
    def _validate_text(value: str, name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")

    @staticmethod
    def _validate_date(date: str) -> None:
        DevelopmentTreeQuery._validate_text(date, "date")
        try:
            parsed = datetime.fromisoformat(date)
        except ValueError as exc:
            raise ValueError("date must be ISO-8601") from exc
        if parsed.date().isoformat() != date:
            raise ValueError("date must be ISO-8601 YYYY-MM-DD")

    __all__ = ["DevelopmentTreeQuery"]
