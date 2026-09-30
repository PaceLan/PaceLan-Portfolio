import unittest
from pathlib import Path

from agent_workflow.dependency_graph import (
    DependencyEdge,
    DependencyGraph,
)
from agent_workflow.dependency_intelligence import DependencyIntelligence


class DependencyIntelligenceBoundaryTests(unittest.TestCase):

    def setUp(self) -> None:
        self.graph = DependencyGraph(
            nodes=(
                Path("a.py"),
                Path("b.py"),
                Path("c.py"),
            ),
            edges=(
                DependencyEdge(Path("a.py"), "b"),
                DependencyEdge(Path("b.py"), "c"),
                DependencyEdge(Path("c.py"), "a"),
            ),
        )
        self.intelligence = DependencyIntelligence(self.graph)

    def test_dependency_chain_terminates_on_cycle(self) -> None:
        chain = self.intelligence.dependency_chain(Path("a.py"))

        self.assertEqual(
            chain,
            ("a", "b", "c"),
        )

    def test_impact_terminates_on_cycle(self) -> None:
        impact = self.intelligence.impact_of(Path("a.py"))

        self.assertEqual(
            impact.direct_dependents,
            (Path("c.py"),),
        )
        self.assertEqual(
            impact.all_dependents,
            (
                Path("b.py"),
                Path("c.py"),
            ),
        )

    def test_cycle_does_not_duplicate_dependencies(self) -> None:
        chain = self.intelligence.dependency_chain(Path("b.py"))

        self.assertEqual(
            chain,
            ("a", "b", "c"),
        )

    def test_unknown_target_inside_cycle_is_stable(self) -> None:
        self.assertEqual(
            self.intelligence.dependency_chain(Path("missing.py")),
            (),
        )
        self.assertEqual(
            self.intelligence.dependents_of(Path("missing.py")),
            (),
        )


if __name__ == "__main__":
    unittest.main()
