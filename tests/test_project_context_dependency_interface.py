import tempfile
import unittest
from pathlib import Path

from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner


class ProjectContextDependencyInterfaceTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.project_root = root / "project"
        self.project_root.mkdir()

        (self.project_root / "main.py").write_text(
            "from helper import run\n",
            encoding="utf-8",
        )
        (self.project_root / "helper.py").write_text(
            "from base import value\n",
            encoding="utf-8",
        )
        (self.project_root / "base.py").write_text(
            "value = 1\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(self.project_root).scan()
        context = ProjectContextBuilder().build(scan_result)
        self.agent = ProjectContextAgentInterface(context)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_agent_exposes_dependency_targets(self) -> None:
        targets = self.agent.query.dependency_targets(
            Path("main.py")
        )

        self.assertEqual(targets, ("helper",))

    def test_agent_exposes_dependents(self) -> None:
        dependents = self.agent.query.dependents(
            Path("helper.py")
        )

        self.assertEqual(dependents, (Path("main.py"),))

    def test_agent_exposes_dependency_chain(self) -> None:
        chain = self.agent.query.dependency_chain(
            Path("main.py")
        )

        self.assertEqual(
            chain,
            ("base", "helper"),
        )

    def test_agent_exposes_dependency_impact(self) -> None:
        impact = self.agent.query.dependency_impact(
            Path("base.py")
        )

        self.assertEqual(
            impact.direct_dependents,
            (Path("helper.py"),),
        )
        self.assertEqual(
            impact.all_dependents,
            (
                Path("helper.py"),
                Path("main.py"),
            ),
        )


if __name__ == "__main__":
    unittest.main()
