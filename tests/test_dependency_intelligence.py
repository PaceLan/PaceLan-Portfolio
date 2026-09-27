"""Tests for static dependency intelligence."""

import unittest
from pathlib import Path

from agent_workflow.dependency_graph import (
    DependencyEdge,
    DependencyGraph,
)
from agent_workflow.dependency_intelligence import (
    DependencyImpact,
    DependencyIntelligence,
)


class DependencyIntelligenceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.graph = DependencyGraph(
            nodes=(
                Path("a.py"),
                Path("b.py"),
                Path("c.py"),
                Path("d.py"),
            ),
            edges=(
                DependencyEdge(Path("a.py"), "b"),
                DependencyEdge(Path("b.py"), "c"),
                DependencyEdge(Path("c.py"), "d"),
                DependencyEdge(Path("d.py"), "external"),
            ),
        )
        self.intelligence = DependencyIntelligence(self.graph)

    def test_dependencies_of_returns_direct_dependencies(self) -> None:
        self.assertEqual(
            self.intelligence.dependencies_of(Path("a.py")),
            ("b",),
        )

    def test_dependencies_of_keeps_external_targets(self) -> None:
        self.assertEqual(
            self.intelligence.dependencies_of(Path("d.py")),
            ("external",),
        )

    def test_dependents_of_returns_direct_dependents(self) -> None:
        self.assertEqual(
            self.intelligence.dependents_of(Path("c.py")),
            (Path("b.py"),),
        )

    def test_dependency_chain_traverses_recursively(self) -> None:
        self.assertEqual(
            self.intelligence.dependency_chain(Path("a.py")),
            ("b", "c", "d", "external"),
        )

    def test_impact_of_returns_direct_and_recursive_dependents(self) -> None:
        self.assertEqual(
            self.intelligence.impact_of(Path("d.py")),
            DependencyImpact(
                target=Path("d.py"),
                direct_dependents=(Path("c.py"),),
                all_dependents=(
                    Path("a.py"),
                    Path("b.py"),
                    Path("c.py"),
                ),
            ),
        )

    def test_unknown_module_has_empty_results(self) -> None:
        unknown = Path("unknown.py")

        self.assertEqual(
            self.intelligence.dependencies_of(unknown),
            (),
        )
        self.assertEqual(
            self.intelligence.dependents_of(unknown),
            (),
        )
        self.assertEqual(
            self.intelligence.dependency_chain(unknown),
            (),
        )

    def test_impact_is_immutable(self) -> None:
        result = self.intelligence.impact_of(Path("d.py"))

        with self.assertRaises(AttributeError):
            result.target = Path("x.py")

        self.assertIsInstance(result.direct_dependents, tuple)
        self.assertIsInstance(result.all_dependents, tuple)


if __name__ == "__main__":
    unittest.main()
