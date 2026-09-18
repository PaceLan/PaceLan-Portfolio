import tempfile
import unittest
from pathlib import Path

from agent_workflow.analysis import AnalysisService


class AnalysisServiceTests(unittest.TestCase):
    def test_analyze_builds_complete_pipeline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "example.py"
            source.write_text(
                "import os\n\nclass Example:\n    pass\n\n"
                "def hello():\n    pass\n",
                encoding="utf-8",
            )

            result = AnalysisService(root).analyze()

            self.assertEqual(result.scan_result.root_path, root.resolve())
            self.assertEqual(len(result.file_index.entries), 1)
            self.assertEqual(len(result.python_ast), 1)
            self.assertEqual(len(result.relationships), 1)
            self.assertEqual(len(result.dependency_graph.nodes), 1)


if __name__ == "__main__":
    unittest.main()