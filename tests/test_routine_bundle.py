from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-obsidian-memory"
SCRIPTS = PLUGIN / "scripts"


class InstalledRoutineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name).resolve()
        self.vault = self.root / "知识库 vault"
        self.config = self.root / "state/config.json"
        self.env = {**os.environ, "CODEX_HOME": str(self.root / "codex"),
                    "CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config), "PYTHONUTF8": "0"}
        self.env.pop("PYTHONPATH", None)
        result = self.run_python(SCRIPTS / "memoryctl.py", "init", "--local-only",
                                 "--vault", str(self.vault), "--locale", "zh-CN", "--no-writable-root")
        self.assertEqual(result.returncode, 0, result.stderr)
        # An adopted layout with spaces and Unicode must work in copied bundles.
        replacements = {"10-memory": "知识区", "20-projects": "项目区",
                        "30-reusable": "共享经验区", "40-conversations": "对话区"}
        for old, new in replacements.items():
            (self.vault / old).rename(self.vault / new)
        for path in self.vault.rglob("*.md"):
            text = path.read_text(encoding="utf-8")
            for old, new in replacements.items():
                text = text.replace(old, new)
            path.write_text(text, encoding="utf-8")
        self.settings = json.loads(self.config.read_text(encoding="utf-8"))
        for key, value in self.settings["paths"].items():
            for old, new in replacements.items():
                value = value.replace(old, new)
            self.settings["paths"][key] = value
        self.config.write_text(json.dumps(self.settings, ensure_ascii=False), encoding="utf-8")
        work = self.root / "local work"
        work.mkdir()
        registered = self.run_python(SCRIPTS / "memoryctl.py", "local-register", "--path", str(work))
        self.assertEqual(registered.returncode, 0, registered.stderr)
        conversations = self.vault / self.settings["paths"]["conversations_dir"]
        (conversations / "fixture.md").write_text(
            "---\ntype: conversation\nconversation_id: codex:automation-fixture\n---\n"
            "[[对话区/index]]\nPRIVATE CHAT SENTINEL\n", encoding="utf-8")
        with (self.vault / self.settings["paths"]["conversation_index"]).open("a", encoding="utf-8") as handle:
            handle.write("\n[[对话区/fixture]]\n")
        self.fake_script = self.root / "fake_codex.py"
        self.fake_script.write_text(
            "import os, sys, time\nfrom pathlib import Path\n"
            "Path(os.environ['FAKE_PROMPT']).write_text(sys.stdin.read(), encoding='utf-8')\n"
            "action = os.environ.get('FAKE_ACTION', 'update')\n"
            "if action == 'fail': sys.exit(7)\n"
            "if action == 'update':\n"
            "    with Path(os.environ['FAKE_REPORT']).open('a', encoding='utf-8') as stream:\n"
            "        stream.write(f'\\n已生成 {time.time_ns()}\\n')\n", encoding="utf-8")
        self.fake = self.root / ("fake-codex.cmd" if os.name == "nt" else "fake-codex")
        if os.name == "nt":
            self.fake.write_text(f'@echo off\r\n"{sys.executable}" -X utf8 "{self.fake_script}" %*\r\n', encoding="utf-8")
        else:
            self.fake.write_text(f'#!/bin/sh\nexec {shlex.quote(sys.executable)} -X utf8 {shlex.quote(str(self.fake_script))} "$@"\n', encoding="utf-8")
            self.fake.chmod(0o700)
        self.env["FAKE_PROMPT"] = str(self.root / "captured-prompt.txt")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_python(self, script: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, "-X", "utf8", "-B", str(script), *args],
                              cwd=self.root, env=self.env, capture_output=True, text=True,
                              encoding="utf-8", timeout=30)

    def stage_bundle(self, platform: str) -> Path:
        installer = SCRIPTS / ("install-windows-tasks.ps1" if platform == "windows" else "install-linux-systemd.sh")
        text = installer.read_text(encoding="utf-8-sig")
        pattern = (r"Join-Path \$PSScriptRoot '([^']+\.py)'" if platform == "windows"
                   else r'install -m 0644 "\$\{script_dir\}/([^"/]+\.py)"')
        names = re.findall(pattern, text)
        self.assertTrue(names, "No installer payload found")
        bundle = self.root / platform
        bundle.mkdir()
        for name in names:
            shutil.copy2(SCRIPTS / name, bundle / name)
        shutil.copytree(PLUGIN / "assets/prompts", bundle / "prompts")
        shutil.copy2(SCRIPTS / "run-hidden.vbs", bundle / "run-hidden.vbs")
        return bundle

    def test_both_installer_payloads_validate_current_custom_layout(self) -> None:
        for platform in ("windows", "linux"):
            with self.subTest(platform=platform):
                bundle = self.stage_bundle(platform)
                result = self.run_python(bundle / "validate_vault.py")
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                report = json.loads(result.stdout)
                self.assertEqual(report["project_homes"], 1)
                self.assertEqual(report["conversation_notes"], 1)
                self.assertEqual(report["conversation_errors"], [])
                self.assertEqual(report["local_registration_errors"], [])

    def test_copied_runner_preserves_failure_gates_and_passes_configured_paths(self) -> None:
        bundle = self.stage_bundle("windows")
        state_path = self.config.parent / "routines.json"
        state_path.write_text('{"last_monthly_period": "2000-01"}\n', encoding="utf-8")
        original = state_path.read_bytes()
        self.env["FAKE_REPORT"] = str(self.vault / self.settings["paths"]["weekly_brief"])
        self.env["FAKE_ACTION"] = "fail"
        failed = self.run_python(bundle / "routine_runner.py", "weekly", "--codex", str(self.fake))
        self.assertNotEqual(failed.returncode, 0)
        self.assertEqual(state_path.read_bytes(), original)
        self.env["FAKE_ACTION"] = "unchanged"
        unchanged = self.run_python(bundle / "routine_runner.py", "weekly", "--codex", str(self.fake))
        self.assertNotEqual(unchanged.returncode, 0)
        self.assertIn("did not update the expected report", unchanged.stderr)
        self.assertEqual(state_path.read_bytes(), original)
        self.env["FAKE_ACTION"] = "update"
        success = self.run_python(bundle / "routine_runner.py", "weekly", "--codex", str(self.fake))
        self.assertEqual(success.returncode, 0, success.stdout + success.stderr)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertRegex(state["last_weekly_period"], r"^\d{4}-W\d{2}$")
        self.assertEqual(state["last_monthly_period"], "2000-01")
        prompt = Path(self.env["FAKE_PROMPT"]).read_text(encoding="utf-8")
        for key in ("projects_dir", "reuse_index", "conversations_dir"):
            self.assertIn(str(self.vault / self.settings["paths"][key]), prompt)
        self.assertIn(str(bundle / "validate_vault.py"), prompt)
        self.assertIn("Simplified Chinese", prompt)
        self.assertNotIn("PRIVATE CHAT SENTINEL", prompt)
        duplicate = self.run_python(bundle / "routine_runner.py", "weekly", "--codex", str(self.fake))
        self.assertEqual(duplicate.returncode, 0, duplicate.stderr)
        self.assertFalse(json.loads(duplicate.stdout)["run"])

        original = state_path.read_bytes()
        broken = self.vault / "broken.md"
        broken.write_text("[[nonexistent]]\n", encoding="utf-8")
        self.env["FAKE_REPORT"] = str(self.vault / self.settings["paths"]["monthly_audit"])
        failed_audit = self.run_python(bundle / "routine_runner.py", "monthly", "--codex", str(self.fake))
        self.assertNotEqual(failed_audit.returncode, 0)
        self.assertIn("Vault validation failed", failed_audit.stderr)
        self.assertEqual(state_path.read_bytes(), original)
        broken.unlink()
        success = self.run_python(bundle / "routine_runner.py", "monthly", "--codex", str(self.fake))
        self.assertEqual(success.returncode, 0, success.stdout + success.stderr)
        state = json.loads(state_path.read_text(encoding="utf-8"))
        self.assertRegex(state["last_monthly_period"], r"^\d{4}-\d{2}$")

    @unittest.skipUnless(os.name == "nt", "Windows WScript launcher")
    def test_hidden_launcher_uses_pinned_codex_without_path(self) -> None:
        bundle = self.stage_bundle("windows")
        self.env["FAKE_REPORT"] = str(self.vault / self.settings["paths"]["weekly_brief"])
        self.env["PATH"] = str(self.root / "no-tools")
        result = subprocess.run(
            [str(Path(os.environ["SystemRoot"]) / "System32/wscript.exe"), "//B", "//Nologo",
             str(bundle / "run-hidden.vbs"), sys.executable, str(bundle / "routine_runner.py"),
             "weekly", str(self.fake)], cwd=self.root, env=self.env, capture_output=True,
            text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        state = json.loads((self.config.parent / "routines.json").read_text(encoding="utf-8"))
        self.assertIn("last_weekly_period", state)


if __name__ == "__main__":
    unittest.main()
