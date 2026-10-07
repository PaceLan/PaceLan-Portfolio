"""Real process execution and output capture."""

from dataclasses import dataclass
from pathlib import Path
import subprocess
import time
from types import MappingProxyType
from typing import Mapping

from .process_lifecycle import ProcessLifecycleState


@dataclass(frozen=True)
class ProcessCommand:
    executable: str
    argv: tuple[str, ...] = ()
    cwd: str | Path | None = None
    env: Mapping[str, str] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.executable, str) or not self.executable.strip():
            raise ValueError("executable must be a non-empty string")

        if any(not isinstance(argument, str) for argument in self.argv):
            raise TypeError("argv must contain only strings")

        if self.cwd is not None and not isinstance(self.cwd, (str, Path)):
            raise TypeError("cwd must be a string, Path, or None")

        if self.env is not None and any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in self.env.items()
        ):
            raise TypeError(
                "env must contain only string keys and values"
            )


@dataclass(frozen=True)
class CommandExecutionResult:
    command: ProcessCommand
    stdout: str
    stderr: str
    exit_code: int
    duration_seconds: float
    process_id: int | None
    process_state: ProcessLifecycleState
    execution_metadata: Mapping[str, object]

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0


class CommandExecutor:
    """Execute one explicitly specified OS process and capture its result."""

    def execute(self, command: ProcessCommand) -> CommandExecutionResult:
        if not isinstance(command, ProcessCommand):
            raise TypeError("command must be a ProcessCommand")

        started_at = time.time()
        started_monotonic = time.monotonic()

        process = subprocess.Popen(
            [command.executable, *command.argv],
            cwd=str(command.cwd) if command.cwd is not None else None,
            env=dict(command.env) if command.env is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        stdout, stderr = process.communicate()

        finished_at = time.time()
        duration = time.monotonic() - started_monotonic

        exit_code = process.returncode
        state = (
            ProcessLifecycleState.EXITED
            if exit_code == 0
            else ProcessLifecycleState.FAILED
        )

        metadata = MappingProxyType(
            {
                "executable": command.executable,
                "argv": tuple(command.argv),
                "cwd": (
                    str(command.cwd)
                    if command.cwd is not None
                    else None
                ),
                "started_at": started_at,
                "finished_at": finished_at,
            }
        )

        return CommandExecutionResult(
            command=command,
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            duration_seconds=duration,
            process_id=process.pid,
            process_state=state,
            execution_metadata=metadata,
        )


__all__ = [
    "CommandExecutionResult",
    "CommandExecutor",
    "ProcessCommand",
]
