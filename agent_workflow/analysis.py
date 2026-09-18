"""Unified project analysis pipeline."""

from dataclasses import dataclass
from pathlib import Path

from agent_workflow.dependency_graph import (
    DependencyGraph,
    DependencyGraphBuilder,
)
from agent_workflow.file_index import FileIndex
from agent_workflow.project_scanner import (
    ProjectScanResult,
    ProjectScanner,
)
from agent_workflow.python_ast import (
    PythonAST,
    PythonASTAnalyzer,
)
from agent_workflow.python_relationships import (
    PythonModuleRelationships,
    PythonRelationshipAnalyzer,
)


@dataclass(frozen=True)
class AnalysisResult:
    """Immutable result of a complete project analysis."""

    scan_result: ProjectScanResult
    file_index: FileIndex
    python_ast: tuple[PythonAST, ...]
    relationships: tuple[PythonModuleRelationships, ...]
    dependency_graph: DependencyGraph


class AnalysisService:
    """Coordinate the complete project analysis pipeline."""

    def __init__(self, root_path: str | Path) -> None:
        self.root_path = Path(root_path).resolve()
        self.scanner = ProjectScanner(self.root_path)
        self.ast_analyzer = PythonASTAnalyzer()
        self.relationship_analyzer = PythonRelationshipAnalyzer()
        self.graph_builder = DependencyGraphBuilder()

    def analyze(self) -> AnalysisResult:
        """Run the complete project analysis pipeline."""
        scan_result = self.scanner.scan()
        file_index = FileIndex.from_scan_result(scan_result)

        python_entries = tuple(
            entry
            for entry in file_index.entries
            if entry.file_type == "python"
        )

        python_ast = tuple(
            self.ast_analyzer.analyze(
                self.root_path / entry.relative_path,
                relative_path=entry.relative_path,
            )
            for entry in python_entries
        )

        relationships = tuple(
            self.relationship_analyzer.analyze(ast_result)
            for ast_result in python_ast
        )

        dependency_graph = self.graph_builder.build(relationships)

        return AnalysisResult(
            scan_result=scan_result,
            file_index=file_index,
            python_ast=python_ast,
            relationships=relationships,
            dependency_graph=dependency_graph,
        )