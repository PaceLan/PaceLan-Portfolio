"""Windows terminal shell resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TerminalShell:
    executable: str
    argv: tuple[str, ...] = ()


class TerminalShellResolver:
    """Resolve a configured Windows shell without starting it."""

    SUPPORTED_NAMES = frozenset(
        {
            "powershell.exe",
            "pwsh.exe",
            "cmd.exe",
        }
    )

    def resolve(self, shell: str | None = None) -> TerminalShell:
        if shell is None or not shell.strip():
            shell = os.environ.get("COMSPEC", "cmd.exe")

        value = shell.strip()
        name = Path(value).name.lower()

        if name not in self.SUPPORTED_NAMES:
            raise ValueError(f"unsupported terminal shell: {shell}")

        return TerminalShell(executable=value)


__all__ = ["TerminalShell", "TerminalShellResolver"]
