"""Static dependency intelligence built on the dependency graph."""

from dataclasses import dataclass
from pathlib import Path

from agent_workflow.dependency_graph import DependencyGraph


@dataclass(frozen=True)
class DependencyImpact:
    """Immutable dependency impact information."""

    target: Path
    direct_dependents: tuple[Path, ...]
    all_dependents: tuple[Path, ...]


class DependencyIntelligence:
    """Query static dependency relationships without executing project code."""

    def __init__(self, graph: DependencyGraph) -> None:
        self.graph = graph

    def dependencies_of(self, path: Path) -> tuple[str, ...]:
        """Return direct dependency targets of a module."""
        source = Path(path)

        return tuple(
            sorted(
                {
                    edge.target
                    for edge in self.graph.edges
                    if edge.source == source
                }
            )
        )

    def dependents_of(self, path: Path) -> tuple[Path, ...]:
        """Return modules that directly depend on the target."""
        target = Path(path)

        return tuple(
            sorted(
                {
                    edge.source
                    for edge in self.graph.edges
                    if self._target_matches(edge.target, target)
                },
                key=str,
            )
        )

    def dependency_chain(
        self,
        path: Path,
    ) -> tuple[str, ...]:
        """Return all reachable dependency targets in stable order."""
        source = Path(path)
        visited_modules: set[Path] = set()
        discovered: set[str] = set()

        def visit(module: Path) -> None:
            if module in visited_modules:
                return

            visited_modules.add(module)

            for dependency in self.dependencies_of(module):
                if dependency in discovered:
                    continue

                discovered.add(dependency)

                dependency_path = self._resolve_node(dependency)
                if dependency_path is not None:
                    visit(dependency_path)

        visit(source)

        return tuple(sorted(discovered))

    def impact_of(self, path: Path) -> DependencyImpact:
        """Return direct and recursive reverse dependency impact."""
        target = Path(path)

        direct = self.dependents_of(target)
        visited: set[Path] = set()
        pending = list(direct)

        while pending:
            current = pending.pop(0)

            if current == target:
                continue

            if current in visited:
                continue

            visited.add(current)

            for dependent in self.dependents_of(current):
                if dependent not in visited:
                    pending.append(dependent)

        all_dependents = tuple(sorted(visited, key=str))

        return DependencyImpact(
            target=target,
            direct_dependents=direct,
            all_dependents=all_dependents,
        )

    def dependency_impact(self, path: Path) -> DependencyImpact:
        """Return dependency impact using the ProjectContextQuery interface."""
        return self.impact_of(path)

    def _resolve_node(self, target: str) -> Path | None:
        """Resolve an import target to a graph node when possible."""
        normalized = target.replace("\\", "/").replace(".", "/")

        candidates = (
            target,
            normalized,
            f"{normalized}.py",
        )

        for node in self.graph.nodes:
            node_text = str(node).replace("\\", "/")

            if node_text in candidates:
                return node

            if node.stem == target:
                return node

        return None

    def _target_matches(self, target: str, path: Path) -> bool:
        """Check whether an import target refers to the project module."""
        resolved = self._resolve_node(target)
        if resolved is not None:
            return resolved == path

        normalized_target = target.replace("\\", "/")
        normalized_path = str(path).replace("\\", "/")

        return normalized_target in {
            normalized_path,
            path.stem,
        }


if __name__ == "__main__":
    raise SystemExit("DependencyIntelligence is a library interface.")
