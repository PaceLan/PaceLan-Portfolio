"""Lifecycle control for real operating-system processes."""

from dataclasses import replace
import subprocess
import time

from .process_lifecycle import ProcessLifecycleState, ProcessSnapshot
from .windows_process_control import resume_process, suspend_process


class ProcessLifecycleController:
    """Control and observe one real OS process."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._snapshot = ProcessSnapshot(
            process_id=None,
            state=ProcessLifecycleState.EXITED,
        )

    def start(
        self,
        executable: str,
        argv: tuple[str, ...] = (),
        *,
        cwd: str | None = None,
    ) -> ProcessSnapshot:
        if self._process is not None and self._process.poll() is None:
            raise RuntimeError("a process is already running")

        started_at = time.time()
        try:
            process = subprocess.Popen(
                [executable, *argv],
                cwd=cwd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,

            )
        except OSError:
            self._process = None
            self._snapshot = ProcessSnapshot(
                process_id=None,
                state=ProcessLifecycleState.FAILED,
                started_at=started_at,
            )
            raise

        self._process = process
        self._snapshot = ProcessSnapshot(
            process_id=process.pid,
            state=ProcessLifecycleState.RUNNING,
            started_at=started_at,
        )
        return self._snapshot

    def snapshot(self) -> ProcessSnapshot:
        process = self._process
        if process is None:
            return self._snapshot

        returncode = process.poll()
        if returncode is None:
            return self._snapshot

        state = (
            ProcessLifecycleState.EXITED
            if returncode == 0
            else ProcessLifecycleState.FAILED
        )
        self._snapshot = replace(
            self._snapshot,
            state=state,
            exit_code=returncode,
            finished_at=time.time(),
        )
        return self._snapshot

    def pause(self) -> ProcessSnapshot:
        """Suspend the current real OS process."""
        process = self._process
        if process is None:
            return self._snapshot

        if process.poll() is not None:
            return self.snapshot()

        suspend_process(process.pid)
        self._snapshot = replace(
            self._snapshot,
            state=ProcessLifecycleState.PAUSED,
        )
        return self._snapshot

    def resume(self) -> ProcessSnapshot:
        """Resume the current real OS process."""
        process = self._process
        if process is None:
            return self._snapshot

        if process.poll() is not None:
            return self.snapshot()

        resume_process(process.pid)
        self._snapshot = replace(
            self._snapshot,
            state=ProcessLifecycleState.RUNNING,
        )
        return self._snapshot
    def terminate(self) -> ProcessSnapshot:
        """Request termination of the current real OS process."""
        process = self._process
        if process is None:
            return self._snapshot

        if process.poll() is None:
            process.terminate()
            process.wait()

        return self.snapshot()
    @property
    def process(self) -> subprocess.Popen[str] | None:
        return self._process


__all__ = ["ProcessLifecycleController"]
