import sys
import time
import unittest

from application.windows_process_control import (
    resume_process,
    suspend_process,
)


class WindowsProcessControlC44Tests(unittest.TestCase):
    def test_suspend_and_resume_real_process(self):
        import subprocess

        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import time; time.sleep(10)",
            ],
        )

        try:
            suspend_process(process.pid)
            time.sleep(0.2)
            self.assertIsNone(process.poll())

            resume_process(process.pid)
            process.terminate()
            process.wait(timeout=3)
            self.assertIsNotNone(process.returncode)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_missing_process_is_rejected(self):
        with self.assertRaises((OSError, RuntimeError)):
            suspend_process(2147483647)


if __name__ == "__main__":
    unittest.main()
