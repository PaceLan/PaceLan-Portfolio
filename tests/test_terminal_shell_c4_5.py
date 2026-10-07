import os
import unittest
from unittest.mock import patch

from application.terminal_shell import TerminalShell, TerminalShellResolver


class TerminalShellResolverTests(unittest.TestCase):
    def setUp(self):
        self.resolver = TerminalShellResolver()

    def test_resolves_powershell(self):
        result = self.resolver.resolve("powershell.exe")

        self.assertEqual(result, TerminalShell("powershell.exe"))

    def test_resolves_pwsh(self):
        result = self.resolver.resolve("pwsh.exe")

        self.assertEqual(result, TerminalShell("pwsh.exe"))

    def test_resolves_cmd(self):
        result = self.resolver.resolve("cmd.exe")

        self.assertEqual(result, TerminalShell("cmd.exe"))

    def test_resolves_explicit_shell_path(self):
        result = self.resolver.resolve(
            r"C:\Windows\System32\cmd.exe"
        )

        self.assertEqual(
            result,
            TerminalShell(r"C:\Windows\System32\cmd.exe"),
        )

    def test_default_uses_comspec(self):
        with patch.dict(os.environ, {"COMSPEC": r"C:\Windows\System32\cmd.exe"}):
            result = self.resolver.resolve()

        self.assertEqual(
            result,
            TerminalShell(r"C:\Windows\System32\cmd.exe"),
        )

    def test_unknown_shell_is_rejected(self):
        with self.assertRaises(ValueError):
            self.resolver.resolve("unknown-shell.exe")

    def test_empty_shell_uses_default(self):
        with patch.dict(os.environ, {"COMSPEC": "cmd.exe"}):
            result = self.resolver.resolve("  ")

        self.assertEqual(result, TerminalShell("cmd.exe"))


if __name__ == "__main__":
    unittest.main()
