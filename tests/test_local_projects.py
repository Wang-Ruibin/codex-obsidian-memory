from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins/codex-obsidian-memory/scripts"
sys.path.insert(0, str(SCRIPTS))
import hook
import local_projects
from memory_core import markdown_snapshot
from reuse_memory import search


class LocalProjectTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "vault"
        self.workspace = self.root / "work"
        self.workspace.mkdir()
        self.config_file = self.root / "state/config.json"
        self.env = {**os.environ, "CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_file)}
        result = self.cli("init", "--local-only", "--vault", str(self.vault), "--no-writable-root")
        self.assertEqual(result.returncode, 0, result.stderr)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPTS / "memoryctl.py"), *args], env=self.env,
                              capture_output=True, text=True, encoding="utf-8", check=False)

    def config(self) -> dict:
        return json.loads(self.config_file.read_text(encoding="utf-8"))

    def register(self, path: Path | None = None, *extra: str) -> dict:
        result = self.cli("local-register", "--path", str(path or self.workspace), *extra)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def event(self, name: str, cwd: Path | None = None, **extra) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(SCRIPTS / "hook.py")], env=self.env,
                              input=json.dumps({"hook_event_name": name, "cwd": str(cwd or self.workspace), **extra}),
                              capture_output=True, text=True, encoding="utf-8", check=False)

    def git(self, *args: str, cwd: Path | None = None) -> None:
        subprocess.run(["git", "-C", str(cwd or self.workspace), *args], check=True, capture_output=True)

    def test_local_only_init_requires_no_git_or_github(self) -> None:
        self.assertEqual(self.config()["scope_mode"], "local-only")
        self.assertEqual(self.config()["github_owners"], [])
        self.assertEqual(self.cli("validate").returncode, 0)
        with patch("memory_core.git_value", return_value=""), patch.object(hook, "repository_identity", return_value=("", "")):
            self.assertFalse(hook.resolve_scope({"cwd": str(self.workspace)}, self.config(), self.vault).eligible)
        self.assertNotEqual(self.cli("init", "--local-only", "--github-owner", "Example", "--vault",
                                     str(self.root / "invalid"), "--no-writable-root").returncode, 0)

    def test_registration_and_current_context_work_without_git_executable(self) -> None:
        args = Namespace(command="local-register", path=self.workspace, name="No Git", project_id=None)
        with patch.dict(os.environ, self.env), patch("memory_core.subprocess.run", side_effect=FileNotFoundError), redirect_stdout(StringIO()) as output:
            self.assertEqual(local_projects.command_local(args), 0)
        result = json.loads(output.getvalue())
        self.assertIn("No Git", result["context"])
        self.assertIn("branch=unidentified", result["context"])
        self.assertEqual(len(list((self.vault / result["project"]["project_home"]).parent.glob("*.md"))), 1)

    def test_mixed_configuration_retrieves_both_local_and_github_sources(self) -> None:
        entry = self.register()["project"]
        local = self.vault / entry["project_home"]
        with local.open("a", encoding="utf-8") as handle:
            handle.write("\nsharedtech evidence from a local project\n")
        remote = self.vault / "20-projects/remote/home.md"
        remote.parent.mkdir()
        remote.write_text("---\ntype: project\ngithub_repo: Example/remote\n---\n"
                          "# sharedtech GitHub evidence\n", encoding="utf-8")
        config = self.config()
        config.update(scope_mode="github-owner", github_owners=["Example"])
        results = search(self.vault, config, "sharedtech", "projects")["results"]
        self.assertEqual({hit["repository"] for hit in results}, {"", "Example/remote"})
        self.assertEqual({hit["project_id"] for hit in results}, {"", entry["project_id"]})

    def test_malformed_registry_produces_validation_error_not_traceback(self) -> None:
        config = self.config()
        config["local_projects"] = ["invalid"]
        self.config_file.write_text(json.dumps(config), encoding="utf-8")
        result = self.cli("validate")
        self.assertEqual(result.returncode, 1)
        self.assertTrue(json.loads(result.stdout)["local_registration_errors"])
        self.assertNotIn("Traceback", result.stderr)

    def test_registration_loads_current_turn_and_future_sessions(self) -> None:
        self.assertFalse(self.event("UserPromptSubmit", prompt="Could memory help? 为当前项目启用记忆").stdout)
        with (self.vault / "10-memory/global-memory.md").open("a", encoding="utf-8") as handle:
            handle.write("\nSTABLE GLOBAL PREFERENCE\n")
        result = self.register(None, "--name", "本地实验")
        self.assertIn("STABLE GLOBAL PREFERENCE", result["context"])
        self.assertIn("project_id=local:", result["context"])
        self.assertIn("current conversation", result["context"])
        page = self.vault / result["project"]["project_home"]
        self.assertTrue(page.exists())
        self.assertNotIn("github_repo:", page.read_text(encoding="utf-8"))
        self.assertEqual(len(list(page.parent.glob("*.md"))), 1)
        with page.open("a", encoding="utf-8") as handle:
            handle.write("\nPROJECT MEMORY PERSISTS\n")
        for event in ("UserPromptSubmit", "SessionStart", "SubagentStart"):
            loaded = self.event(event)
            self.assertEqual(loaded.returncode, 0, loaded.stderr)
            self.assertIn("PROJECT MEMORY PERSISTS", json.loads(loaded.stdout)["hookSpecificOutput"]["additionalContext"])
        self.assertEqual(self.cli("context", "--cwd", str(self.workspace)).returncode, 0)
        self.assertEqual(self.cli("validate").returncode, 0)

    def test_first_turn_stop_requires_registration_writeback_disclosure(self) -> None:
        result = self.register()
        denied = self.event("Stop", last_assistant_message="Done <!-- obsidian-memory-reviewed -->")
        self.assertEqual(json.loads(denied.stdout)["decision"], "block")
        for path in result["changed_notes"]:
            self.assertIn(path, json.loads(denied.stdout)["reason"])
        reply = "## Knowledge-base writeback review\n" + "\n".join(
            f"- {path}: registered the local project and added its exact identity/link." for path in result["changed_notes"]
        ) + "\n<!-- obsidian-memory-writeback-disclosed -->\n<!-- obsidian-memory-reviewed -->"
        accepted = self.event("Stop", last_assistant_message=reply)
        self.assertTrue(json.loads(accepted.stdout)["continue"])
        self.assertNotIn("pending_review", self.config()["local_projects"][0])
        self.assertTrue(json.loads(self.event("Stop", last_assistant_message="Done <!-- obsidian-memory-reviewed -->").stdout)["continue"])

    def test_repeated_registration_does_not_duplicate_or_overwrite_notes(self) -> None:
        first = self.register()
        before = markdown_snapshot(self.vault)
        second = self.register()
        self.assertEqual(first["project"]["project_id"], second["project"]["project_id"])
        self.assertEqual(second["changed_notes"], [])
        self.assertEqual(before, markdown_snapshot(self.vault))
        self.assertEqual(len(self.config()["local_projects"]), 1)

    def test_same_basename_and_directory_boundaries(self) -> None:
        other = self.root / "other/work"
        other.mkdir(parents=True)
        one = self.register()["project"]
        two = self.register(other)["project"]
        self.assertNotEqual(one["project_id"], two["project_id"])
        sibling = self.root / "work-extra"
        sibling.mkdir()
        self.assertFalse(self.event("UserPromptSubmit", sibling).stdout)
        child = self.workspace / "src"
        child.mkdir()
        self.assertIn(one["project_id"], self.event("UserPromptSubmit", child).stdout)

    def test_disabled_nested_project_does_not_fall_back_to_parent(self) -> None:
        self.register()
        child = self.workspace / "nested"
        child.mkdir()
        entry = self.register(child)["project"]
        before = markdown_snapshot(self.vault)
        self.assertEqual(self.cli("local-disable", entry["project_id"]).returncode, 0)
        self.assertFalse(self.event("UserPromptSubmit", child).stdout)
        self.assertTrue(json.loads(self.event("Stop", child).stdout)["continue"])
        self.assertEqual(before, markdown_snapshot(self.vault))
        enabled = self.cli("local-enable", entry["project_id"])
        self.assertIn("context", json.loads(enabled.stdout))
        self.assertIn(entry["project_id"], self.event("UserPromptSubmit", child).stdout)

    def test_nested_git_repository_does_not_inherit_parent_registration(self) -> None:
        self.register()
        nested = self.workspace / "nested"
        nested.mkdir()
        self.git("init", "-q", cwd=nested)
        self.assertFalse(self.event("UserPromptSubmit", nested).stdout)
        own = self.register(nested)
        self.assertIn(own["project"]["project_id"], self.event("UserPromptSubmit", nested).stdout)

    def test_move_keeps_id_and_notes_without_moving_user_files(self) -> None:
        original = self.register()["project"]
        destination = self.root / "renamed"
        self.workspace.rename(destination)
        before = markdown_snapshot(self.vault)
        moved = self.cli("local-move", original["project_id"], "--path", str(destination))
        self.assertEqual(moved.returncode, 0, moved.stderr)
        self.assertEqual(json.loads(moved.stdout)["project"]["project_id"], original["project_id"])
        self.assertEqual(before, markdown_snapshot(self.vault))
        self.workspace.mkdir()
        self.assertFalse(self.event("UserPromptSubmit").stdout)
        self.assertIn(original["project_id"], self.event("UserPromptSubmit", destination).stdout)

    def test_explicit_existing_id_attachment_reuses_vault_home(self) -> None:
        original = self.register()["project"]
        config = self.config()
        config["local_projects"] = []  # Simulate another environment's independent configuration.
        self.config_file.write_text(json.dumps(config), encoding="utf-8")
        before = markdown_snapshot(self.vault)
        attached = self.register(None, "--project-id", original["project_id"])
        self.assertEqual(attached["project"]["project_home"], original["project_home"])
        self.assertEqual(before, markdown_snapshot(self.vault))

    def test_git_branch_identity_is_exact_and_no_other_branch_is_loaded(self) -> None:
        self.git("init", "-q")
        self.git("symbolic-ref", "HEAD", "refs/heads/Release")
        entry = self.register()["project"]
        page = self.vault / entry["project_home"]
        for filename, branch, identity, marker in (
                ("upper", "Release", entry["project_id"], "RIGHT BRANCH"),
                ("lower", "release", entry["project_id"], "WRONG CASE"),
                ("foreign", "Release", "local:" + "0" * 32, "FOREIGN ID")):
            (page.parent / f"{filename}.md").write_text(
                f"---\ntype: branch\nproject_id: {identity}\nworking_branch: {branch}\n---\n{marker}\n", encoding="utf-8")
            with page.open("a", encoding="utf-8") as handle:
                handle.write(f"\n[[{filename}]]\n")
        context = json.loads(self.event("UserPromptSubmit").stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertIn("RIGHT BRANCH", context)
        self.assertNotIn("WRONG CASE", context)
        self.assertNotIn("FOREIGN ID", context)

    def test_local_experience_search_and_disable_withhold_derived_lesson(self) -> None:
        entry = self.register()["project"]
        page = self.vault / entry["project_home"]
        with page.open("a", encoding="utf-8") as handle:
            handle.write("\nPortable offline evidence\n")
        lesson = self.vault / "10-memory/reusable/local.md"
        lesson.write_text("---\ntype: reusable-memory\nstatus: verified\nsummary: Portable offline result\n"
                          f"keywords: portable offline\nsource_project_id: {entry['project_id']}\n"
                          f"source_note: {entry['project_home']}\nsource_branch:\nverified_on: 2026-01-01\n"
                          "---\n# Portable method\n[[index]]\n", encoding="utf-8")
        results = search(self.vault, self.config(), "offline")
        self.assertEqual(results["searched"], ["shared"])
        self.assertEqual(results["results"][0]["project_id"], entry["project_id"])
        self.assertEqual(results["results"][0]["repository"], "")
        self.assertEqual(self.cli("validate").returncode, 0)
        self.cli("local-disable", entry["project_id"])
        self.assertEqual(search(self.vault, self.config(), "offline")["results"], [])
        self.assertNotEqual(self.cli("read", entry["project_home"], "--cwd", str(self.workspace)).returncode, 0)

    def test_excluded_github_origin_cannot_bypass_scope_as_local(self) -> None:
        entry = self.register()["project"]
        self.git("init", "-q")
        self.git("remote", "add", "origin", "git@github.com:Example/excluded.git")
        config = self.config()
        config["excluded_repositories"] = ["Example/excluded"]
        self.config_file.write_text(json.dumps(config), encoding="utf-8")
        self.assertFalse(self.event("UserPromptSubmit").stdout)
        self.assertNotEqual(self.cli("local-register", "--path", str(self.workspace)).returncode, 0)
        self.assertEqual(search(self.vault, config, "Goal", "projects")["results"], [])

    def test_local_id_survives_adding_github_origin(self) -> None:
        entry = self.register()["project"]
        self.git("init", "-q")
        self.git("remote", "add", "origin", "git@github.com:Example/published.git")
        self.assertIn(entry["project_id"], self.event("UserPromptSubmit").stdout)
        self.assertEqual(len(self.config()["local_projects"]), 1)

    def test_scope_refuses_vault_and_ancestors_and_rejects_wrong_home(self) -> None:
        for path in (self.vault, self.root, Path(self.root.anchor)):
            self.assertNotEqual(self.cli("local-register", "--path", str(path)).returncode, 0)
        entry = self.register()["project"]
        page = self.vault / entry["project_home"]
        page.write_text("---\ntype: project\ngithub_repo: Example/wrong\n---\n", encoding="utf-8")
        self.assertNotEqual(self.event("UserPromptSubmit").returncode, 0)
        validation = self.cli("validate")
        self.assertNotEqual(validation.returncode, 0)
        self.assertTrue(json.loads(validation.stdout)["local_registration_errors"])

    def test_local_identity_duplicates_and_mixed_identity_are_reported(self) -> None:
        entry = self.register()["project"]
        page = self.vault / entry["project_home"]
        duplicate = page.with_name("copy.md")
        shutil.copy2(page, duplicate)
        report = json.loads(self.cli("validate").stdout)
        self.assertIn(entry["project_id"], report["duplicate_project_homes"])
        duplicate.write_text(page.read_text(encoding="utf-8").replace("type: project", "type: project\ngithub_repo: Example/wrong"), encoding="utf-8")
        self.assertTrue(json.loads(self.cli("validate").stdout)["project_identity_errors"])

    def test_legacy_branch_without_identity_stays_unindexed_and_does_not_break_validation(self) -> None:
        entry = self.register()["project"]
        page = self.vault / entry["project_home"]
        legacy = page.with_name("legacy.md")
        legacy.write_text("---\ntype: branch\nproject: old-display-name\nworking_branch: main\n---\n"
                          "# legacyunidentified\n[[project]]\n", encoding="utf-8")
        report = self.cli("validate")
        self.assertEqual(report.returncode, 0, report.stdout + report.stderr)
        self.assertEqual(json.loads(report.stdout)["branch_pages"], 0)
        self.assertEqual(search(self.vault, self.config(), "legacyunidentified")["results"], [])

    def test_config_commit_failure_rolls_back_only_registration_notes(self) -> None:
        note = self.vault / "new.md"
        before = markdown_snapshot(self.vault)
        real = local_projects.atomic_write
        def fail(path, text):
            if path == self.config_file:
                raise OSError("simulated config write failure")
            return real(path, text)
        with patch.dict(os.environ, self.env), patch.object(local_projects, "atomic_write", side_effect=fail):
            with self.assertRaises(OSError):
                local_projects.commit_registration(self.config(), {note: "temporary registration\n"})
        self.assertEqual(before, markdown_snapshot(self.vault))


if __name__ == "__main__":
    unittest.main()
