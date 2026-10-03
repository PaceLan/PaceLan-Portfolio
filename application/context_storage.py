"""Durable storage for unified ProjectContext snapshots."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from agent_workflow.dependency_graph import DependencyEdge, DependencyGraph
from agent_workflow.file_index import FileIndex, FileIndexEntry
from agent_workflow.project_context import ProjectContext
from agent_workflow.project_scanner import (
    ProjectDirectory,
    ProjectFile,
    ProjectScanResult,
    ProjectScanStatistics,
)
from agent_workflow.python_ast import (
    PythonAST,
    PythonClass,
    PythonFunction,
    PythonImport,
)
from agent_workflow.python_relationships import (
    PythonModuleRelationships,
    PythonRelationship,
    PythonSymbol,
)


class ContextStorage:
    """Persist and restore one complete ProjectContext snapshot."""

    SCHEMA_VERSION = 1
    DIRECTORY_NAME = ".pacepilot"
    FILE_NAME = "context.json"

    def _storage_path(self, project_path: str | Path) -> Path:
        return (
            Path(project_path)
            / self.DIRECTORY_NAME
            / self.FILE_NAME
        )

    def exists(self, project_path: str | Path) -> bool:
        return self._storage_path(project_path).is_file()

    def save(
        self,
        context: ProjectContext,
        project_path: str | Path,
    ) -> Path:
        if not isinstance(context, ProjectContext):
            raise TypeError("context must be a ProjectContext")

        root = Path(project_path)
        if not root.exists() or not root.is_dir():
            raise ValueError("project_path must be an existing directory")

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "context": self._context_to_dict(context),
        }

        target = self._storage_path(project_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".context.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        try:
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        return target

    def load(self, project_path: str | Path) -> ProjectContext:
        root = Path(project_path).resolve()
        target = self._storage_path(project_path)

        if not target.is_file():
            raise FileNotFoundError(
                f"Context storage does not exist: {target}"
            )

        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid context storage: {target}") from exc

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                "Unsupported context storage schema: "
                f"{payload.get('schema_version')!r}"
            )

        try:
            return self._context_from_dict(payload["context"], root)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid context storage structure") from exc

    @staticmethod
    def _context_to_dict(context: ProjectContext) -> dict:
        return {
            "root_path": str(context.root_path),
            "scan_result": {
                "files": [
                    {
                        "relative_path": str(item.relative_path),
                        "extension": item.extension,
                        "name": item.name,
                        "size": item.size,
                        "type": item.type,
                    }
                    for item in context.scan_result.files
                ],
                "directories": [
                    {
                        "relative_path": str(item.relative_path),
                        "name": item.name,
                        "files": [str(path) for path in item.files],
                        "subdirectories": [
                            str(path) for path in item.subdirectories
                        ],
                        "type": item.type,
                    }
                    for item in context.scan_result.directories
                ],
                "statistics": {
                    "file_count": context.scan_result.statistics.file_count,
                    "directory_count": (
                        context.scan_result.statistics.directory_count
                    ),
                    "total_size": context.scan_result.statistics.total_size,
                    "ignored_count": (
                        context.scan_result.statistics.ignored_count
                    ),
                },
                "errors": list(context.scan_result.errors),
            },
            "file_index": {
                "entries": [
                    {
                        "relative_path": str(item.relative_path),
                        "extension": item.extension,
                        "file_type": item.file_type,
                    }
                    for item in context.file_index.entries
                ],
            },
            "python_asts": [
                {
                    "relative_path": str(item.relative_path),
                    "imports": [
                        {"name": value.name, "level": value.level}
                        for value in item.imports
                    ],
                    "classes": [
                        {"name": value.name, "lineno": value.lineno}
                        for value in item.classes
                    ],
                    "functions": [
                        {"name": value.name, "lineno": value.lineno}
                        for value in item.functions
                    ],
                }
                for item in context.python_asts
            ],
            "python_relationships": [
                {
                    "relative_path": str(item.relative_path),
                    "symbols": [
                        {
                            "name": value.name,
                            "kind": value.kind,
                            "lineno": value.lineno,
                        }
                        for value in item.symbols
                    ],
                    "relationships": [
                        {
                            "source": value.source,
                            "target": value.target,
                            "kind": value.kind,
                        }
                        for value in item.relationships
                    ],
                }
                for item in context.python_relationships
            ],
            "dependency_graph": {
                "nodes": [
                    str(path) for path in context.dependency_graph.nodes
                ],
                "edges": [
                    {
                        "source": str(edge.source),
                        "target": edge.target,
                    }
                    for edge in context.dependency_graph.edges
                ],
            },
        }

    @staticmethod
    def _context_from_dict(
        data: dict,
        root: Path,
    ) -> ProjectContext:
        scan_data = data["scan_result"]

        files = tuple(
            ProjectFile(
                relative_path=Path(item["relative_path"]),
                extension=item["extension"],
                name=item["name"],
                size=item["size"],
                type=item.get("type", "file"),
            )
            for item in scan_data["files"]
        )

        directories = tuple(
            ProjectDirectory(
                relative_path=Path(item["relative_path"]),
                name=item["name"],
                files=tuple(
                    Path(path) for path in item.get("files", [])
                ),
                subdirectories=tuple(
                    Path(path)
                    for path in item.get("subdirectories", [])
                ),
                type=item.get("type", "directory"),
            )
            for item in scan_data.get("directories", [])
        )

        stats = scan_data["statistics"]
        scan_result = ProjectScanResult(
            root_path=root,
            files=files,
            directories=directories,
            statistics=ProjectScanStatistics(
                file_count=stats["file_count"],
                directory_count=stats["directory_count"],
                total_size=stats["total_size"],
                ignored_count=stats["ignored_count"],
            ),
            errors=tuple(scan_data.get("errors", [])),
        )

        file_index = FileIndex(
            root_path=root,
            entries=tuple(
                FileIndexEntry(
                    relative_path=Path(item["relative_path"]),
                    extension=item["extension"],
                    file_type=item["file_type"],
                )
                for item in data["file_index"]["entries"]
            ),
        )

        python_asts = tuple(
            PythonAST(
                relative_path=Path(item["relative_path"]),
                imports=tuple(
                    PythonImport(
                        name=value["name"],
                        level=value["level"],
                    )
                    for value in item["imports"]
                ),
                classes=tuple(
                    PythonClass(
                        name=value["name"],
                        lineno=value["lineno"],
                    )
                    for value in item["classes"]
                ),
                functions=tuple(
                    PythonFunction(
                        name=value["name"],
                        lineno=value["lineno"],
                    )
                    for value in item["functions"]
                ),
            )
            for item in data["python_asts"]
        )

        python_relationships = tuple(
            PythonModuleRelationships(
                relative_path=Path(item["relative_path"]),
                symbols=tuple(
                    PythonSymbol(
                        name=value["name"],
                        kind=value["kind"],
                        lineno=value["lineno"],
                    )
                    for value in item["symbols"]
                ),
                relationships=tuple(
                    PythonRelationship(
                        source=value["source"],
                        target=value["target"],
                        kind=value["kind"],
                    )
                    for value in item["relationships"]
                ),
            )
            for item in data["python_relationships"]
        )

        graph_data = data["dependency_graph"]
        dependency_graph = DependencyGraph(
            nodes=tuple(
                Path(path) for path in graph_data["nodes"]
            ),
            edges=tuple(
                DependencyEdge(
                    source=Path(edge["source"]),
                    target=edge["target"],
                )
                for edge in graph_data["edges"]
            ),
        )

        return ProjectContext(
            root_path=root,
            scan_result=scan_result,
            file_index=file_index,
            python_asts=python_asts,
            python_relationships=python_relationships,
            dependency_graph=dependency_graph,
        )


__all__ = ["ContextStorage"]







