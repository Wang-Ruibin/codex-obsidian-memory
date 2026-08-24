from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "codex-obsidian-memory" / "scripts"


class WindowsAutomationTests(unittest.TestCase):
    def test_scheduled_tasks_use_windowless_launcher(self) -> None:
        installer = (SCRIPTS / "install-windows-tasks.ps1").read_text(encoding="utf-8-sig")
        launcher = (SCRIPTS / "run-hidden.vbs").read_text(encoding="utf-8-sig")
        self.assertIn("wscript.exe", installer)
        self.assertIn("-Hidden", installer)
        self.assertIn("run-hidden.vbs", installer)
        self.assertNotIn("-Execute $python.Source", installer)
        self.assertIn("shell.Run(command, 0, True)", launcher)
        self.assertIn("On Error Resume Next", launcher)

    def test_runner_requires_report_update_before_success_state(self) -> None:
        runner = (SCRIPTS / "routine_runner.py").read_text(encoding="utf-8-sig")
        self.assertIn("did not update the expected report", runner)
        self.assertIn("append_failure_log", runner)
        self.assertIn("CREATE_NO_WINDOW", runner)


if __name__ == "__main__":
    unittest.main()
