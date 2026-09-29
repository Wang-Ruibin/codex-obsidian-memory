from __future__ import annotations

import json
import os
import subprocess
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from io import StringIO
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-obsidian-memory"
sys.path.insert(0, str(PLUGIN / "scripts"))
import hook
import local_projects
from memory_core import claim_shared_file, clear_review_snapshot, review_changes, review_snapshot_path, save_review_snapshot


class ConcurrentReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "vault"
        shutil.copytree(PLUGIN / "assets/vault-template/en", self.vault)
        self.work_a, self.work_b = self.root / "work-a", self.root / "work-b"
        self.work_a.mkdir()
        self.work_b.mkdir()
        self.config_path = self.root / "state/config.json"
        self.config_path.parent.mkdir()
        self.config = {"enabled": True, "vault": str(self.vault), "scope_mode": "github-owner",
                       "github_owners": ["Example"], "excluded_repositories": [], "paths": {}}
        self.config_path.write_text(json.dumps(self.config), encoding="utf-8")
        self.pages = {}
        for repository, slug, label in (("Example/alpha", "alpha", "A_PROJECT_ONLY"),
                                        ("Example/beta", "beta", "B_PROJECT_ONLY")):
            folder = self.vault / "20-projects" / slug
            folder.mkdir()
            home = folder / "home.md"
            home.write_text(f"---\ntype: project\ngithub_repo: {repository}\n---\n# {label}\n"
                            "[[branch]]\n[[20-projects/project-index]]\n", encoding="utf-8")
            branch = folder / "branch.md"
            branch.write_text(f"---\ntype: branch\ngithub_repo: {repository}\nworking_branch: main\n---\n"
                              f"# {label} branch\n", encoding="utf-8")
            self.pages[slug] = branch
        self.events = {
            "alpha": {"hook_event_name": "UserPromptSubmit", "cwd": str(self.work_a),
                      "session_id": "conversation-a", "turn_id": "task-a"},
            "beta": {"hook_event_name": "UserPromptSubmit", "cwd": str(self.work_b),
                     "session_id": "conversation-b", "turn_id": "task-b"},
        }

    def tearDown(self):
        self.temp.cleanup()

    def call_hook(self, event):
        mapping = {self.work_a: ("Example/alpha", "main"), self.work_b: ("Example/beta", "main")}
        with (patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}),
              patch.object(hook, "repository_identity", side_effect=lambda cwd: mapping[Path(cwd)]),
              patch.object(hook, "load_event", return_value=event),
              patch.object(hook, "load_config", return_value=self.config),
              patch.object(sys, "stdout", new_callable=StringIO) as output):
            self.assertEqual(hook.main(), 0)
        return json.loads(output.getvalue())

    def stop(self, slug, message):
        return self.call_hook({**self.events[slug], "hook_event_name": "Stop", "last_assistant_message": message})

    def start_both(self):
        first = self.call_hook(self.events["alpha"])["hookSpecificOutput"]["additionalContext"]
        second = self.call_hook(self.events["beta"])["hookSpecificOutput"]["additionalContext"]
        self.assertIn("A_PROJECT_ONLY", first)
        self.assertNotIn("B_PROJECT_ONLY", first)
        self.assertIn("B_PROJECT_ONLY", second)
        self.assertNotIn("A_PROJECT_ONLY", second)
        return first, second

    def test_parallel_projects_have_separate_snapshots_and_audits(self):
        self.start_both()
        for slug in ("alpha", "beta"):
            with self.pages[slug].open("a", encoding="utf-8") as note:
                note.write(f"\n- Verified {slug} result.\n")
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            first = review_snapshot_path(self.events["alpha"])
            second = review_snapshot_path(self.events["beta"])
            self.assertNotEqual(first, second)
            self.assertNotIn("20-projects/beta/", first.read_text(encoding="utf-8"))
            self.assertNotIn("20-projects/alpha/", second.read_text(encoding="utf-8"))
        blocked_a = self.stop("alpha", "<!-- obsidian-memory-reviewed -->")
        blocked_b = self.stop("beta", "<!-- obsidian-memory-reviewed -->")
        self.assertEqual(blocked_a["decision"], "block")
        self.assertIn("20-projects/alpha/branch.md", blocked_a["reason"])
        self.assertNotIn("20-projects/beta/branch.md", blocked_a["reason"])
        self.assertIn("20-projects/beta/branch.md", blocked_b["reason"])
        self.assertNotIn("20-projects/alpha/branch.md", blocked_b["reason"])
        for slug in ("alpha", "beta"):
            path = f"20-projects/{slug}/branch.md"
            reply = ("## Knowledge-base writeback review\n"
                     f"- {path}: saved verified {slug} project outcome.\n"
                     "<!-- obsidian-memory-writeback-disclosed -->\n"
                     "<!-- obsidian-memory-reviewed -->")
            self.assertTrue(self.stop(slug, reply)["continue"])

    def test_shared_note_claims_serialize_editing_between_projects(self):
        context_a, context_b = self.start_both()
        self.assertIn("claim-shared", context_a)
        self.assertIn("claim-shared", context_b)
        global_note = self.vault / "10-memory/global-memory.md"
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            token_a = review_snapshot_path(self.events["alpha"]).stem
            token_b = review_snapshot_path(self.events["beta"]).stem
            relative = "10-memory/global-memory.md"
            self.assertEqual(claim_shared_file(token_a, "example/alpha", relative, self.vault, self.config), relative)
            with self.assertRaisesRegex(ValueError, "reserved by another active conversation"):
                claim_shared_file(token_b, "example/beta", relative, self.vault, self.config)
            with global_note.open("a", encoding="utf-8") as note:
                note.write("\n- SHARED_FROM_ALPHA verified.\n")
            self.assertNotIn(relative, [path for _, path in review_changes(
                self.events["beta"], self.vault, project_root=self.pages["beta"].parent, owner="example/beta")])
        reply_a = ("## Knowledge-base writeback review\n"
                   "- 10-memory/global-memory.md: added verified shared lesson from alpha.\n"
                   "<!-- obsidian-memory-writeback-disclosed -->\n<!-- obsidian-memory-reviewed -->")
        self.assertTrue(self.stop("alpha", reply_a)["continue"])
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            self.assertEqual(claim_shared_file(token_b, "example/beta", relative, self.vault, self.config), relative)
            with global_note.open("a", encoding="utf-8") as note:
                note.write("\n- SHARED_FROM_BETA verified.\n")
            self.assertEqual(review_changes(self.events["beta"], self.vault,
                                             project_root=self.pages["beta"].parent, owner="example/beta"),
                             [("modified", relative)])
        reply_b = ("## Knowledge-base writeback review\n"
                   "- 10-memory/global-memory.md: added verified shared lesson from beta.\n"
                   "<!-- obsidian-memory-writeback-disclosed -->\n<!-- obsidian-memory-reviewed -->")
        self.assertTrue(self.stop("beta", reply_b)["continue"])
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            self.assertFalse(list((self.vault / ".codex-obsidian-memory/claims").glob("*.json")))

    def test_cross_workspace_stop_with_same_turn_is_blocked(self):
        self.start_both()
        switched = {**self.events["alpha"], "cwd": str(self.work_b),
                    "hook_event_name": "Stop", "last_assistant_message": "<!-- obsidian-memory-reviewed -->"}
        outcome = self.call_hook(switched)
        self.assertEqual(outcome["decision"], "block")
        self.assertIn("identity changed", outcome["reason"])

    def test_claim_shared_cli_checks_workspace_and_exact_turn(self):
        self.start_both()
        subprocess.run(["git", "init", "-q", str(self.work_a)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.work_a), "remote", "add", "origin",
                        "git@github.com:Example/alpha.git"], check=True, capture_output=True)
        subprocess.run(["git", "init", "-q", str(self.work_b)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(self.work_b), "remote", "add", "origin",
                        "git@github.com:Example/beta.git"], check=True, capture_output=True)
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            token = review_snapshot_path(self.events["alpha"]).stem
            environment = {**os.environ, "CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}
            command = [sys.executable, str(PLUGIN / "scripts/memoryctl.py"), "claim-shared",
                       "10-memory/global-memory.md", "--review-token", token, "--cwd", str(self.work_a)]
            claimed = subprocess.run(command, env=environment, capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(claimed.returncode, 0, claimed.stderr)
            self.assertEqual(json.loads(claimed.stdout)["owner"], "example/alpha")
            wrong = subprocess.run(command[:-1] + [str(self.work_b)], env=environment,
                                   capture_output=True, text=True, encoding="utf-8")
            self.assertNotEqual(wrong.returncode, 0)
            self.assertIn("not belong", wrong.stderr)

    def test_separate_environment_configs_share_one_vault_lease(self):
        self.start_both()
        second_config = self.root / "other-environment/config.json"
        second_config.parent.mkdir()
        second_config.write_text(json.dumps(self.config), encoding="utf-8")
        relative = "10-memory/global-memory.md"
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            token_a = review_snapshot_path(self.events["alpha"]).stem
            claim_shared_file(token_a, "example/alpha", relative, self.vault, self.config)
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(second_config)}):
            save_review_snapshot(self.events["beta"], self.vault,
                                 project_root=self.pages["beta"].parent, owner="example/beta")
            token_b = review_snapshot_path(self.events["beta"]).stem
            with self.assertRaisesRegex(ValueError, "reserved by another active conversation"):
                claim_shared_file(token_b, "example/beta", relative, self.vault, self.config)
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            clear_review_snapshot(self.events["alpha"])
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(second_config)}):
            self.assertEqual(claim_shared_file(token_b, "example/beta", relative, self.vault, self.config), relative)
            clear_review_snapshot(self.events["beta"])

    def test_concurrent_new_github_projects_keep_both_index_links_and_separate_reviews(self):
        unrelated = {"session_id": "unrelated", "turn_id": "read", "cwd": str(self.work_a)}
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            save_review_snapshot(unrelated, self.vault, owner="example/alpha", project_root=self.pages["alpha"].parent)
        projects = []
        for slug in ("new-c", "new-d"):
            work = self.root / slug
            subprocess.run(["git", "init", "-q", str(work)], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(work), "remote", "add", "origin",
                            f"git@github.com:Example/{slug}.git"], check=True, capture_output=True)
            event = {"session_id": slug, "turn_id": "register", "cwd": str(work)}
            with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
                save_review_snapshot(event, self.vault, owner=f"example/{slug}")
            projects.append((slug, work, event))
        environment = {**os.environ, "CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}
        processes = [subprocess.Popen(
            [sys.executable, str(PLUGIN / "scripts/memoryctl.py"), "register-github", "--cwd", str(work),
             "--review-token", review_snapshot_path(event).stem],
            env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            for _, work, event in projects]
        registered = []
        for process in processes:
            stdout, stderr = process.communicate(timeout=35)
            self.assertEqual(process.returncode, 0, stderr)
            registered.append(json.loads(stdout))
        index = (self.vault / "20-projects/project-index.md").read_text(encoding="utf-8")
        for result in registered:
            target = result["project_home"].removesuffix(".md")
            self.assertIn(f"[[{target}|", index)
        # A turn already in progress that did not register anything must not review the shared index.
        with patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}):
            for (slug, _, event), result in zip(projects, registered):
                root = (self.vault / result["project_home"]).parent
                changed = [path for _, path in review_changes(event, self.vault,
                                                 project_root=root, owner=f"example/{slug}")]
                self.assertIn(result["project_home"], changed)
                self.assertIn("20-projects/project-index.md", changed)
                self.assertNotIn(next(item["project_home"] for item in registered if item is not result), changed)
            self.assertEqual(review_changes(unrelated, self.vault,
                                            project_root=self.pages["alpha"].parent, owner="example/alpha"), [])

    def test_failed_github_index_write_rolls_back_only_its_new_home(self):
        work = self.root / "failed-register"
        subprocess.run(["git", "init", "-q", str(work)], check=True, capture_output=True)
        subprocess.run(["git", "-C", str(work), "remote", "add", "origin",
                        "git@github.com:Example/new-failed.git"], check=True, capture_output=True)
        index = self.vault / "20-projects/project-index.md"
        before = index.read_bytes()
        writer = local_projects.atomic_write
        def fail_index(path, content):
            if path == index:
                raise OSError("simulated index update failure")
            return writer(path, content)
        with (patch.dict(os.environ, {"CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.config_path)}),
              patch.object(local_projects, "atomic_write", side_effect=fail_index)):
            event = {"session_id": "failed-register", "turn_id": "register", "cwd": str(work)}
            save_review_snapshot(event, self.vault, owner="example/new-failed")
            with self.assertRaises(OSError):
                local_projects.command_register_github(Namespace(cwd=work, review_token=review_snapshot_path(event).stem))
        self.assertEqual(index.read_bytes(), before)
        self.assertFalse(list((self.vault / "20-projects/new-failed").glob("*.md")))
        self.assertFalse((self.vault / ".codex-obsidian-memory/registration.lock").exists())


if __name__ == "__main__":
    unittest.main()
