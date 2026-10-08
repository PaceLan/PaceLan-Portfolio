from __future__ import annotations

import json
import os
from pathlib import Path

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)


class DevelopmentTreeStorage:
    """Persist the Development Tree independently from Project Storage."""

    SCHEMA_VERSION = 1
    FILE_NAME = "development_tree.json"

    def _path(self, project_path: str | Path) -> Path:
        return Path(project_path) / ".pacepilot" / self.FILE_NAME

    def save(
        self,
        project_path: str | Path,
        nodes: tuple[DevelopmentTreeNode, ...],
    ) -> None:
        if not isinstance(nodes, tuple):
            raise TypeError("nodes must be a tuple")

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "nodes": [self._serialize(node) for node in nodes],
        }

        path = self._path(project_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")

        try:
            with temporary.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, indent=2)
                handle.write("\n")
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def load(
        self,
        project_path: str | Path,
    ) -> tuple[DevelopmentTreeNode, ...]:
        path = self._path(project_path)

        if not path.exists():
            return ()

        try:
            with path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("Invalid development tree storage") from exc

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported development tree schema: "
                f"{payload.get('schema_version')!r}"
            )

        raw_nodes = payload.get("nodes")
        if not isinstance(raw_nodes, list):
            raise ValueError("Development tree nodes must be a list")

        return tuple(self._deserialize(item) for item in raw_nodes)

    @staticmethod
    def _serialize(node: DevelopmentTreeNode) -> dict:
        return {
            "node_id": node.node_id,
            "project_id": node.project_id,
            "node_key": node.node_key,
            "node_type": node.node_type.value,
            "status": node.status.value,
            "title": node.title,
            "parent_id": node.parent_id,
            "started_at": node.started_at,
            "completed_at": node.completed_at,
            "task_id": node.task_id,
            "run_id": node.run_id,
            "history_id": node.history_id,
            "summary": node.summary,
        }

    @staticmethod
    def _deserialize(data: dict) -> DevelopmentTreeNode:
        if not isinstance(data, dict):
            raise ValueError("Development tree node must be an object")

        return DevelopmentTreeNode(
            node_id=data["node_id"],
            project_id=data["project_id"],
            node_key=data["node_key"],
            node_type=DevelopmentNodeType(data["node_type"]),
            status=DevelopmentNodeStatus(data["status"]),
            title=data["title"],
            parent_id=data.get("parent_id"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at"),
            task_id=data.get("task_id"),
            run_id=data.get("run_id"),
            history_id=data.get("history_id"),
            summary=data.get("summary", ""),
        )


__all__ = ["DevelopmentTreeStorage"]
