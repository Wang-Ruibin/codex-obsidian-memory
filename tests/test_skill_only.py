from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/codex-obsidian-memory-skill"


class StandaloneSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / ".test-tmp").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="skill-only-", dir=ROOT / ".test-tmp")
        self.root = Path(self.temporary.name).resolve()
        # Run an actual copied folder; no installed plugin or repository imports.
        self.package = self.root / "installed-skill"
        shutil.copytree(SKILL, self.package, ignore=shutil.ignore_patterns("__pycache__"))
        self.home = self.root / "codex-home"
        self.home.mkdir()
        self.hook_profile = self.home / "obsidian-memory/config.json"
        self.hook_profile.parent.mkdir()
        self.hook_profile.write_text('{"enabled":true,"sentinel":"原有 Hook 配置"}', encoding="utf-8")
        (self.home / "config.toml").write_text('sandbox_mode = "workspace-write"\n', encoding="utf-8")
        (self.home / "AGENTS.md").write_text("# 原有指导\n", encoding="utf-8")
        self.protected = {p: p.read_bytes() for p in [self.hook_profile, self.home / "config.toml", self.home / "AGENTS.md"]}
        self.profile = self.home / "obsidian-memory-skill/config.json"
        self.vault = self.root / "中文知识库"
        self.workspace = self.root / "ordinary-folder"
        self.workspace.mkdir()
        self.environment = os.environ.copy()
        self.environment.update(CODEX_HOME=str(self.home), CODEX_THREAD_ID="real-test-session-a",
                                CODEX_OBSIDIAN_MEMORY_CONFIG=str(self.hook_profile),
                                CODEX_OBSIDIAN_SKILL_CONFIG=str(self.profile), PYTHONUTF8="0",
                                GIT_CEILING_DIRECTORIES=str(self.root),
                                GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="safe.directory",
                                GIT_CONFIG_VALUE_0=str(self.workspace))
        self.script = self.package / "scripts/skill_memory.py"

    def tearDown(self) -> None:
        for path, data in self.protected.items():
            self.assertEqual(path.read_bytes(), data, path)
        self.assertFalse((self.home / "obsidian-memory/conversations.json").exists())
        self.temporary.cleanup()

    def run_cli(self, *args: str, session: str | None = None) -> subprocess.CompletedProcess:
        env = self.environment.copy()
        if session:
            env["CODEX_THREAD_ID"] = session
        return subprocess.run([sys.executable, "-X", "utf8", "-B", str(self.script), *args],
                              cwd=self.workspace, env=env, capture_output=True, text=True, encoding="utf-8", timeout=30)

    def cli(self, *args: str, session: str | None = None) -> dict:
        result = self.run_cli(*args, session=session)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def init(self, github: bool = False) -> None:
        self.cli("init", "--vault", str(self.vault), "--locale", "zh-CN",
                 *(["--github-owner", "Example"] if github else ["--local-only"]))

    def git(self, *args: str) -> None:
        result = subprocess.run(["git", *args], env=self.environment, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(result.returncode, 0, result.stderr)

    def start(self, *, session: str | None = None) -> dict:
        return self.cli("start", "--cwd", str(self.workspace), session=session)

    def complete(self, task: dict, *, session: str | None = None) -> dict:
        changes = self.cli("changes", "--task-id", task["task_id"], "--cwd", str(self.workspace), session=session)["changes"]
        draft = self.root / "review.md"
        draft.write_text("## 知识库回写审查\n\n" + "\n".join(f"- `{path}`：保存已确认项目约束和验证结果。" for _, path in changes) +
                         "\n请审查并纠正。\n", encoding="utf-8")
        return self.cli("finish", "--task-id", task["task_id"], "--cwd", str(self.workspace), "--review-file", str(draft), session=session)

    def register_local(self) -> dict:
        return self.cli("local-register", "--path", str(self.workspace), "--name", "示例项目")

    def title(self, value: str) -> None:
        (self.home / "session_index.jsonl").write_text(json.dumps({"id": "real-test-session-a", "thread_name": value}, ensure_ascii=False) + "\n", encoding="utf-8")

    def test_package_is_self_contained_and_never_installs_hooks(self) -> None:
        self.init()
        self.assertEqual(self.cli("validate")["broken_links"], [])
        self.assertEqual(self.cli("status")["integration_mode"], "skill")
        self.assertFalse(self.start()["eligible"])
        self.assertFalse((self.home / "obsidian-memory-skill/conversations.json").exists())
        names = {p.name for p in self.package.rglob("*") if p.is_file()}
        for forbidden in ("hook.py", "hooks.json", "plugin.json", "conversation_watcher.py", "routine_runner.py", "install-windows-tasks.ps1"):
            self.assertNotIn(forbidden, names)
        self.assertNotEqual(self.run_cli("hook").returncode, 0)
        self.assertNotEqual(self.run_cli("init", "--vault", str(self.vault), "--local-only").returncode, 0)

    def test_project_baseline_resumes_and_disclosure_failure_keeps_claims(self) -> None:
        self.init()
        registration = self.register_local()
        task = self.start()
        self.assertIn("示例项目", task["context"])
        self.complete(task)
        task = self.start()
        self.assertEqual(self.cli("changes", "--task-id", task["task_id"], "--cwd", str(self.workspace))["changes"], [])
        page = self.vault / registration["project"]["project_home"]
        page.write_text(page.read_text(encoding="utf-8") + "\n项目预算为三十分钟。\n", encoding="utf-8")
        results = self.cli("search", "预算", "--cwd", str(self.workspace))["results"]
        self.assertEqual(results[0]["path"], registration["project"]["project_home"])
        excerpt = self.cli("read", results[0]["path"], "--cwd", str(self.workspace))
        self.assertIn("项目预算", json.dumps(excerpt, ensure_ascii=False))
        resumed = self.start()
        self.assertEqual(resumed["task_id"], task["task_id"])
        self.cli("claim-shared", "10-memory/global-memory.md", "--task-id", task["task_id"], "--cwd", str(self.workspace))
        other = self.start(session="real-test-session-b")
        foreign = self.run_cli("claim-shared", "10-memory/global-memory.md", "--task-id", other["task_id"], "--cwd", str(self.workspace), session="real-test-session-b")
        self.assertNotEqual(foreign.returncode, 0)
        bad = self.run_cli("finish", "--task-id", task["task_id"], "--cwd", str(self.workspace))
        self.assertNotEqual(bad.returncode, 0)
        self.assertEqual(self.start()["task_id"], task["task_id"])
        self.assertTrue(self.complete(task)["completed"])
        self.cli("claim-shared", "10-memory/global-memory.md", "--task-id", other["task_id"], "--cwd", str(self.workspace), session="real-test-session-b")
        self.complete(other, session="real-test-session-b")

    def test_chat_default_off_opt_in_isolated_disable_and_explicit_title_sync(self) -> None:
        self.init()
        self.assertFalse(self.start()["eligible"])
        self.title("初始标题")
        note = self.cli("conversation-enable", "--cwd", str(self.workspace))["note"]
        path = self.vault / note
        path.write_text(path.read_text(encoding="utf-8") + "\n只属于当前对话的持久事实。\n", encoding="utf-8")
        task = self.start()
        self.assertIn("只属于当前对话", task["context"])
        self.assertFalse(self.start(session="real-test-session-b")["eligible"])
        self.assertNotEqual(self.run_cli("read", note, "--cwd", str(self.workspace), session="real-test-session-b").returncode, 0)
        self.assertFalse((self.profile.parent / "conversation-watcher.lock").exists())
        self.complete(task)
        self.cli("conversation-disable")
        self.title("改过的标题")
        self.assertTrue(path.exists(), "No background worker should rename an idle Skill note")
        task = self.start()
        self.assertFalse(task["content_memory"])
        self.assertEqual(task["context"], "")
        new_path = self.vault / "40-conversations/改过的标题.md"
        self.assertFalse(path.exists())
        self.assertIn("只属于当前对话", new_path.read_text(encoding="utf-8"))
        self.assertNotEqual(self.run_cli("search", "持久", "--cwd", str(self.workspace)).returncode, 0)
        self.complete(task)
        self.cli("conversation-disable", "--freeze-title")
        self.title("冻结后不应同步")
        self.cli("conversation-sync")
        self.assertTrue(new_path.exists())

    def test_local_project_and_github_exclusion_keep_precedence(self) -> None:
        self.init(github=True)
        self.register_local()
        self.assertNotEqual(self.run_cli("conversation-enable", "--cwd", str(self.workspace), "--title", "测试").returncode, 0)
        self.git("init", "-b", "main", str(self.workspace))
        self.git("-C", str(self.workspace), "remote", "add", "origin", "git@github.com:Example/blocked.git")
        self.cli("exclude", "Example/blocked")
        self.assertFalse(self.start()["eligible"])

    def test_new_github_registration_and_exact_branch_loading(self) -> None:
        self.init(github=True)
        self.git("init", "-b", "main", str(self.workspace))
        self.git("-C", str(self.workspace), "remote", "add", "origin", "git@github.com:Example/demo.git")
        task = self.start()
        result = self.cli("register-github", "--task-id", task["task_id"], "--cwd", str(self.workspace))
        home = self.vault / result["project_home"]
        for branch in ("main", "Main"):
            filename = "lower.md" if branch == "main" else "upper.md"
            (home.parent / filename).write_text(f"---\ntype: branch\ngithub_repo: Example/demo\nworking_branch: {branch}\n---\n# Only-{branch}\n", encoding="utf-8")
            home.write_text(home.read_text(encoding="utf-8") + f"\n[[{filename[:-3]}]]\n", encoding="utf-8")
        context = self.start()["context"]
        self.assertIn("Only-main", context)
        self.assertNotIn("Only-Main", context)
        self.complete(task)

    def test_review_rejects_vague_or_omitted_notes_and_wrong_session(self) -> None:
        self.init()
        self.register_local()
        task = self.start()
        draft = self.root / "bad.md"
        draft.write_text("## 知识库回写审查\n\n- `20-projects/project-index.md`：已更新。\n", encoding="utf-8")
        result = self.run_cli("finish", "--task-id", task["task_id"], "--cwd", str(self.workspace), "--review-file", str(draft))
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(json.loads(result.stdout)["completed"])
        self.assertNotEqual(self.run_cli("changes", "--task-id", task["task_id"], "--cwd", str(self.workspace), session="real-test-session-b").returncode, 0)
        self.complete(task)

    def test_missing_original_snapshot_never_silently_rebaselines(self) -> None:
        self.init()
        self.register_local()
        task = self.start()
        (self.profile.parent / "writeback-reviews" / f"{task['review_token']}.json").unlink()
        result = self.run_cli("start", "--cwd", str(self.workspace))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("baseline is missing", result.stderr)

    def test_adoption_is_additive_and_global_disable_preserves_notes(self) -> None:
        self.vault.mkdir()
        existing = self.vault / "已有笔记.md"
        existing.write_text("不覆盖原正文。\n", encoding="utf-8")
        self.cli("init", "--vault", str(self.vault), "--local-only", "--no-template", "--path", "projects_dir=项目", "--path", "project_index=项目/索引.md")
        self.assertEqual(existing.read_text(encoding="utf-8"), "不覆盖原正文。\n")
        self.assertEqual(set(p.name for p in self.vault.iterdir()), {"已有笔记.md"})
        self.cli("disable")
        self.assertNotEqual(self.run_cli("start", "--cwd", str(self.workspace)).returncode, 0)
        self.cli("enable")
        self.assertTrue(self.cli("status")["enabled"])

    def test_profile_override_cannot_target_hook_settings(self) -> None:
        self.environment["CODEX_OBSIDIAN_SKILL_CONFIG"] = str(self.hook_profile)
        result = self.run_cli("init", "--vault", str(self.vault), "--local-only")
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.vault.exists())

    def test_generated_runtime_is_current(self) -> None:
        result = subprocess.run([sys.executable, "-X", "utf8", "-B", str(ROOT / "scripts/build_skill.py"), "--check"],
                                capture_output=True, text=True, encoding="utf-8", timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_platform_launcher_uses_only_its_private_runtime_state(self) -> None:
        env = self.environment.copy()
        runtime = self.root / "skill-runtime"
        runtime.mkdir()
        (runtime / "python-path.txt").write_text(sys.executable + "\n", encoding="utf-8")
        env["CODEX_OBSIDIAN_SKILL_RUNTIME_DIR"] = str(runtime)
        env["CODEX_OBSIDIAN_RUNTIME_DIR"] = str(self.root / "untouched-hook-runtime")
        if os.name == "nt":
            command = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                       str(self.package / "scripts/skillctl.ps1"), "-Action"]
        else:
            command = ["sh", str(self.package / "scripts/skillctl.sh")]
        for args in (["prepare-runtime"], ["init", "--vault", str(self.vault), "--local-only", "--locale", "zh-CN"], ["validate"]):
            result = subprocess.run([*command, *args], cwd=self.workspace, env=env, capture_output=True,
                                    text=True, encoding="utf-8", timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertFalse((self.root / "untouched-hook-runtime").exists())


if __name__ == "__main__":
    unittest.main()
