from __future__ import annotations

"""Deterministic, read-only task context understanding."""

from dataclasses import dataclass
from pathlib import Path
import re

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from agent_workflow.project_context_interface import (
        ProjectContextAgentInterface,
    )
from agent_workflow.python_relationships import (
    PythonRelationship,
    PythonSymbol,
)
from agent_workflow.workflow_core import WorkflowTask


@dataclass(frozen=True)
class TaskContext:
    """Normalized task information used during context understanding."""

    task_id: str
    project_id: str
    description: str
    context: str
    target: str = ""


@dataclass(frozen=True)
class ContextSummary:
    """Immutable structured summary for Agent consumption."""

    task_id: str
    project_id: str
    target: str
    relevant_file_count: int
    relevant_symbol_count: int
    relationship_count: int
    dependency_count: int


@dataclass(frozen=True)
class ContextUnderstandingResult:
    """Immutable deterministic understanding of task-relevant context."""

    task: TaskContext
    relevant_files: tuple[Path, ...]
    relevant_symbols: tuple[PythonSymbol, ...] = ()
    relationships: tuple[PythonRelationship, ...] = ()
    dependencies: tuple[str, ...] = ()
    summary: str = ""
    structured_summary: ContextSummary | None = None


class ContextUnderstanding:
    """Select relevant project context without modifying the project."""

    _TARGET_PATTERN = re.compile(
        r"(?:file|path|target)\s*[:=]\s*([^\s,;]+)",
        re.IGNORECASE,
    )

    def __init__(
        self,
        project_interface: ProjectContextAgentInterface,
    ) -> None:
        from agent_workflow.project_context_interface import (
            ProjectContextAgentInterface,
        )

        if not isinstance(
            project_interface,
            ProjectContextAgentInterface,
        ):
            raise TypeError(
                "project_interface must be a "
                "ProjectContextAgentInterface"
            )

        self.project_interface = project_interface
        self.query = project_interface.query

    def understand(
        self,
        task: WorkflowTask,
    ) -> ContextUnderstandingResult:
        """Build deterministic task context without project mutation."""
        if not isinstance(task, WorkflowTask):
            raise TypeError("task must be a WorkflowTask")

        task_context = self._build_task_context(task)

        relevant_files = self._select_relevant_files(
            task_context
        )

        relevant_symbols = self._select_relevant_symbols(
            relevant_files
        )

        relationships = self._expand_relationships(
            relevant_files,
            relevant_symbols,
        )

        dependencies = self._expand_dependencies(
            relevant_files,
            relationships,
        )

        summary = self._build_summary(
            task_context,
            relevant_files,
            relevant_symbols,
            relationships,
            dependencies,
        )

        structured_summary = ContextSummary(
            task_id=task_context.task_id,
            project_id=task_context.project_id,
            target=task_context.target,
            relevant_file_count=len(relevant_files),
            relevant_symbol_count=len(relevant_symbols),
            relationship_count=len(relationships),
            dependency_count=len(dependencies),
        )

        return ContextUnderstandingResult(
            task=task_context,
            relevant_files=relevant_files,
            relevant_symbols=relevant_symbols,
            relationships=relationships,
            dependencies=dependencies,
            summary=summary,
            structured_summary=structured_summary,
        )

    def _build_task_context(
        self,
        task: WorkflowTask,
    ) -> TaskContext:
        return TaskContext(
            task_id=task.task_id,
            project_id=task.project_id,
            description=task.description,
            context=task.context,
            target=self._extract_target(task),
        )

    def _extract_target(
        self,
        task: WorkflowTask,
    ) -> str:
        combined = f"{task.description} {task.context}".strip()

        match = self._TARGET_PATTERN.search(combined)

        if match:
            return match.group(1)

        return ""

    def _select_relevant_files(
        self,
        task_context: TaskContext,
    ) -> tuple[Path, ...]:
        """Select relevant files using the existing context interfaces."""
        files = self.project_interface.context.scan_result.files

        python_files = set(
            self.query.python_files()
        )

        description = (
            f"{task_context.description} "
            f"{task_context.context}"
        ).lower()

        target = task_context.target.lower()

        selected: set[Path] = set()

        for project_file in files:
            relative_path = project_file.relative_path

            path_text = str(relative_path).replace(
                "\\",
                "/",
            )

            path_lower = path_text.lower()
            name_lower = project_file.name.lower()
            stem_lower = Path(
                project_file.name
            ).stem.lower()

            if target:
                normalized_target = target.replace(
                    "\\",
                    "/",
                )

                normalized_target = (
                    normalized_target.lower()
                )

                if (
                    path_lower == normalized_target
                    or name_lower
                    == Path(normalized_target).name
                ):
                    selected.add(relative_path)
                    continue

            if (
                name_lower
                and name_lower in description
            ):
                selected.add(relative_path)
                continue

            if (
                stem_lower
                and stem_lower in description
            ):
                selected.add(relative_path)
                continue

            if relative_path in python_files:
                module_name = stem_lower.replace(
                    "-",
                    "_",
                )

                if (
                    module_name
                    and module_name in description
                ):
                    selected.add(relative_path)

        return tuple(
            sorted(
                selected,
                key=lambda path: str(path),
            )
        )

    def _select_relevant_symbols(
        self,
        relevant_files: tuple[Path, ...],
    ) -> tuple[PythonSymbol, ...]:
        """Collect symbols defined by relevant Python files."""
        symbols: list[PythonSymbol] = []

        for relative_path in relevant_files:
            relationships = (
                self.query.get_python_relationships(
                    relative_path
                )
            )

            if relationships is None:
                continue

            symbols.extend(
                relationships.symbols
            )

        unique_symbols = self._deduplicate_symbols(
            symbols
        )

        return tuple(
            sorted(
                unique_symbols,
                key=lambda symbol: (
                    symbol.name,
                    symbol.kind,
                    symbol.lineno,
                ),
            )
        )

    @staticmethod
    def _deduplicate_symbols(
        symbols: list[PythonSymbol],
    ) -> tuple[PythonSymbol, ...]:
        seen: set[tuple[str, str, int]] = set()
        result: list[PythonSymbol] = []

        for symbol in symbols:
            key = (
                symbol.name,
                symbol.kind,
                symbol.lineno,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(symbol)

        return tuple(result)

    def _expand_relationships(
        self,
        relevant_files: tuple[Path, ...],
        relevant_symbols: tuple[PythonSymbol, ...],
    ) -> tuple[PythonRelationship, ...]:
        """Collect relationships precisely associated with relevant symbols."""

        symbol_names = {
            symbol.name
            for symbol in relevant_symbols
        }

        relationships: list[PythonRelationship] = []

        for relative_path in relevant_files:
            module_relationships = (
                self.query.get_python_relationships(
                    relative_path
                )
            )

            if module_relationships is None:
                continue

            for relationship in module_relationships.relationships:
                if relationship.kind == "contains":
                    if relationship.target in symbol_names:
                        relationships.append(relationship)
                    continue

                relationships.append(relationship)

        unique_relationships = (
            self._deduplicate_relationships(
                relationships
            )
        )

        return tuple(
            sorted(
                unique_relationships,
                key=lambda relationship: (
                    relationship.source,
                    relationship.target,
                    relationship.kind,
                ),
            )
        )

    @staticmethod
    def _deduplicate_relationships(
        relationships: list[PythonRelationship],
    ) -> tuple[PythonRelationship, ...]:
        seen: set[tuple[str, str, str]] = set()
        result: list[PythonRelationship] = []

        for relationship in relationships:
            key = (
                relationship.source,
                relationship.target,
                relationship.kind,
            )

            if key in seen:
                continue

            seen.add(key)
            result.append(relationship)

        return tuple(result)

    def _expand_dependencies(
        self,
        relevant_files: tuple[Path, ...],
        relationships: tuple[PythonRelationship, ...] = (),
    ) -> tuple[str, ...]:
        """Expand dependencies from files and import relationships."""

        dependencies: set[str] = set()

        for relative_path in relevant_files:
            dependencies.update(
                self.query.dependency_targets(
                    relative_path
                )
            )

            dependencies.update(
                self.query.dependency_chain(
                    relative_path
                )
            )

        for relationship in relationships:
            if relationship.kind == "imports":
                dependencies.add(relationship.target)

        return tuple(
            sorted(dependencies)
        )

    def understand_task(
        self,
        task: WorkflowTask,
    ) -> ContextUnderstandingResult:
        """Agent-facing alias for deterministic task understanding."""
        return self.understand(task)

    @staticmethod
    def _build_summary(
        task: TaskContext,
        relevant_files: tuple[Path, ...],
        relevant_symbols: tuple[PythonSymbol, ...],
        relationships: tuple[PythonRelationship, ...],
        dependencies: tuple[str, ...],
    ) -> str:
        return (
            f"Task {task.task_id}: "
            f"{len(relevant_files)} relevant files, "
            f"{len(relevant_symbols)} relevant symbols, "
            f"{len(relationships)} relationships, "
            f"{len(dependencies)} dependencies."
        )


if __name__ == "__main__":
    raise SystemExit(
        "ContextUnderstanding is a library interface."
    )