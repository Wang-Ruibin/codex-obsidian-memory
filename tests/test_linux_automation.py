from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = (
    ROOT
    / "plugins"
    / "codex-obsidian-memory"
    / "scripts"
    / "install-linux-systemd.sh"
)


class LinuxAutomationTests(unittest.TestCase):
    def test_systemd_installer_is_user_scoped_and_persistent(self) -> None:
        script = INSTALLER.read_text(encoding="utf-8-sig")
        self.assertIn("set -euo pipefail", script)
        self.assertIn("systemctl --user", script)
        self.assertIn("Persistent=true", script)
        self.assertIn("command -v python3", script)
        self.assertIn("command -v codex", script)
        self.assertIn("--uninstall", script)
        self.assertNotIn("sudo ", script)

    def test_installer_uses_user_data_and_config_roots(self) -> None:
        script = INSTALLER.read_text(encoding="utf-8-sig")
        self.assertIn("XDG_DATA_HOME", script)
        self.assertIn("XDG_CONFIG_HOME", script)
        self.assertIn("codex-obsidian-memory/automation", script)
        self.assertIn("systemd/user", script)


if __name__ == "__main__":
    unittest.main()
