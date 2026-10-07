import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SERVER = ROOT / "tests" / "fixtures_vscode_terminal_server_c4_5_4.js"


class VSCodeControlChannelE2ETests(unittest.TestCase):
    def test_python_channel_reaches_node_terminal_control(self):
        process = subprocess.Popen(
            ["node", str(SERVER)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        try:
            line = process.stdout.readline().strip()
            self.assertTrue(line)

            port = json.loads(line)["port"]
            process.stdout.readline()

            from application.vscode_control_channel import VSCodeControlChannel

            channel = VSCodeControlChannel(
                f"http://127.0.0.1:{port}/terminal"
            )

            created = channel.create(r"C:\workspace", "PacePilot")
            self.assertEqual(created.state, "RUNNING")
            self.assertTrue(created.terminal_id)

            sent = channel.send(created.terminal_id, "python -m unittest")
            self.assertEqual(sent.state, "RUNNING")

            status = channel.status(created.terminal_id)
            self.assertEqual(status.state, "RUNNING")

            closed = channel.close(created.terminal_id)
            self.assertEqual(closed.state, "CLOSED")
        finally:
            process.terminate()
            process.wait(timeout=5)

            if process.stdout is not None:
                process.stdout.close()

            if process.stderr is not None:
                process.stderr.close()


if __name__ == "__main__":
    unittest.main()
