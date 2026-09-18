"""Tests for static dependency graph construction."""

import unittest
from pathlib import Path

from agent_workflow.dependency_graph import (
    DependencyEdge,
    DependencyGraphBuilder,
)
from agent_workflow.python_relationships import (
    PythonModuleRelationships,
    PythonRelationship,
    PythonSymbol,
)


class DependencyGraphBuilderTests(unittest.TestCase):
    """Verify dependency graph construction."""

    def test_builds_nodes_and_import_edges(self) -> None:
        relationships = (
            PythonModuleRelationships(
                relative_path=Path("b.py"),
                symbols=(
                    PythonSymbol(
                        name="Beta",
                        kind="class",
                        lineno=1,
                    ),
                ),
                relationships=(
                    PythonRelationship(
                        source="b.py",
                        target="alpha",
                        kind="imports",
                    ),
                    PythonRelationship(
                        source="b.py",
                        target="Beta",
                        kind="contains",
                    ),
                ),
            ),
            PythonModuleRelationships(
                relative_path=Path("a.py"),
                symbols=(),
                relationships=(
                    PythonRelationship(
                        source="a.py",
                        target="os",
                        kind="imports",
                    ),
                ),
            ),
        )

        result = DependencyGraphBuilder().build(relationships)

        self.assertEqual(
            result.nodes,
            (Path("a.py"), Path("b.py")),
        )
        self.assertEqual(
            result.edges,
            (
                DependencyEdge(
                    source=Path("a.py"),
                    target="os",
                ),
                DependencyEdge(
                    source=Path("b.py"),
                    target="alpha",
                ),
            ),
        )

    def test_ignores_non_import_relationships(self) -> None:
        relationships = (
            PythonModuleRelationships(
                relative_path=Path("module.py"),
                symbols=(),
                relationships=(
                    PythonRelationship(
                        source="module.py",
                        target="SomeClass",
                        kind="contains",
                    ),
                ),
            ),
        )

        result = DependencyGraphBuilder().build(relationships)

        self.assertEqual(
            result.nodes,
            (Path("module.py"),),
        )
        self.assertEqual(result.edges, ())

    def test_handles_empty_relationships(self) -> None:
        result = DependencyGraphBuilder().build(())

        self.assertEqual(result.nodes, ())
        self.assertEqual(result.edges, ())

    def test_preserves_duplicate_import_targets_as_one_edge(self) -> None:
        relationships = (
            PythonModuleRelationships(
                relative_path=Path("module.py"),
                symbols=(),
                relationships=(
                    PythonRelationship(
                        source="module.py",
                        target="os",
                        kind="imports",
                    ),
                    PythonRelationship(
                        source="module.py",
                        target="os",
                        kind="imports",
                    ),
                ),
            ),
        )

        result = DependencyGraphBuilder().build(relationships)

        self.assertEqual(
            result.edges,
            (
                DependencyEdge(
                    source=Path("module.py"),
                    target="os",
                ),
            ),
        )

    def test_graph_is_immutable(self) -> None:
        relationships = (
            PythonModuleRelationships(
                relative_path=Path("module.py"),
                symbols=(),
                relationships=(),
            ),
        )

        result = DependencyGraphBuilder().build(relationships)

        with self.assertRaises(AttributeError):
            result.nodes = ()

        with self.assertRaises(AttributeError):
            result.edges = ()

    def test_edge_is_immutable(self) -> None:
        edge = DependencyEdge(
            source=Path("module.py"),
            target="os",
        )

        with self.assertRaises(AttributeError):
            edge.source = Path("other.py")

        with self.assertRaises(AttributeError):
            edge.target = "sys"

    def test_edges_are_stably_sorted(self) -> None:
        relationships = (
            PythonModuleRelationships(
                relative_path=Path("z.py"),
                symbols=(),
                relationships=(
                    PythonRelationship(
                        source="z.py",
                        target="beta",
                        kind="imports",
                    ),
                    PythonRelationship(
                        source="z.py",
                        target="alpha",
                        kind="imports",
                    ),
                ),
            ),
            PythonModuleRelationships(
                relative_path=Path("a.py"),
                symbols=(),
                relationships=(
                    PythonRelationship(
                        source="a.py",
                        target="zeta",
                        kind="imports",
                    ),
                ),
            ),
        )

        result = DependencyGraphBuilder().build(relationships)

        self.assertEqual(
            result.edges,
            (
                DependencyEdge(
                    source=Path("a.py"),
                    target="zeta",
                ),
                DependencyEdge(
                    source=Path("z.py"),
                    target="alpha",
                ),
                DependencyEdge(
                    source=Path("z.py"),
                    target="beta",
                ),
            ),
        )


if __name__ == "__main__":
    unittest.main()