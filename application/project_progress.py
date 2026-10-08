from __future__ import annotations

from dataclasses import dataclass

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)


@dataclass(frozen=True)
class ProjectProgress:
    project_id: str
    total_modules: int
    completed_modules: int
    progress_percent: float
    current_module: str | None
    remaining_modules: tuple[str, ...]


class ProjectProgressView:
    """Read-only overall progress view for one project."""

    def __init__(self, nodes: tuple[DevelopmentTreeNode, ...]) -> None:
        if not isinstance(nodes, tuple):
            raise TypeError("nodes must be a tuple")
        if not all(isinstance(node, DevelopmentTreeNode) for node in nodes):
            raise TypeError("nodes must contain only DevelopmentTreeNode")
        self._nodes = nodes

    def for_project(self, project_id: str) -> ProjectProgress:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be a non-empty string")

        selected = tuple(
            node
            for node in self._nodes
            if node.project_id == project_id.strip()
            and node.node_type is DevelopmentNodeType.MODULE
        )

        completed = tuple(
            node
            for node in selected
            if node.status is DevelopmentNodeStatus.COMPLETED
        )

        current = next(
            (
                node.node_key
                for node in selected
                if node.status is DevelopmentNodeStatus.IN_PROGRESS
            ),
            None,
        )

        remaining = tuple(
            node.node_key
            for node in selected
            if node.status is not DevelopmentNodeStatus.COMPLETED
        )

        total = len(selected)
        completed_count = len(completed)

        return ProjectProgress(
            project_id=project_id.strip(),
            total_modules=total,
            completed_modules=completed_count,
            progress_percent=(
                completed_count * 100.0 / total if total else 0.0
            ),
            current_module=current,
            remaining_modules=remaining,
        )


__all__ = ["ProjectProgress", "ProjectProgressView"]
