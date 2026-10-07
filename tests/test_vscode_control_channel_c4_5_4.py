import json
import unittest
from unittest.mock import patch

from application.vscode_control_channel import VSCodeControlChannel


class VSCodeControlChannelC454Tests(unittest.TestCase):
    def test_create_sends_create_operation(self):
        channel = VSCodeControlChannel("http://127.0.0.1:8766/terminal")

        with patch("application.vscode_control_channel.urlopen") as opened:
            opened.return_value.__enter__.return_value.read.return_value = (
                b'{"terminal_id":"t1","state":"RUNNING"}'
            )

            result = channel.create("C:\\work")

            request = opened.call_args.args[0]
            body = json.loads(request.data.decode("utf-8"))

        self.assertEqual(body["operation"], "create")
        self.assertEqual(body["cwd"], "C:\\work")
        self.assertEqual(result.terminal_id, "t1")
        self.assertEqual(result.state, "RUNNING")

    def test_send_sends_command(self):
        channel = VSCodeControlChannel("http://127.0.0.1:8766/terminal")

        with patch("application.vscode_control_channel.urlopen") as opened:
            opened.return_value.__enter__.return_value.read.return_value = (
                b'{"terminal_id":"t1","state":"RUNNING","output":"ok"}'
            )

            result = channel.send("t1", "python -m unittest")

            body = json.loads(
                opened.call_args.args[0].data.decode("utf-8")
            )

        self.assertEqual(body["operation"], "send")
        self.assertEqual(body["terminal_id"], "t1")
        self.assertEqual(body["command"], "python -m unittest")
        self.assertEqual(result.output, "ok")

    def test_close_sends_close_operation(self):
        channel = VSCodeControlChannel("http://127.0.0.1:8766/terminal")

        with patch("application.vscode_control_channel.urlopen") as opened:
            opened.return_value.__enter__.return_value.read.return_value = (
                b'{"terminal_id":"t1","state":"CLOSED"}'
            )

            result = channel.close("t1")

            body = json.loads(
                opened.call_args.args[0].data.decode("utf-8")
            )

        self.assertEqual(body["operation"], "close")
        self.assertEqual(result.state, "CLOSED")

    def test_status_sends_status_operation(self):
        channel = VSCodeControlChannel("http://127.0.0.1:8766/terminal")

        with patch("application.vscode_control_channel.urlopen") as opened:
            opened.return_value.__enter__.return_value.read.return_value = (
                b'{"terminal_id":"t1","state":"RUNNING"}'
            )

            result = channel.status("t1")

            body = json.loads(
                opened.call_args.args[0].data.decode("utf-8")
            )

        self.assertEqual(body["operation"], "status")
        self.assertEqual(body["terminal_id"], "t1")
        self.assertEqual(result.state, "RUNNING")


if __name__ == "__main__":
    unittest.main()
