"""Read-only Agent interface for unified ProjectContext."""

from dataclasses import dataclass
from pathlib import Path

from agent_workflow.context_understanding import ContextUnderstanding
from agent_workflow.project_context import ProjectContext
from agent_workflow.project_context_query import ProjectContextQuery


@dataclass(frozen=True)
class ProjectSummary:
    """Stable read-only summary of a project context."""

    root_path: Path
    total_files: int
    python_files: int


class ProjectContextAgentInterface:
    """Expose ProjectContext through a stable Agent-facing interface."""

    def __init__(
        self,
        context: ProjectContext,
        query: ProjectContextQuery | None = None,
    ) -> None:
        if not isinstance(context, ProjectContext):
            raise TypeError("context must be a ProjectContext")

        if query is not None and not isinstance(
            query,
            ProjectContextQuery,
        ):
            raise TypeError("query must be a ProjectContextQuery")

        self._context = context
        self._query = (
            query
            if query is not None
            else ProjectContextQuery(context)
        )
        self._context_understanding = ContextUnderstanding(self)

    @property
    def context(self) -> ProjectContext:
        """Return the immutable project context."""
        return self._context

    @property
    def query(self) -> ProjectContextQuery:
        """Return the read-only project context query interface."""
        return self._query

    @property
    def context_understanding(self) -> ContextUnderstanding:
        """Return the read-only Context Understanding interface."""
        return self._context_understanding

    @property
    def project_summary(self) -> ProjectSummary:
        """Return a stable summary for Agent consumption."""
        return ProjectSummary(
            root_path=self._context.root_path,
            total_files=len(self._context.scan_result.files),
            python_files=len(self._query.python_files()),
        )
