from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-obsidian-memory"
sys.path.insert(0, str(PLUGIN / "scripts"))
import layout_migration as migration
import memory_core
from memory_core import (load_config, markdown_snapshot, review_changes,
                         review_snapshot_path, save_config, save_review_snapshot)


class LayoutMigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.vault = self.root / "vault"
        shutil.copytree(PLUGIN / "assets/vault-template/en", self.vault)
        self.env = patch.dict(os.environ, {"CODEX_HOME": str(self.root / "codex"),
                    "CODEX_OBSIDIAN_MEMORY_CONFIG": str(self.root / "state/config.json"),
                    "CODEX_OBSIDIAN_NO_WATCHER": "1"})
        self.env.start()
        # Model a pre-migration installation without modifying the user's vault.
        old = self.vault / "10-memory/reusable"
        old.parent.mkdir(exist_ok=True)
        (self.vault / "30-reusable").rename(old)
        home = self.vault / "00-memory-home.md"
        home.write_text(home.read_text(encoding="utf-8").replace("30-reusable", "10-memory/reusable"), encoding="utf-8")
        for path in old.glob("*.md"):
            path.write_text(path.read_text(encoding="utf-8").replace("30-reusable", "10-memory/reusable"), encoding="utf-8")
        self.config = {"enabled": True, "vault": str(self.vault), "locale": "en", "github_owners": ["Example"],
                       "paths": {**memory_core.DEFAULT_PATHS, "reuse_dir": "10-memory/reusable",
                                 "reuse_index": "10-memory/reusable/index.md", "reuse_template": "10-memory/reusable/template.md"}}
        save_config(self.config)
        self.note = old / "lesson.md"
        self.note.write_text("# Verified lesson\n\nPreserve this verified fact.\n\n[[10-memory/reusable/index]]\n"
                             "[Home](../../00-memory-home.md)\n"
                             "[External](https://example.org/10-memory/reusable/index.md)\n", encoding="utf-8")

    def tearDown(self):
        self.env.stop()
        self.temp.cleanup()

    def plan(self):
        return migration.plan(load_config(), "30-经验", "40-对话")

    def test_plan_is_read_only_and_apply_preserves_facts_and_repairs_links(self):
        before = markdown_snapshot(self.vault)
        config_before = memory_core.config_path().read_bytes()
        planned = self.plan()
        self.assertEqual(markdown_snapshot(self.vault), before)
        self.assertEqual(memory_core.config_path().read_bytes(), config_before)
        result = migration.apply(planned)
        self.assertFalse((self.vault / "10-memory/reusable").exists())
        note = self.vault / "30-经验/lesson.md"
        text = note.read_text(encoding="utf-8")
        self.assertIn("Preserve this verified fact.", text)
        self.assertIn("[[30-经验/index]]", text)
        self.assertIn("[Home](../00-memory-home.md)", text)
        self.assertIn("https://example.org/10-memory/reusable/index.md", text)
        self.assertTrue((self.vault / "40-对话/index.md").is_file())
        self.assertEqual(load_config()["paths"]["reuse_dir"], "30-经验")
        self.assertTrue(result["files"])

    def test_legacy_configuration_without_path_keys_keeps_existing_old_notes(self):
        memory_core.config_path().write_text(json.dumps({"version": 1, "enabled": True, "vault": str(self.vault)}), encoding="utf-8")
        self.assertEqual(load_config()["paths"]["reuse_dir"], "10-memory/reusable")

    def test_target_collision_and_bad_paths_leave_source_untouched(self):
        before = markdown_snapshot(self.vault)
        for reuse, chats in (("20-projects", "40-conversations"), ("../outside", "40-new"),
                             ("nested/lessons", "40-new"), ("30-经验", "30-经验")):
            with self.subTest(reuse=reuse), self.assertRaises(ValueError):
                migration.plan(load_config(), reuse, chats)
        self.assertEqual(markdown_snapshot(self.vault), before)

    def test_changed_vault_requires_fresh_plan(self):
        planned = self.plan()
        self.note.write_text(self.note.read_text(encoding="utf-8") + "\nConcurrent new fact\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "fresh plan"):
            migration.apply(planned)
        self.assertTrue(self.note.exists())
        self.assertFalse((self.vault / "30-经验").exists())

    def test_failed_configuration_publish_restores_source_and_contents(self):
        before = markdown_snapshot(self.vault)
        config_before = memory_core.config_path().read_bytes()
        planned = self.plan()
        with patch.object(migration, "save_config", side_effect=OSError("simulated publication failure")):
            with self.assertRaises(OSError):
                migration.apply(planned)
        self.assertEqual(markdown_snapshot(self.vault), before)
        self.assertEqual(memory_core.config_path().read_bytes(), config_before)
        self.assertTrue(self.note.is_file())

    def test_maintenance_review_receipt_covers_moved_and_external_notes(self):
        event = {"session_id": "maintenance", "turn_id": "turn", "cwd": str(self.root)}
        own = self.vault / "20-projects/own"
        own.mkdir()
        save_review_snapshot(event, self.vault, project_root=own, owner="example/own")
        token = review_snapshot_path(event).stem
        migration.apply(self.plan(), token, "example/own")
        changed = review_changes(event, self.vault, project_root=own, owner="example/own")
        self.assertIn(("deleted", "10-memory/reusable/lesson.md"), changed)
        self.assertIn(("created", "30-经验/lesson.md"), changed)
        self.assertIn(("modified", "00-memory-home.md"), changed)

    def test_other_turn_shared_claim_blocks_migration(self):
        directory = self.vault / ".codex-obsidian-memory/claims"
        directory.mkdir(parents=True)
        (directory / "active.json").write_text('{"token":"another-turn"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "shared-note claim"):
            migration.apply(self.plan())
        self.assertTrue(self.note.is_file())


if __name__ == "__main__":
    unittest.main()
