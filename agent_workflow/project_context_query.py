"""Read-only queries over ProjectContext."""

from pathlib import Path

from agent_workflow.dependency_intelligence import (
    DependencyImpact,
    DependencyIntelligence,
)
from agent_workflow.project_context import ProjectContext
from agent_workflow.project_scanner import ProjectFile
from agent_workflow.python_ast import PythonAST
from agent_workflow.python_relationships import PythonModuleRelationships


class ProjectContextQuery:
    """Provide stable read-only queries over a ProjectContext."""

    def __init__(self, context: ProjectContext) -> None:
        if not isinstance(context, ProjectContext):
            raise TypeError("context must be a ProjectContext")

        self.context = context
        self._dependency_intelligence = DependencyIntelligence(
            context.dependency_graph
        )

    def get_file(self, relative_path: Path) -> ProjectFile | None:
        """Return a scanned project file by relative path."""
        path = Path(relative_path)

        for project_file in self.context.scan_result.files:
            if project_file.relative_path == path:
                return project_file

        return None

    def get_python_ast(
        self,
        relative_path: Path,
    ) -> PythonAST | None:
        """Return Python AST information by relative path."""
        path = Path(relative_path)

        for ast_result in self.context.python_asts:
            if ast_result.relative_path == path:
                return ast_result

        return None

    def get_python_relationships(
        self,
        relative_path: Path,
    ) -> PythonModuleRelationships | None:
        """Return Python relationships by relative path."""
        path = Path(relative_path)

        for relationships in self.context.python_relationships:
            if relationships.relative_path == path:
                return relationships

        return None

    def python_files(self) -> tuple[Path, ...]:
        """Return all Python files in stable order."""
        return tuple(
            entry.relative_path
            for entry in self.context.file_index.entries
            if entry.file_type == "python"
        )

    def dependency_targets(
        self,
        relative_path: Path,
    ) -> tuple[str, ...]:
        """Return imported dependency targets for one Python file."""
        return self._dependency_intelligence.dependencies_of(
            Path(relative_path)
        )

    def dependents(
        self,
        relative_path: Path,
    ) -> tuple[Path, ...]:
        """Return files that directly depend on one Python file."""
        return self._dependency_intelligence.dependents_of(
            Path(relative_path)
        )

    def dependency_chain(
        self,
        relative_path: Path,
    ) -> tuple[str, ...]:
        """Return all recursively reachable dependency targets."""
        return self._dependency_intelligence.dependency_chain(
            Path(relative_path)
        )

    def dependency_impact(
        self,
        relative_path: Path,
    ) -> DependencyImpact:
        """Return direct and recursive reverse dependency impact."""
        return self._dependency_intelligence.dependency_impact(
            Path(relative_path)
        )


if __name__ == "__main__":
    raise SystemExit("ProjectContextQuery is a library interface.")
