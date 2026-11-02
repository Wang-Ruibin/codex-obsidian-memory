from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
import unicodedata
from argparse import Namespace
from contextlib import closing, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-obsidian-memory"
sys.path.insert(0, str(PLUGIN / "scripts"))
import conversations
import hook
from memory_core import (DEFAULT_PATHS, REVIEW_MARKER, WRITEBACK_DISCLOSURE_MARKER,
                         load_config, review_changes, save_config, save_review_snapshot)


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "vault"
        shutil.copytree(PLUGIN / "assets/vault-template/en", self.vault)
        self.work = self.root / "ordinary"
        self.work.mkdir()
        self.codex = self.root / "codex"
        self.codex.mkdir()
        self.env = patch.dict(os.environ, {"CODEX_HOME": str(self.codex),
                             "CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.root / "state/config.json"),
                             "CODEX_OBSIDIAN_NO_WATCHER": "1"})
        self.env.start()
        self.config = {"enabled": True, "vault": str(self.vault), "locale": "zh-CN",
                       "scope_mode": "github-owner", "github_owners": ["Example"],
                       "paths": dict(DEFAULT_PATHS)}
        save_config(self.config)

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def run_command(self, name, value="chat-a", title="中文对话", **kwargs):
        args = Namespace(command=name, session_id=value, title=title, cwd=self.work, **kwargs)
        with redirect_stdout(StringIO()) as output:
            conversations.command(args)
        return json.loads(output.getvalue())

    def event(self, value="chat-a", **extra):
        return {"session_id": value, "turn_id": "turn-1", "cwd": str(self.work), **extra}

    def run_hook(self, event):
        with patch.object(hook, "load_event", return_value=event), redirect_stdout(StringIO()) as output:
            self.assertEqual(hook.main(), 0)
        return json.loads(output.getvalue()) if output.getvalue() else None

    def write_name(self, value, name, old_title="This is the first user prompt, not the displayed name"):
        with closing(sqlite3.connect(self.codex / "state_5.sqlite")) as connection, connection:
            connection.execute("CREATE TABLE IF NOT EXISTS threads(id TEXT PRIMARY KEY, name TEXT, title TEXT)")
            connection.execute("INSERT OR REPLACE INTO threads VALUES(?,?,?)", (value, name, old_title))

    def test_default_off_does_not_write_or_scan_prompt_keywords(self):
        event = self.event(hook_event_name="UserPromptSubmit", prompt='Example only: "enable conversation memory"')
        with patch.object(conversations, "metadata_title") as metadata:
            self.assertIsNone(self.run_hook(event))
            self.assertEqual(self.run_hook({**event, "hook_event_name": "Stop"}), {"continue": True})
            metadata.assert_not_called()
        self.assertFalse(conversations.state_path().exists())

    def test_enable_is_immediate_isolated_and_requires_first_writeback_review(self):
        result = self.run_command("conversation-enable")
        self.assertIn("中文对话", result["context"])
        self.assertIn("codex:chat-a", result["context"])
        self.assertEqual(Path(result["note"]).name, "中文对话.md")
        self.assertEqual(hook.resolve_scope(self.event("other"), self.config, self.vault).kind, "none")
        stop = self.event(hook_event_name="Stop", last_assistant_message=REVIEW_MARKER)
        self.assertEqual(self.run_hook(stop)["decision"], "block")
        visible = "## 知识库回写审查\n" + "\n".join(
            f"- `{path}`：创建对话记忆入口及已确认背景。" for path in result["changed_notes"])
        stop["last_assistant_message"] = visible + "\n" + WRITEBACK_DISCLOSURE_MARKER + "\n" + REVIEW_MARKER
        self.assertEqual(self.run_hook(stop), {"continue": True})
        self.assertNotIn("pending_review", conversations.registered("chat-a"))

    def test_same_titles_do_not_overwrite_and_context_does_not_load_other_chats(self):
        a = self.run_command("conversation-enable")
        (self.vault / a["note"]).write_text((self.vault / a["note"]).read_text(encoding="utf-8") + "\nA PRIVATE FACT\n", encoding="utf-8")
        b = self.run_command("conversation-enable", "chat-b")
        self.assertNotEqual(a["note"].casefold(), b["note"].casefold())
        self.assertNotIn("A PRIVATE FACT", b["context"])
        self.assertIn("A PRIVATE FACT", (self.vault / a["note"]).read_text(encoding="utf-8"))
        conversations.clear_review("chat-a")
        event = self.event()
        save_review_snapshot(event, self.vault, owner="codex:chat-a", files=(self.vault / a["note"],))
        with (self.vault / b["note"]).open("a", encoding="utf-8") as handle:
            handle.write("\nB PRIVATE FACT\n")
        self.assertEqual(review_changes(event, self.vault, owner="codex:chat-a", files=(self.vault / a["note"],)), [])

    def test_displayed_name_wins_over_first_prompt_and_index_is_fallback(self):
        self.write_name("chat-a", "界面标题")
        self.assertEqual(conversations.metadata_title("chat-a"), "界面标题")
        with closing(sqlite3.connect(self.codex / "state_5.sqlite")) as connection, connection:
            connection.execute("UPDATE threads SET name=NULL")
        (self.codex / "session_index.jsonl").write_text(
            '{"id":"chat-a","thread_name":"旧名"}\n{"id":"chat-a","thread_name":"新名"}\n', encoding="utf-8")
        self.assertEqual(conversations.metadata_title("chat-a"), "新名")
        self.assertEqual(conversations.metadata_title("never-opted-in"), "")

    def test_title_rename_preserves_facts_and_index_links(self):
        self.write_name("chat-a", "旧标题")
        result = self.run_command("conversation-enable")
        old = self.vault / result["note"]
        with old.open("a", encoding="utf-8") as handle:
            handle.write("\n## Durable outcome\nVerified fact: exact evidence.\n")
        self.write_name("chat-a", "新标题")
        changed = conversations.sync_titles()
        new = self.vault / conversations.registered("chat-a")["note"]
        self.assertEqual(new.name, "新标题.md")
        self.assertFalse(old.exists())
        self.assertIn("Verified fact: exact evidence.", new.read_text(encoding="utf-8"))
        self.assertIn(result["note"], changed)
        index = (self.vault / self.config["paths"]["conversation_index"]).read_text(encoding="utf-8")
        self.assertIn("新标题", index)
        self.assertNotIn("旧标题", index)

    def test_disable_retains_notes_and_stops_loading_but_title_sync_can_continue(self):
        result = self.run_command("conversation-enable")
        self.run_command("conversation-disable")
        self.write_name("chat-a", "Renamed while memory is off")
        self.assertTrue(conversations.sync_titles())
        self.assertTrue((self.vault / conversations.registered("chat-a")["note"]).is_file())
        self.assertEqual(hook.resolve_scope(self.event(), self.config, self.vault).kind, "none")
        self.assertTrue(self.run_command("conversation-enable")["enabled"])

    def test_disable_can_explicitly_freeze_filename_updates(self):
        self.run_command("conversation-enable")
        self.run_command("conversation-disable", freeze_title=True)
        with patch.object(conversations, "metadata_title") as metadata:
            self.assertEqual(conversations.sync_titles(), [])
            metadata.assert_not_called()

    def test_existing_local_project_and_github_routes_are_preserved(self):
        with patch.object(conversations, "repository_identity", return_value=("Example/repo", "main")):
            with self.assertRaisesRegex(ValueError, "GitHub"):
                self.run_command("conversation-enable")
        with patch.object(conversations, "local_for_workspace", return_value={"enabled": True}):
            with self.assertRaisesRegex(ValueError, "local project"):
                self.run_command("conversation-enable")
        self.assertFalse(conversations.state_path().exists())

    def test_invalid_missing_titles_and_traversal_do_not_create_notes(self):
        with self.assertRaisesRegex(ValueError, "title is unavailable"):
            self.run_command("conversation-enable", title="")
        with self.assertRaises(ValueError):
            self.run_command("conversation-enable", "../../escape")
        with self.assertRaises(ValueError):
            conversations.note_path(self.vault, self.config, {"note": "../escape.md"})
        for title in ("CON", "a/b:c?", " . ", "名字" * 100):
            name = conversations.filename(title)
            self.assertNotRegex(name, r'[<>:"/\\|?*]')
            self.assertTrue(name.endswith(".md"))
            self.assertLessEqual(len(name), 104)

    def test_registry_publish_failure_rolls_back_title_rename(self):
        self.write_name("chat-a", "Before")
        result = self.run_command("conversation-enable")
        old = self.vault / result["note"]
        original = old.read_bytes()
        self.write_name("chat-a", "After")
        real = conversations.atomic_write
        def fail(path, text):
            if path == conversations.state_path():
                raise OSError("simulated registry failure")
            return real(path, text)
        with patch.object(conversations, "atomic_write", side_effect=fail), self.assertRaises(OSError):
            conversations.sync_titles()
        self.assertEqual(old.read_bytes(), original)
        self.assertFalse((old.parent / "After.md").exists())
        self.assertEqual(conversations.registered("chat-a")["title"], "Before")

    def test_other_environment_index_entries_are_retained(self):
        self.run_command("conversation-enable")
        original = conversations.state_path().read_text(encoding="utf-8")
        conversations.state_path().unlink()
        b = self.run_command("conversation-enable", "chat-b", "Another")
        index = (self.vault / self.config["paths"]["conversation_index"]).read_text(encoding="utf-8")
        self.assertIn("codex:chat-a", index)
        self.assertIn("codex:chat-b", index)
        self.assertIn("Another", b["context"])

    def test_same_id_reuses_note_after_registry_is_lost(self):
        a = self.run_command("conversation-enable")
        path = self.vault / a["note"]
        with path.open("a", encoding="utf-8") as handle:
            handle.write("\nA retained verified fact\n")
        conversations.state_path().unlink()
        b = self.run_command("conversation-enable")
        self.assertEqual(a["note"], b["note"])
        self.assertIn("A retained verified fact", path.read_text(encoding="utf-8"))

    def test_case_collisions_and_case_only_renames(self):
        a = self.run_command("conversation-enable", title="Topic")
        b = self.run_command("conversation-enable", "chat-b", "topic")
        self.assertNotEqual(a["note"].casefold(), b["note"].casefold())
        self.write_name("chat-a", "TOPIC")
        conversations.sync_titles()
        note = self.vault / conversations.registered("chat-a")["note"]
        self.assertEqual(note.name, "TOPIC.md")
        self.assertIn("TOPIC.md", [path.name for path in note.parent.iterdir()])

    def test_long_unicode_title_creates_a_portable_filename(self):
        result = self.run_command("conversation-enable", title="名字" * 100)
        note = self.vault / result["note"]
        self.assertTrue(note.is_file())
        self.assertLessEqual(len(note.name.encode("utf-8")), 200)

    def test_unicode_normalization_alias_does_not_overwrite_an_existing_file(self):
        foreign = self.vault / "40-conversations/Cafe\u0301.md"
        foreign.write_text("Preserve the existing user's file.\n", encoding="utf-8")
        before = foreign.read_bytes()
        result = self.run_command("conversation-enable", title="Café")
        note = self.vault / result["note"]
        self.assertEqual(foreign.read_bytes(), before)
        self.assertNotEqual(unicodedata.normalize("NFC", foreign.name), unicodedata.normalize("NFC", note.name))

    def test_review_does_not_clear_a_new_rename_receipt(self):
        a = self.run_command("conversation-enable")
        self.write_name("chat-a", "New name")
        conversations.sync_titles()
        self.assertFalse(conversations.clear_review("chat-a", a["changed_notes"]))
        self.assertTrue(conversations.registered("chat-a")["pending_review"])

    def test_real_watcher_renames_without_a_new_prompt(self):
        self.write_name("chat-a", "Idle before")
        self.run_command("conversation-enable")
        command = [sys.executable, "-X", "utf8", "-B", str(PLUGIN / "scripts/conversation_watcher.py"),
                   "--config", os.environ["CODEX_OBSIDIAN_MEMORY_CONFIG"], "--interval", "0.1", "--cycles", "20"]
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            self.write_name("chat-a", "Idle after")
            deadline = time.monotonic() + 5
            while time.monotonic() < deadline and not (self.vault / "40-conversations/Idle after.md").exists():
                time.sleep(0.05)
            self.assertTrue((self.vault / "40-conversations/Idle after.md").is_file())
            stdout, stderr = process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0, stderr.decode())
            self.assertEqual(stdout, b"")
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_worker_exits_when_its_plugin_script_is_removed(self):
        self.run_command("conversation-enable")
        script = self.root / "conversation_watcher.py"
        shutil.copy2(PLUGIN / "scripts/conversation_watcher.py", script)
        env = {**os.environ, "PYTHONPATH": str(PLUGIN / "scripts")}
        process = subprocess.Popen([sys.executable, "-B", str(script), "--config",
                                    os.environ["CODEX_OBSIDIAN_MEMORY_CONFIG"], "--interval", "0.1"],
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            marker = conversations.state_path().parent / "conversation-watcher.lock"
            deadline = time.monotonic() + 5
            while not marker.exists() and time.monotonic() < deadline:
                time.sleep(0.05)
            self.assertTrue(marker.exists())
            script.unlink()
            _, stderr = process.communicate(timeout=5)
            self.assertEqual(process.returncode, 0, stderr.decode())
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


if __name__ == "__main__":
    unittest.main()
