import tempfile
import unittest
from pathlib import Path

from agent_workflow.dependency_graph import DependencyGraphBuilder
from agent_workflow.dependency_intelligence import DependencyIntelligence
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.project_context import ProjectContextBuilder


class TestDependencyIntelligenceM1693(unittest.TestCase):

    def _build_intelligence(self, files):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            for relative_path, content in files.items():
                target = root / relative_path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)

            graph = context.dependency_graph

            return DependencyIntelligence(graph), root

    def test_empty_graph_returns_empty_dependency_views(self):
        intelligence, root = self._build_intelligence({})

        target = root / "missing.py"

        self.assertEqual(intelligence.dependencies_of(target), ())
        self.assertEqual(intelligence.dependents_of(target), ())

    def test_missing_node_has_stable_impact(self):
        intelligence, root = self._build_intelligence({
            "main.py": "value = 1\n",
        })

        impact = intelligence.impact_of(root / "missing.py")

        self.assertIsNotNone(impact)

    def test_single_file_has_no_dependency_chain(self):
        intelligence, root = self._build_intelligence({
            "main.py": "value = 1\n",
        })

        chain = intelligence.dependency_chain(root / "main.py")

        self.assertEqual(tuple(chain), ())

    def test_dependency_chain_is_deterministic(self):
        intelligence, root = self._build_intelligence({
            "main.py": "import utility\n",
            "utility.py": "import helper\n",
            "helper.py": "value = 1\n",
        })

        target = root / "main.py"

        first = tuple(intelligence.dependency_chain(target))
        second = tuple(intelligence.dependency_chain(target))

        self.assertEqual(first, second)

    def test_dependency_views_are_repeatable(self):
        intelligence, root = self._build_intelligence({
            "main.py": "import utility\n",
            "utility.py": "value = 1\n",
        })

        target = root / "main.py"

        self.assertEqual(
            intelligence.dependencies_of(target),
            intelligence.dependencies_of(target),
        )

        self.assertEqual(
            intelligence.dependents_of(target),
            intelligence.dependents_of(target),
        )

    def test_dependency_impact_is_repeatable(self):
        intelligence, root = self._build_intelligence({
            "main.py": "import utility\n",
            "utility.py": "value = 1\n",
        })

        target = root / "main.py"

        first = intelligence.impact_of(target)
        second = intelligence.impact_of(target)

        self.assertEqual(first, second)

    def test_relative_graph_identity_is_preserved(self):
        intelligence, root = self._build_intelligence({
            "main.py": "import utility\n",
            "utility.py": "value = 1\n",
        })

        dependencies = intelligence.dependencies_of(root / "main.py")

        for dependency in dependencies:
            self.assertFalse(Path(dependency).is_absolute())

    def test_dependency_chain_does_not_duplicate_nodes(self):
        intelligence, root = self._build_intelligence({
            "main.py": "import utility\nimport helper\n",
            "utility.py": "import helper\n",
            "helper.py": "value = 1\n",
        })

        chain = tuple(intelligence.dependency_chain(root / "main.py"))

        self.assertEqual(len(chain), len(set(chain)))

    def test_legacy_dependency_impact_alias_matches_impact(self):
        intelligence, root = self._build_intelligence({
            "main.py": "import utility\n",
            "utility.py": "value = 1\n",
        })

        target = root / "main.py"

        self.assertEqual(
            intelligence.dependency_impact(target),
            intelligence.impact_of(target),
        )


if __name__ == "__main__":
    unittest.main()
