from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-obsidian-memory"
MEMORYCTL = PLUGIN / "scripts" / "memoryctl.py"
RUNNER = PLUGIN / "scripts" / "routine_runner.py"


class CliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.config = self.root / "state" / "config.json"
        self.environment = os.environ.copy()
        self.environment["CODEX_OBSIDIAN_MEMORY_CONFIG"] = str(self.config)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(MEMORYCTL), *args],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            env=self.environment,
            check=False,
        )

    def test_init_validate_and_uninstall_never_delete_vault(self) -> None:
        vault = self.root / "vault"
        initialized = self.run_cli(
            "init",
            "--vault",
            str(vault),
            "--github-owner",
            "Example",
            "--no-writable-root",
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        self.assertEqual(self.run_cli("validate").returncode, 0)
        self.assertTrue(vault.is_dir())
        uninstalled = self.run_cli("uninstall")
        self.assertEqual(uninstalled.returncode, 0, uninstalled.stderr)
        self.assertTrue(vault.is_dir())
        self.assertFalse(self.config.exists())

    def test_adopt_custom_layout_without_copying_default_template(self) -> None:
        vault = self.root / "existing"
        knowledge = vault / "知识"
        projects = vault / "项目"
        knowledge.mkdir(parents=True)
        projects.mkdir()
        (vault / "AGENTS.md").write_text("# Protocol\n", encoding="utf-8")
        (vault / "首页.md").write_text("[[知识/全局]]\n[[知识/维护]]\n[[项目/总览]]\n", encoding="utf-8")
        (knowledge / "全局.md").write_text("[[../首页|Home]]\n", encoding="utf-8")
        (knowledge / "维护.md").write_text("[[../首页|Home]]\n[[模板]]\n", encoding="utf-8")
        (knowledge / "模板.md").write_text("[[维护]]\n", encoding="utf-8")
        (projects / "总览.md").write_text("[[../首页|Home]]\n", encoding="utf-8")
        result = self.run_cli(
            "init",
            "--vault",
            str(vault),
            "--github-owner",
            "Example",
            "--no-template",
            "--no-writable-root",
            "--path",
            "home=首页.md",
            "--path",
            "global_memory=知识/全局.md",
            "--path",
            "maintenance=知识/维护.md",
            "--path",
            "template=知识/模板.md",
            "--path",
            "project_index=项目/总览.md",
            "--path",
            "projects_dir=项目",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((vault / "00-memory-home.md").exists())
        self.assertEqual(self.run_cli("validate").returncode, 0)

    def test_simplified_chinese_locale_installs_matching_schema(self) -> None:
        vault = self.root / "zh-vault"
        result = self.run_cli(
            "init",
            "--vault",
            str(vault),
            "--github-owner",
            "Example",
            "--locale",
            "zh-CN",
            "--no-writable-root",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        home = (vault / "00-memory-home.md").read_text(encoding="utf-8")
        self.assertIn("# 记忆首页", home)
        config = json.loads(self.config.read_text(encoding="utf-8"))
        self.assertEqual(config["locale"], "zh-CN")
        self.assertEqual(self.run_cli("validate").returncode, 0)

    def test_branch_validation_distinguishes_case_but_rejects_exact_duplicates(self) -> None:
        vault = self.root / "vault"
        self.assertEqual(self.run_cli("init", "--vault", str(vault), "--github-owner",
                                     "Example", "--no-writable-root").returncode, 0)
        folder = vault / "20-projects" / "demo"
        folder.mkdir()
        index = vault / "20-projects" / "project-index.md"
        with index.open("a", encoding="utf-8") as handle:
            handle.write("\n[[20-projects/demo/upper]]\n[[20-projects/demo/lower]]\n")
        for filename, branch in (("upper", "Release"), ("lower", "release")):
            (folder / f"{filename}.md").write_text(
                f"---\ntype: branch\ngithub_repo: Example/demo\nworking_branch: {branch}\n---\n"
                "[[20-projects/project-index]]\n", encoding="utf-8")
        valid = self.run_cli("validate")
        self.assertEqual(valid.returncode, 0, valid.stdout + valid.stderr)
        duplicate = folder / "duplicate.md"
        duplicate.write_text((folder / "upper.md").read_text(encoding="utf-8").replace(
            "Example/demo", "example/DEMO"), encoding="utf-8")
        invalid = self.run_cli("validate")
        self.assertNotEqual(invalid.returncode, 0)
        self.assertIn("example/demo:Release", json.loads(invalid.stdout)["duplicate_branch_identities"])

    def make_fake_codex(self, exit_code: int, report: Path | None = None) -> Path:
        update = ""
        if report is not None:
            escaped_report = str(report).replace("'", "\\'")
            code = (
                "import time; from pathlib import Path; "
                f"Path(r'{escaped_report}').write_text(f'# updated {{time.time_ns()}}\\n', "
                "encoding='utf-8')"
            )
            update = f'"{sys.executable}" -c "{code}"\n'
        if os.name == "nt":
            path = self.root / f"codex-{exit_code}.cmd"
            path.write_text(
                "@echo fake codex\r\n"
                + ("@" + update.replace("\n", "\r\n") if update else "")
                + f"@exit /b {exit_code}\r\n",
                encoding="utf-8",
            )
        else:
            path = self.root / f"codex-{exit_code}"
            path.write_text(
                "#!/bin/sh\necho fake codex\n" + update + f"exit {exit_code}\n",
                encoding="utf-8",
            )
            path.chmod(path.stat().st_mode | stat.S_IXUSR)
        return path

    def test_routine_marks_only_successful_periods(self) -> None:
        vault = self.root / "vault"
        initialized = self.run_cli(
            "init",
            "--vault",
            str(vault),
            "--github-owner",
            "Example",
            "--no-writable-root",
        )
        self.assertEqual(initialized.returncode, 0, initialized.stderr)
        busy_lock = self.config.parent / "weekly.lock"
        busy_lock.write_text("test", encoding="ascii")
        busy = subprocess.run(
            [sys.executable, str(RUNNER), "weekly", "--dry-run"],
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )
        self.assertEqual(busy.returncode, 0, busy.stderr)
        self.assertIn('"busy": true', busy.stdout)
        busy_lock.unlink()
        failure = subprocess.run(
            [sys.executable, str(RUNNER), "weekly", "--codex", str(self.make_fake_codex(7))],
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )
        self.assertNotEqual(failure.returncode, 0)
        failure_log = (self.config.parent / "logs" / "weekly.log").read_text(encoding="utf-8")
        self.assertIn("failed=", failure_log)
        self.assertFalse((self.config.parent / "routines.json").exists())
        unchanged = subprocess.run(
            [sys.executable, str(RUNNER), "weekly", "--codex", str(self.make_fake_codex(0))],
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )
        self.assertNotEqual(unchanged.returncode, 0)
        self.assertIn("did not update the expected report", unchanged.stderr)
        self.assertFalse((self.config.parent / "routines.json").exists())
        weekly_report = vault / "10-memory" / "weekly-brief.md"
        success = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "weekly",
                "--codex",
                str(self.make_fake_codex(0, weekly_report)),
            ],
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )
        self.assertEqual(success.returncode, 0, success.stderr)
        state = json.loads((self.config.parent / "routines.json").read_text(encoding="utf-8"))
        self.assertRegex(state["last_weekly_period"], r"^\d{4}-W\d{2}$")

        broken = vault / "broken.md"
        broken.write_text("# Broken\n\n[[missing-note]]\n", encoding="utf-8")
        monthly_report = vault / "10-memory" / "monthly-audit.md"
        unhealthy_monthly = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "monthly",
                "--codex",
                str(self.make_fake_codex(0, monthly_report)),
            ],
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )
        self.assertNotEqual(unhealthy_monthly.returncode, 0)
        state = json.loads((self.config.parent / "routines.json").read_text(encoding="utf-8"))
        self.assertNotIn("last_monthly_period", state)
        broken.unlink()
        healthy_monthly = subprocess.run(
            [
                sys.executable,
                str(RUNNER),
                "monthly",
                "--codex",
                str(self.make_fake_codex(0, monthly_report)),
            ],
            text=True,
            capture_output=True,
            env=self.environment,
            check=False,
        )
        self.assertEqual(healthy_monthly.returncode, 0, healthy_monthly.stderr)
        state = json.loads((self.config.parent / "routines.json").read_text(encoding="utf-8"))
        self.assertRegex(state["last_monthly_period"], r"^\d{4}-\d{2}$")


if __name__ == "__main__":
    unittest.main()
