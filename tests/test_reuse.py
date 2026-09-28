from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-obsidian-memory"
SCRIPTS = PLUGIN / "scripts"
sys.path.insert(0, str(SCRIPTS))

from memory_core import frontmatter_value, markdown_snapshot  # noqa: E402
from reuse_memory import MAX_NOTE_BYTES, read_reference, search  # noqa: E402
import reuse_memory  # noqa: E402


class ReuseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "vault"
        shutil.copytree(PLUGIN / "assets/vault-template/en", self.vault)
        self.config = {"enabled": True, "vault": str(self.vault), "github_owners": ["Example"],
                       "excluded_repositories": ["Example/excluded"], "paths": {}}
        self.home = self.project("Example/old", "old")
        self.branch = self.home.parent / "release.md"
        self.branch.write_text("---\ntype: branch\ngithub_repo: Example/old\nworking_branch: Release\n---\n"
                               "# Background task\nWindows 后台 闪窗 validated task solution\n", encoding="utf-8")
        with self.home.open("a", encoding="utf-8") as handle:
            handle.write("\n[[release]]\n")
        self.config_file = self.root / "config.json"
        self.env = {**os.environ, "CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_file)}

    def tearDown(self) -> None:
        self.temp.cleanup()

    def project(self, repo: str, folder: str) -> Path:
        path = self.vault / "20-projects" / folder / "home.md"
        path.parent.mkdir(parents=True)
        path.write_text(f"---\ntype: project\ngithub_repo: {repo}\n---\n# Project\n"
                        "[[20-projects/project-index]]\n", encoding="utf-8")
        with (self.vault / "20-projects/project-index.md").open("a", encoding="utf-8") as handle:
            handle.write(f"\n[[20-projects/{folder}/home]]\n")
        return path

    def lesson(self, **overrides: str) -> Path:
        fields = {"type": "reusable-memory", "status": "verified", "summary": "Prevent flashing windows",
                  "keywords": "Windows 后台 闪窗", "source_repo": "Example/old",
                  "source_note": "20-projects/old/release.md", "source_branch": "Release",
                  "verified_on": "2026-01-01"}
        fields.update(overrides)
        path = self.vault / "10-memory/reusable/background.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("---\n" + "".join(f"{key}: {value}\n" for key, value in fields.items())
                        + "---\n# Windows background tasks\n[[index]]\n"
                        "## Applies when\nWindows scheduler only.\n"
                        "## Method and reason\nUse the verified launcher.\n"
                        "## Limitations\nNot a Linux scheduler.\n"
                        "## Evidence\nSource note records the tested result.\n", encoding="utf-8")
        return path

    def cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        self.config_file.write_text(json.dumps(self.config), encoding="utf-8")
        return subprocess.run([sys.executable, str(SCRIPTS / "memoryctl.py"), *args], env=self.env,
                              capture_output=True, text=True, encoding="utf-8", check=False)

    def test_old_vault_falls_back_and_preserves_branch_identity(self) -> None:
        shutil.rmtree(self.vault / "10-memory/reusable")
        result = search(self.vault, self.config, "Windows 闪窗")
        self.assertEqual(result["searched"], ["shared", "projects"])
        hit = result["results"][0]
        self.assertEqual(hit["branch"], "Release")
        self.assertTrue(hit["reference_only"])
        self.assertEqual(hit["repository"], "Example/old")
        self.assertEqual(hit["line"], 7)

    def test_shared_first_and_explicit_project_retry(self) -> None:
        self.lesson()
        before = markdown_snapshot(self.vault)
        result = search(self.vault, self.config, "WINDOWS 后台")
        self.assertEqual(result["searched"], ["shared"])
        self.assertEqual(result["results"][0]["kind"], "shared")
        self.assertEqual(search(self.vault, self.config, "Windows", "projects")["results"][0]["kind"], "project")
        self.assertEqual(before, markdown_snapshot(self.vault))

    def test_shared_hit_does_not_read_branch_bodies_or_excluded_home(self) -> None:
        self.lesson()
        excluded = self.project("Example/excluded", "excluded")
        with patch.object(reuse_memory, "read_text", wraps=reuse_memory.read_text) as reads:
            self.assertTrue(search(self.vault, self.config, "Windows")["results"])
        read_paths = [call.args[0] for call in reads.call_args_list]
        self.assertNotIn(self.branch, read_paths)
        self.assertNotIn(excluded, read_paths)

    def test_rank_prefers_more_matched_terms_and_honors_limit(self) -> None:
        other = self.project("Example/second", "second")
        with other.open("a", encoding="utf-8") as handle:
            handle.write("\nWindows\n")
        result = search(self.vault, self.config, "Windows 后台", "projects", 1)
        self.assertEqual(len(result["results"]), 1)
        self.assertEqual(result["results"][0]["path"], "20-projects/old/release.md")
        self.assertEqual(result["results"][0]["matched_keywords"], ["windows", "后台"])

    def test_shared_provenance_status_and_date_must_validate(self) -> None:
        for override in ({"source_branch": "release"}, {"source_repo": "Other/old"},
                         {"source_note": "../outside.md"}, {"status": "draft"},
                         {"verified_on": "2099-01-01"}, {"verified_on": "yesterday"},
                         {"summary": ""}):
            with self.subTest(override=override):
                self.lesson(**override)
                self.assertEqual(search(self.vault, self.config, "Windows", "shared")["results"], [])

    def test_excluded_source_revokes_shared_search_and_read(self) -> None:
        lesson = self.lesson()
        self.config["excluded_repositories"].append("example/OLD")
        self.assertEqual(search(self.vault, self.config, "Windows")["results"], [])
        for path in (lesson, self.branch):
            with self.assertRaises(ValueError):
                read_reference(self.vault, self.config, path.relative_to(self.vault).as_posix())

    def test_inclusions_indexed_mode_and_false_body_identity(self) -> None:
        foreign = self.project("Other/foreign", "foreign")
        with foreign.open("a", encoding="utf-8") as handle:
            handle.write("\ngithub_repo: Example/pretend\nuniqueforeign\n")
        self.assertEqual(search(self.vault, self.config, "uniqueforeign")["results"], [])
        self.config["included_repositories"] = ["Other/foreign"]
        self.assertEqual(len(search(self.vault, self.config, "uniqueforeign")["results"]), 1)
        self.config["included_repositories"] = []
        self.config["scope_mode"] = "indexed-only"
        self.assertEqual(len(search(self.vault, self.config, "uniqueforeign")["results"]), 1)
        self.config["excluded_repositories"].append("Other/foreign")
        self.assertEqual(search(self.vault, self.config, "uniqueforeign")["results"], [])

    def test_only_linked_notes_with_consistent_identity_are_references(self) -> None:
        for name, header in (("orphan", ""), ("wrong", "---\ngithub_repo: Other/repo\n---\n")):
            (self.home.parent / f"{name}.md").write_text(header + "uniquefailure\n", encoding="utf-8")
        with self.home.open("a", encoding="utf-8") as handle:
            handle.write("\n[[wrong]]\n")
        self.assertEqual(search(self.vault, self.config, "uniquefailure")["results"], [])
        with self.home.open("a", encoding="utf-8") as handle:
            handle.write("\n[[orphan]]\n")
        self.assertEqual(len(search(self.vault, self.config, "uniquefailure")["results"]), 1)

    def test_ambiguous_project_homes_fail_closed(self) -> None:
        duplicate = self.project("example/OLD", "duplicate")
        self.assertEqual(search(self.vault, self.config, "Windows")["results"], [])
        duplicate.unlink()
        (self.home.parent / "duplicate.md").write_text("---\ntype: project\ngithub_repo: Example/another\n---\n", encoding="utf-8")
        self.assertEqual(search(self.vault, self.config, "Windows")["results"], [])

    def test_bounded_read_redacts_before_slicing_and_keeps_source_lines(self) -> None:
        source = self.branch.read_text(encoding="utf-8") + (
            "-----BEGIN PRIVATE KEY-----\nSENSITIVE\n-----END PRIVATE KEY-----\n"
            "after-key evidence\nsecret ghp_" + "a" * 30 + "\n" + "x" * 15000 + "\n")
        self.branch.write_text(source, encoding="utf-8")
        reference = self.branch.relative_to(self.vault).as_posix()
        result = read_reference(self.vault, self.config, reference, 8, 6)
        serialized = json.dumps(result)
        self.assertNotIn("SENSITIVE", serialized)
        self.assertNotIn("ghp_", serialized)
        self.assertEqual(result["lines"][3]["line"], 11)
        self.assertEqual(result["lines"][3]["text"], "after-key evidence")
        self.assertTrue(result["lines"][-1]["truncated"])
        self.assertEqual(search(self.vault, self.config, "after-key")["results"][0]["line"], 11)
        self.assertLess(len(serialized), 14000)

    def test_hidden_oversized_symlink_and_traversal_not_returned(self) -> None:
        (self.home.parent / ".hidden.md").write_text("invisiblehit", encoding="utf-8")
        (self.home.parent / "large.md").write_bytes(b"invisiblehit " * (MAX_NOTE_BYTES // 10))
        with self.home.open("a", encoding="utf-8") as handle:
            handle.write("\n[[.hidden]]\n[[large]]\n[[linked]]\n")
        outside = self.root / "outside.md"
        outside.write_text("invisiblehit", encoding="utf-8")
        try:
            (self.home.parent / "linked.md").symlink_to(outside)
        except OSError:
            pass  # Windows may not grant symlink privileges.
        self.assertEqual(search(self.vault, self.config, "invisiblehit")["results"], [])
        for path in (str(outside), "../outside.md", "20-projects/old/linked.md", "20-projects/old/.hidden.md"):
            with self.assertRaises(ValueError):
                read_reference(self.vault, self.config, path)

    def test_ranking_limits_and_invalid_queries(self) -> None:
        self.lesson()
        for query in ("", "!", " ".join(f"term{i}" for i in range(17)), "x" * 501):
            with self.assertRaises(ValueError):
                search(self.vault, self.config, query)
        with self.assertRaises(ValueError):
            search(self.vault, self.config, "Windows", limit=11)
        self.assertEqual(search(self.vault, self.config, "nomatch")["results"], [])
        self.assertEqual(search(self.vault, self.config, "Windows 后台"), search(self.vault, self.config, "Windows 后台"))
        with self.assertRaises(ValueError):
            read_reference(self.vault, self.config, "20-projects/old/release.md", 0)

    def test_cli_workspace_scope_and_disabled_memory(self) -> None:
        allowed = self.cli("search", "Windows", "--cwd", str(self.vault))
        self.assertEqual(allowed.returncode, 0, allowed.stderr)
        hit = json.loads(allowed.stdout)["results"][0]
        read = self.cli("read", hit["path"], "--cwd", str(self.vault), "--start-line", str(hit["line"]))
        self.assertEqual(read.returncode, 0, read.stderr)
        self.assertNotEqual(self.cli("search", "Windows", "--cwd", str(self.root)).returncode, 0)
        self.config["enabled"] = False
        disabled = self.cli("search", "Windows", "--cwd", str(self.vault))
        self.assertNotEqual(disabled.returncode, 0)
        self.assertNotIn("validated task solution", disabled.stdout + disabled.stderr)

    def test_cli_real_git_workspace_and_configured_paths(self) -> None:
        work = self.root / "work"
        subprocess.run(["git", "init", "-q", str(work)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(work), "remote", "add", "origin", "git@github.com:Example/new.git"], check=True)
        custom = self.vault / "知识/复用"
        custom.parent.mkdir()
        self.lesson()
        shutil.move(str(self.vault / "10-memory/reusable"), custom)
        self.config["paths"] = {"reuse_dir": "知识/复用", "reuse_index": "知识/复用/index.md",
                                "reuse_template": "知识/复用/template.md"}
        result = self.cli("search", "后台", "--cwd", str(work))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["results"][0]["path"], "知识/复用/background.md")
        self.config["excluded_repositories"].append("Example/new")
        self.assertNotEqual(self.cli("search", "Windows", "--cwd", str(work)).returncode, 0)

    def test_validator_reports_bad_shared_provenance(self) -> None:
        self.lesson(source_branch="release")
        result = self.cli("validate")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("10-memory/reusable/background.md", json.loads(result.stdout)["reusable_lesson_errors"])

    def test_retired_lessons_are_retained_but_not_candidates(self) -> None:
        lesson = self.lesson(status="retired", source_branch="missing")
        self.assertEqual(search(self.vault, self.config, "Windows", "shared")["results"], [])
        result = self.cli("validate")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(lesson.exists())

    def test_repository_level_provenance_has_empty_branch(self) -> None:
        self.lesson(source_note="20-projects/old/home.md", source_branch="")
        result = search(self.vault, self.config, "Windows", "shared")
        self.assertEqual(result["results"][0]["branch"], "")

    def test_empty_frontmatter_field_does_not_consume_next_field(self) -> None:
        self.assertEqual(frontmatter_value("---\nsource_branch:\nsource_note: notes.md\n---\n", "source_branch"), "")


if __name__ == "__main__":
    unittest.main()
