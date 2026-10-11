import unittest
import threading
from application.terminal_session import TerminalSession, TerminalSessionState
from application.terminal_session_binding import TerminalSessionBinding
from application.vscode_control_channel import TerminalControlResult
from application.vscode_terminal_executor import VSCodeTerminalCommandExecutor


class FakeChannel:
    def __init__(self, statuses, output="Python 3.x\\n",
                 output_status="CAPTURED"):
        self.statuses = list(statuses)
        self.sent = []
        self.output = output
        self.output_status = output_status

    def create(self, cwd, name="PacePilot", session_id=None):
        return TerminalControlResult("create", "t1", session_id, "RUNNING")

    def send(self, terminal_id, command, session_id=None):
        self.sent.append(command)
        return TerminalControlResult(
            "send", terminal_id, session_id, "RUNNING",
            command_id="c1", command_status="RUNNING"
        )

    def status(self, terminal_id=None, session_id=None, command_id=None):
        if len(self.statuses) > 1:
            status, code = self.statuses.pop(0)
        elif self.statuses:
            status, code = self.statuses[0]
        else:
            status, code = "UNKNOWN", None
        return TerminalControlResult(
            "status", terminal_id, session_id, "RUNNING",
            output=self.output,
            output_status=self.output_status,
            command_id=command_id,
            command_status=status,
            exit_code=code
        )


class TerminalExecutorTests(unittest.TestCase):
    def make_executor(self, statuses, **kwargs):
        channel = FakeChannel(statuses)
        return VSCodeTerminalCommandExecutor(
            channel, ".", poll_interval=0.001, **kwargs
        ), channel

    def test_success_requires_exact_zero_exit_code(self):
        executor, channel = self.make_executor([("SUCCEEDED", 0)])
        result = executor.execute("python -V")
        self.assertEqual(result, "Python 3.x\\n")
        self.assertEqual(channel.sent, ["python -V"])

    def test_captured_empty_output_is_valid(self):
        channel = FakeChannel([("SUCCEEDED", 0)], output="")
        executor = VSCodeTerminalCommandExecutor(
            channel, ".", poll_interval=0.001
        )
        self.assertEqual(executor.execute("python -c pass"), "")

    def test_unavailable_output_fails_closed(self):
        channel = FakeChannel(
            [("SUCCEEDED", 0)], output_status="UNAVAILABLE"
        )
        executor = VSCodeTerminalCommandExecutor(
            channel, ".", poll_interval=0.001
        )
        with self.assertRaisesRegex(RuntimeError, "capture unavailable"):
            executor.execute("python -V")

    def test_output_capture_error_fails_closed(self):
        channel = FakeChannel(
            [("SUCCEEDED", 0)], output_status="ERROR"
        )
        executor = VSCodeTerminalCommandExecutor(
            channel, ".", poll_interval=0.001
        )
        with self.assertRaisesRegex(RuntimeError, "capture error"):
            executor.execute("python -V")

    def test_unknown_output_status_fails_closed(self):
        channel = FakeChannel(
            [("SUCCEEDED", 0)], output_status="UNKNOWN"
        )
        executor = VSCodeTerminalCommandExecutor(
            channel, ".", poll_interval=0.001
        )
        with self.assertRaisesRegex(RuntimeError, "untrusted"):
            executor.execute("python -V")

    def test_nonzero_exit_fails(self):
        executor, _ = self.make_executor([("FAILED", 7)])
        with self.assertRaises(RuntimeError):
            executor.execute("python -c pass")

    def test_success_without_exit_code_fails(self):
        executor, _ = self.make_executor([("SUCCEEDED", None)])
        with self.assertRaises(RuntimeError):
            executor.execute("python -V")

    def test_unknown_status_does_not_count_as_success(self):
        executor, _ = self.make_executor([("UNKNOWN", None)], timeout=0.01)
        with self.assertRaises(TimeoutError):
            executor.execute("python -V")

    def test_missing_command_id_fails_closed(self):
        class NoIdChannel(FakeChannel):
            def send(self, terminal_id, command, session_id=None):
                return TerminalControlResult(
                    "send", terminal_id, session_id, "RUNNING",
                    command_status="RUNNING"
                )
        executor = VSCodeTerminalCommandExecutor(NoIdChannel([]), ".")
        with self.assertRaisesRegex(RuntimeError, "no command_id"):
            executor.execute("python -V")

    def test_empty_command_rejected(self):
        executor, _ = self.make_executor([])
        with self.assertRaises(ValueError):
            executor.execute("  ")


    def test_concurrent_execute_calls_are_serialized(self):
        first_send_entered = threading.Event()
        release_first = threading.Event()
        second_send_entered = threading.Event()
        send_guard = threading.Lock()
        send_count = [0]

        class BlockingChannel(FakeChannel):
            def send(self, terminal_id, command, session_id=None):
                with send_guard:
                    send_count[0] += 1
                    index = send_count[0]

                if index == 1:
                    first_send_entered.set()
                    if not release_first.wait(3):
                        raise TimeoutError("test did not release first send")
                else:
                    second_send_entered.set()

                return TerminalControlResult(
                    "send", terminal_id, session_id, "RUNNING",
                    command_id=f"c{index}", command_status="RUNNING"
                )

            def status(self, terminal_id=None, session_id=None, command_id=None):
                return TerminalControlResult(
                    "status", terminal_id, session_id, "RUNNING",
                    output=command_id,
                    output_status="CAPTURED",
                    command_id=command_id,
                    command_status="SUCCEEDED",
                    exit_code=0
                )

        channel = BlockingChannel([])
        executor = VSCodeTerminalCommandExecutor(
            channel, ".", timeout=1, poll_interval=0.001
        )
        results = {}
        errors = []

        def run(name):
            try:
                results[name] = executor.execute(name)
            except Exception as exc:
                errors.append(exc)

        first = threading.Thread(target=run, args=("first",))
        second = threading.Thread(target=run, args=("second",))
        first.start()
        self.assertTrue(first_send_entered.wait(1), "first send did not start")
        second.start()

        try:
            self.assertFalse(
                second_send_entered.wait(0.1),
                "second command entered send before first command was released"
            )
        finally:
            release_first.set()

        first.join(2)
        second.join(2)
        self.assertFalse(first.is_alive(), "first execution thread did not finish")
        self.assertFalse(second.is_alive(), "second execution thread did not finish")
        self.assertEqual(errors, [])
        self.assertEqual(results, {"first": "c1", "second": "c2"})


if __name__ == "__main__":
    unittest.main()
