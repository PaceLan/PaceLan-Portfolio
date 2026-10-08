from __future__ import annotations

from dataclasses import dataclass

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentTreeNode,
)


@dataclass(frozen=True)
class ModuleProgress:
    module_key: str
    total_nodes: int
    completed_nodes: int
    progress_percent: float
    current_node: str | None
    remaining_nodes: tuple[str, ...]


class ModuleProgressView:
    """Read-only progress view for one development module."""

    def __init__(self, nodes: tuple[DevelopmentTreeNode, ...]) -> None:
        if not isinstance(nodes, tuple):
            raise TypeError("nodes must be a tuple")
        if not all(isinstance(node, DevelopmentTreeNode) for node in nodes):
            raise TypeError("nodes must contain only DevelopmentTreeNode")
        self._nodes = nodes

    def for_module(self, module_key: str) -> ModuleProgress:
        if not isinstance(module_key, str) or not module_key.strip():
            raise ValueError("module_key must be a non-empty string")

        prefix = module_key.strip()
        selected = tuple(
            node for node in self._nodes
            if node.node_key == prefix
            or node.node_key.startswith(prefix + ".")
        )

        completed = tuple(
            node for node in selected
            if node.status is DevelopmentNodeStatus.COMPLETED
        )
        remaining = tuple(
            node.node_key for node in selected
            if node.status is not DevelopmentNodeStatus.COMPLETED
        )

        current = next(
            (
                node.node_key
                for node in selected
                if node.status is DevelopmentNodeStatus.IN_PROGRESS
            ),
            None,
        )

        total = len(selected)
        completed_count = len(completed)

        return ModuleProgress(
            module_key=prefix,
            total_nodes=total,
            completed_nodes=completed_count,
            progress_percent=(
                completed_count * 100.0 / total if total else 0.0
            ),
            current_node=current,
            remaining_nodes=remaining,
        )


__all__ = ["ModuleProgress", "ModuleProgressView"]
