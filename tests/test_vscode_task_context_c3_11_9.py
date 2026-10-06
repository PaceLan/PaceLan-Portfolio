import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "vscode-extension" / "extension.js"


class TestVSCodeTaskContextC3119(unittest.TestCase):
    def setUp(self):
        self.source = SOURCE.read_text(encoding="utf-8-sig")

    def test_extension_declares_task_context(self):
        self.assertIn("taskContext:", self.source)
        self.assertIn("task_id: null", self.source)
        self.assertIn("workflow_id: null", self.source)

    def test_response_updates_task_context(self):
        self.assertIn("state.taskContext = {", self.source)
        self.assertIn("task_id: result.task_id ?? taskId", self.source)
        self.assertIn("workflow_id: result.workflow_id ?? null", self.source)

    def test_project_id_is_not_fabricated(self):
        self.assertIn("project_id: null", self.source)


if __name__ == "__main__":
    unittest.main()
