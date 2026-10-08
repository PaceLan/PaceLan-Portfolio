import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "vscode-extension"
MANIFEST = EXTENSION / "package.json"
SOURCE = EXTENSION / "extension.js"


class TestVSCodeExtensionC22(unittest.TestCase):
    def test_manifest_declares_real_extension(self):
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8-sig"))

        self.assertEqual(manifest["main"], "./extension.js")
        self.assertIn("commands", manifest["contributes"])

        commands = {
            item["command"]
            for item in manifest["contributes"]["commands"]
        }

        self.assertIn("pacepilot.createTask", commands)
        self.assertIn("pacepilot.pause", commands)
        self.assertIn("pacepilot.resume", commands)
        self.assertIn("pacepilot.stop", commands)

    def test_extension_uses_vscode_command_api(self):
        source = SOURCE.read_text(encoding="utf-8-sig")

        self.assertIn("vscode.commands.registerCommand", source)
        self.assertIn("vscode.workspace.onDidChangeWorkspaceFolders", source)

    def test_extension_tracks_terminal_lifecycle(self):
        source = SOURCE.read_text(encoding="utf-8-sig")

        self.assertIn("vscode.window.onDidOpenTerminal", source)
        self.assertIn("vscode.window.onDidCloseTerminal", source)
        self.assertIn("vscode.window.terminals", source)

    def test_extension_calls_c1_http_boundary(self):
        source = SOURCE.read_text(encoding="utf-8-sig")

        self.assertIn('DEFAULT_ENDPOINT = "http://127.0.0.1:8765/agent"', source)
        self.assertIn('method: "POST"', source)
        self.assertIn("task_id: taskId", source)
        self.assertIn("workflow_id: null", source)


if __name__ == "__main__":
    unittest.main()
