from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
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


if __name__ == "__main__":
    unittest.main()
