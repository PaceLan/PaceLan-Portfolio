"""Static dependency graph derived from Python relationships."""

from dataclasses import dataclass
from pathlib import Path

from agent_workflow.python_relationships import PythonModuleRelationships


@dataclass(frozen=True)
class DependencyEdge:
    """A static dependency from one Python module to an imported target."""

    source: Path
    target: str


@dataclass(frozen=True)
class DependencyGraph:
    """Immutable static dependency graph."""

    nodes: tuple[Path, ...]
    edges: tuple[DependencyEdge, ...]


class DependencyGraphBuilder:
    """Build a dependency graph from Python module relationships."""

    def build(
        self,
        relationships: tuple[PythonModuleRelationships, ...],
    ) -> DependencyGraph:
        """Build a stable dependency graph from module relationships."""
        nodes = sorted(
            {
                module.relative_path
                for module in relationships
            },
            key=str,
        )

        edges = sorted(
            {
                DependencyEdge(
                    source=module.relative_path,
                    target=relationship.target,
                )
                for module in relationships
                for relationship in module.relationships
                if relationship.kind == "imports"
            },
            key=lambda edge: (str(edge.source), edge.target),
        )

        return DependencyGraph(
            nodes=tuple(nodes),
            edges=tuple(edges),
        )