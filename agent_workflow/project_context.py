"""Unified immutable project context for Agent consumption."""

from dataclasses import dataclass
from pathlib import Path

from agent_workflow.dependency_graph import (
    DependencyGraph,
    DependencyGraphBuilder,
)
from agent_workflow.file_index import FileIndex
from agent_workflow.project_scanner import ProjectScanResult
from agent_workflow.python_ast import PythonAST, PythonASTAnalyzer
from agent_workflow.python_relationships import (
    PythonModuleRelationships,
    PythonRelationshipAnalyzer,
)


@dataclass(frozen=True)
class ProjectContext:
    """Immutable unified understanding of a scanned project."""

    root_path: Path
    scan_result: ProjectScanResult
    file_index: FileIndex
    python_asts: tuple[PythonAST, ...]
    python_relationships: tuple[PythonModuleRelationships, ...]
    dependency_graph: DependencyGraph


class ProjectContextBuilder:
    """Build unified project context from an existing scan result."""

    def __init__(
        self,
        ast_analyzer: PythonASTAnalyzer | None = None,
        relationship_analyzer: PythonRelationshipAnalyzer | None = None,
        dependency_graph_builder: DependencyGraphBuilder | None = None,
    ) -> None:
        self.ast_analyzer = (
            ast_analyzer
            if ast_analyzer is not None
            else PythonASTAnalyzer()
        )
        self.relationship_analyzer = (
            relationship_analyzer
            if relationship_analyzer is not None
            else PythonRelationshipAnalyzer()
        )
        self.dependency_graph_builder = (
            dependency_graph_builder
            if dependency_graph_builder is not None
            else DependencyGraphBuilder()
        )

    def build(
        self,
        scan_result: ProjectScanResult,
    ) -> ProjectContext:
        """Build complete project context from a scan result."""
        file_index = FileIndex.from_scan_result(scan_result)

        python_asts: list[PythonAST] = []

        for entry in file_index.entries:
            if entry.file_type != "python":
                continue

            source_path = scan_result.root_path / entry.relative_path

            python_asts.append(
                self.ast_analyzer.analyze(
                    source_path,
                    relative_path=entry.relative_path,
                )
            )

        python_asts.sort(
            key=lambda item: str(item.relative_path)
        )

        python_relationships = tuple(
            self.relationship_analyzer.analyze(ast_result)
            for ast_result in python_asts
        )

        dependency_graph = self.dependency_graph_builder.build(
            python_relationships
        )

        return ProjectContext(
            root_path=scan_result.root_path,
            scan_result=scan_result,
            file_index=file_index,
            python_asts=tuple(python_asts),
            python_relationships=python_relationships,
            dependency_graph=dependency_graph,
        )
