from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-obsidian-memory"
SCRIPTS = PLUGIN / "scripts"
sys.path.insert(0, str(SCRIPTS))

import hook  # noqa: E402


class HookRoutingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.vault = Path(self.temporary.name) / "vault"
        shutil.copytree(PLUGIN / "assets" / "vault-template" / "shared", self.vault)
        shutil.copytree(
            PLUGIN / "assets" / "vault-template" / "en",
            self.vault,
            dirs_exist_ok=True,
        )
        project_dir = self.vault / "20-projects" / "demo"
        project_dir.mkdir(parents=True)
        (project_dir / "demo.md").write_text(
            """---
type: project
github_repo: Example/demo
---
# Demo

[[20-projects/demo/main|main]]
[[20-projects/demo/feature-api|feature/api]]
""",
            encoding="utf-8",
        )
        (project_dir / "main.md").write_text(
            "---\ntype: branch\ngithub_repo: Example/demo\nworking_branch: main\n---\nMAIN ONLY\n",
            encoding="utf-8",
        )
        (project_dir / "feature-api.md").write_text(
            "---\ntype: branch\ngithub_repo: Example/demo\nworking_branch: feature/api\n---\nFEATURE ONLY\n",
            encoding="utf-8",
        )
        self.config = {
            "enabled": True,
            "vault": str(self.vault),
            "scope_mode": "github-owner",
            "github_owners": ["Example"],
            "included_repositories": [],
            "excluded_repositories": ["Example/excluded"],
            "paths": {
                "home": "00-memory-home.md",
                "global_memory": "10-memory/global-memory.md",
                "maintenance": "10-memory/maintenance.md",
                "template": "10-memory/project-template.md",
                "project_index": "20-projects/project-index.md",
                "projects_dir": "20-projects",
                "weekly_brief": "10-memory/weekly-brief.md",
                "monthly_audit": "10-memory/monthly-audit.md",
            },
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_exact_branch_page_only(self) -> None:
        project = self.vault / "20-projects" / "demo" / "demo.md"
        scope = hook.Scope(
            kind="github-project",
            cwd=Path(self.temporary.name),
            repository="Example/demo",
            branch="feature/api",
            project_page=project,
        )
        context = hook.build_context(scope, self.config, self.vault)
        self.assertIn("FEATURE ONLY", context)
        self.assertNotIn("MAIN ONLY", context)
        self.assertIn("Long-term memory protocol", context)

    def test_new_repository_receives_template_and_index(self) -> None:
        scope = hook.Scope(
            kind="github-project",
            cwd=Path(self.temporary.name),
            repository="Example/new-repo",
            branch="main",
        )
        context = hook.build_context(scope, self.config, self.vault)
        self.assertIn("Project memory template", context)
        self.assertIn("Project index", context)
        self.assertIn("not indexed yet", context)

    def test_branch_case_and_repository_identity_are_exact(self) -> None:
        project = self.vault / "20-projects" / "demo" / "demo.md"
        for filename, branch, repository, body in (
            ("release-upper", "Release", "Example/demo", "UPPER BRANCH"),
            ("release-lower", "release", "example/DEMO", "LOWER BRANCH"),
            ("wrong-repo", "Release", "Other/demo", "WRONG REPOSITORY"),
        ):
            with project.open("a", encoding="utf-8") as handle:
                handle.write(f"\n[[{filename}]]\n")
            (project.parent / f"{filename}.md").write_text(
                f"---\ntype: branch\ngithub_repo: {repository}\nworking_branch: {branch}\n---\n{body}\n",
                encoding="utf-8",
            )
        for branch, wanted, unwanted in (("Release", "UPPER BRANCH", "LOWER BRANCH"),
                                         ("release", "LOWER BRANCH", "UPPER BRANCH")):
            scope = hook.Scope("github-project", self.vault, "Example/demo", branch, project)
            context = hook.build_context(scope, self.config, self.vault)
            self.assertIn(wanted, context)
            self.assertNotIn(unwanted, context)
            self.assertNotIn("WRONG REPOSITORY", context)
        scope = hook.Scope("github-project", self.vault, "Example/demo", "", project)
        context = hook.build_context(scope, self.config, self.vault)
        self.assertNotIn("UPPER BRANCH", context)
        self.assertNotIn("LOWER BRANCH", context)

    def test_scope_matrix(self) -> None:
        cwd = Path(self.temporary.name) / "work"
        cwd.mkdir()
        with patch.object(hook, "repository_identity", return_value=("Example/demo", "main")):
            self.assertTrue(hook.resolve_scope({"cwd": str(cwd)}, self.config, self.vault).eligible)
        with patch.object(hook, "repository_identity", return_value=("Example/excluded", "main")):
            self.assertFalse(hook.resolve_scope({"cwd": str(cwd)}, self.config, self.vault).eligible)
        with patch.object(hook, "repository_identity", return_value=("Other/demo", "main")):
            self.assertFalse(hook.resolve_scope({"cwd": str(cwd)}, self.config, self.vault).eligible)
        with patch.object(hook, "repository_identity", return_value=("", "")):
            self.assertFalse(hook.resolve_scope({"cwd": str(cwd)}, self.config, self.vault).eligible)
        self.assertEqual(hook.resolve_scope({"cwd": str(self.vault)}, self.config, self.vault).kind, "vault")

    def test_writeback_requires_visible_disclosure(self) -> None:
        event = {
            "hook_event_name": "UserPromptSubmit",
            "cwd": str(self.vault),
            "session_id": "session-review",
            "turn_id": "turn-review",
        }
        config_path = Path(self.temporary.name) / "state" / "config.json"
        config_path.parent.mkdir()
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(config_path)}):
            hook.save_review_snapshot(event, self.vault)
            snapshot_path = hook.review_snapshot_path(event)
            self.assertIsNotNone(snapshot_path)
            snapshot_text = snapshot_path.read_text(encoding="utf-8")
            self.assertNotIn("Long-term memory protocol", snapshot_text)

            changed = self.vault / "10-memory" / "global-memory.md"
            changed.write_text(
                changed.read_text(encoding="utf-8") + "\n- Durable preference\n",
                encoding="utf-8",
            )
            changes = hook.review_changes(event, self.vault)
            self.assertIn(("modified", "10-memory/global-memory.md"), changes)

            stop = {
                **event,
                "hook_event_name": "Stop",
                "last_assistant_message": "Done <!-- obsidian-memory-reviewed -->",
                "stop_hook_active": False,
            }
            with (
                patch.object(hook, "load_event", return_value=stop),
                patch.object(hook, "load_config", return_value=self.config),
                patch.object(sys, "stdout", new_callable=StringIO) as output,
            ):
                self.assertEqual(hook.main(), 0)
            blocked = json.loads(output.getvalue())
            self.assertEqual(blocked["decision"], "block")
            self.assertIn("10-memory/global-memory.md", blocked["reason"])
            self.assertIn("Knowledge-base writeback review", blocked["reason"])

            stop["last_assistant_message"] = (
                "Done\n"
                "<!-- obsidian-memory-writeback-disclosed -->\n"
                "<!-- obsidian-memory-reviewed -->"
            )
            with (
                patch.object(hook, "load_event", return_value=stop),
                patch.object(hook, "load_config", return_value=self.config),
                patch.object(sys, "stdout", new_callable=StringIO) as output,
            ):
                self.assertEqual(hook.main(), 0)
            marker_only = json.loads(output.getvalue())
            self.assertEqual(marker_only["decision"], "block")

            # A retry must not bypass missing per-file summaries or discard evidence.
            stop["stop_hook_active"] = True
            stop["last_assistant_message"] = (
                "## Knowledge-base writeback review\n- Memory updated.\n"
                "<!-- obsidian-memory-writeback-disclosed -->\n<!-- obsidian-memory-reviewed -->"
            )
            with (
                patch.object(hook, "load_event", return_value=stop),
                patch.object(hook, "load_config", return_value=self.config),
                patch.object(sys, "stdout", new_callable=StringIO) as output,
            ):
                self.assertEqual(hook.main(), 0)
            self.assertEqual(json.loads(output.getvalue())["decision"], "block")
            self.assertTrue(snapshot_path.exists())

            stop["last_assistant_message"] = (
                "## Knowledge-base writeback review\n"
                "- global-memory.md: added Durable preference.\n"
                "<!-- obsidian-memory-writeback-disclosed -->\n"
                "<!-- obsidian-memory-reviewed -->"
            )
            with (
                patch.object(hook, "load_event", return_value=stop),
                patch.object(hook, "load_config", return_value=self.config),
                patch.object(sys, "stdout", new_callable=StringIO) as output,
            ):
                self.assertEqual(hook.main(), 0)
            self.assertTrue(json.loads(output.getvalue())["continue"])
            self.assertFalse(snapshot_path.exists())


if __name__ == "__main__":
    unittest.main()
