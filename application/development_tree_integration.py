from __future__ import annotations

from dataclasses import dataclass

from application.development_tree import DevelopmentTreeNode
from application.history import AgentHistoryEntry


@dataclass(frozen=True)
class DevelopmentTreeIntegration:
    node: DevelopmentTreeNode
    history: AgentHistoryEntry | None
    progress_status: str
    verification_status: str | None


class DevelopmentTreeIntegrationView:
    """Read-only linkage between Tree nodes and existing History records."""

    def __init__(
        self,
        nodes: tuple[DevelopmentTreeNode, ...],
        history: tuple[AgentHistoryEntry, ...] = (),
    ) -> None:
        if not isinstance(nodes, tuple):
            raise TypeError("nodes must be a tuple")
        if not all(isinstance(node, DevelopmentTreeNode) for node in nodes):
            raise TypeError("nodes must contain only DevelopmentTreeNode")
        if not isinstance(history, tuple):
            raise TypeError("history must be a tuple")
        if not all(isinstance(entry, AgentHistoryEntry) for entry in history):
            raise TypeError("history must contain only AgentHistoryEntry")

        self._nodes = nodes
        self._history = history

    def all(self) -> tuple[DevelopmentTreeIntegration, ...]:
        return tuple(self._build(node) for node in self._nodes)

    def for_node(self, node_id: str) -> DevelopmentTreeIntegration:
        if not isinstance(node_id, str) or not node_id.strip():
            raise ValueError("node_id must be a non-empty string")

        for node in self._nodes:
            if node.node_id == node_id.strip():
                return self._build(node)

        raise KeyError(f"Unknown node_id: {node_id}")

    def for_task(self, task_id: str) -> tuple[DevelopmentTreeIntegration, ...]:
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")
        return tuple(
            self._build(node)
            for node in self._nodes
            if node.task_id == task_id.strip()
        )

    def for_history(
        self,
        history_id: str,
    ) -> tuple[DevelopmentTreeIntegration, ...]:
        if not isinstance(history_id, str) or not history_id.strip():
            raise ValueError("history_id must be a non-empty string")
        return tuple(
            self._build(node)
            for node in self._nodes
            if node.history_id == history_id.strip()
        )

    def _build(self, node: DevelopmentTreeNode) -> DevelopmentTreeIntegration:
        entry = next(
            (
                item
                for item in self._history
                if item.history_id == node.history_id
            ),
            None,
        )
        return DevelopmentTreeIntegration(
            node=node,
            history=entry,
            progress_status=node.status.value,
            verification_status=(
                entry.verification_status if entry is not None else None
            ),
        )


__all__ = [
    "DevelopmentTreeIntegration",
    "DevelopmentTreeIntegrationView",
]
