import threading
import unittest

from application.runtime_authority import (
    RuntimeAuthority,
    RuntimeAuthorityCommand,
    RuntimeAuthorityState,
)


class RuntimeAuthorityC37Tests(unittest.TestCase):
    def test_duplicate_start_only_one_is_accepted(self):
        authority = RuntimeAuthority()

        results = [
            authority.command(RuntimeAuthorityCommand.START),
            authority.command(RuntimeAuthorityCommand.START),
        ]

        self.assertEqual(sum(result.accepted for result in results), 1)
        self.assertEqual(authority.state(), RuntimeAuthorityState.RUNNING)

    def test_invalid_transitions_are_rejected_without_state_drift(self):
        authority = RuntimeAuthority()

        self.assertFalse(authority.command("pause").accepted)
        self.assertEqual(authority.state(), RuntimeAuthorityState.IDLE)

        self.assertTrue(authority.command("start").accepted)
        self.assertFalse(authority.command("resume").accepted)
        self.assertEqual(authority.state(), RuntimeAuthorityState.RUNNING)

    def test_stop_and_terminate_share_same_transition(self):
        authority = RuntimeAuthority()
        authority.start()

        first = authority.command("stop")
        second = authority.command("terminate")

        self.assertTrue(first.accepted)
        self.assertFalse(second.accepted)
        self.assertEqual(authority.state(), RuntimeAuthorityState.TERMINATED)

    def test_concurrent_start_has_exactly_one_winner(self):
        authority = RuntimeAuthority()
        barrier = threading.Barrier(8)
        results = []
        lock = threading.Lock()

        def worker():
            barrier.wait()
            result = authority.command("start")
            with lock:
                results.append(result)

        threads = [threading.Thread(target=worker) for _ in range(8)]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(results), 8)
        self.assertEqual(sum(result.accepted for result in results), 1)
        self.assertEqual(authority.state(), RuntimeAuthorityState.RUNNING)

    def test_concurrent_stop_and_terminate_have_one_winner(self):
        authority = RuntimeAuthority()
        authority.start()

        barrier = threading.Barrier(8)
        results = []
        lock = threading.Lock()

        def worker(command):
            barrier.wait()
            result = authority.command(command)
            with lock:
                results.append(result)

        commands = ["stop", "terminate"] * 4
        threads = [
            threading.Thread(target=worker, args=(command,))
            for command in commands
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual(len(results), 8)
        self.assertEqual(sum(result.accepted for result in results), 1)
        self.assertEqual(authority.state(), RuntimeAuthorityState.TERMINATED)


if __name__ == "__main__":
    unittest.main()
