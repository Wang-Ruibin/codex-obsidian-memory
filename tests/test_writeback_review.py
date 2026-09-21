from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "plugins" / "codex-obsidian-memory" / "scripts"))
from memory_core import REVIEW_MARKER, WRITEBACK_DISCLOSURE_MARKER
from writeback_review import disclosure_errors


class WritebackReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.vault = Path(self.tmp.name)
        self.changes = [("modified", "projects/demo/main.md"), ("created", "projects/demo/plan.md"),
                        ("deleted", "projects/demo/old.md")]

    def tearDown(self):
        self.tmp.cleanup()

    def review(self, body, heading="## Knowledge-base writeback review"):
        return f"{heading}\n{body}\n{WRITEBACK_DISCLOSURE_MARKER}\n{REVIEW_MARKER}"

    def test_each_created_modified_and_deleted_file_needs_description(self):
        valid = "\n".join(f"- `{path}`: {kind} the deployment decision." for kind, path in self.changes)
        self.assertEqual(disclosure_errors(self.review(valid), self.changes, self.vault), [])
        for body in ("", "- Memory updated.", valid.splitlines()[0],
                     "- projects/demo/main.md, projects/demo/plan.md, projects/demo/old.md: updated.",
                     "\n".join(f"- `{path}`: updated." for _, path in self.changes)):
            with self.subTest(body=body):
                self.assertTrue(disclosure_errors(self.review(body), self.changes, self.vault))

    def test_hidden_quoted_or_outside_section_entries_do_not_count(self):
        entry = "- projects/demo/main.md: added deployment decision."
        for body in (f"<!-- {entry} -->", f"```text\n{entry}\n```", f"~~~\n{entry}\n~~~",
                     f"> {entry}", f"## Other section\n{entry}"):
            self.assertTrue(disclosure_errors(self.review(body), self.changes[:1], self.vault))
        self.assertTrue(disclosure_errors(self.review("", f"We need a Knowledge-base writeback review"),
                                          self.changes[:1], self.vault))

    def test_markers_must_follow_review_in_order(self):
        body = "- projects/demo/main.md: added deployment decision."
        for message in (self.review(body).replace(WRITEBACK_DISCLOSURE_MARKER, ""),
                        self.review(body).replace(REVIEW_MARKER, ""),
                        WRITEBACK_DISCLOSURE_MARKER + self.review(body),
                        REVIEW_MARKER + self.review(body)):
            self.assertTrue(disclosure_errors(message, self.changes[:1], self.vault))

    def test_chinese_and_linked_absolute_paths(self):
        path = (self.vault / self.changes[0][1]).as_posix()
        message = self.review(f"- [main.md](<{path}:12>): 新增部署验证结果。", "**知识库回写审查**")
        self.assertEqual(disclosure_errors(message, self.changes[:1], self.vault), [])

    def test_basename_must_be_unique_in_entire_vault(self):
        other = self.vault / "other" / "main.md"
        other.parent.mkdir()
        other.write_text("Other project", encoding="utf-8")
        body = "- main.md: added deployment decision."
        self.assertTrue(disclosure_errors(self.review(body), self.changes[:1], self.vault))
        body = "- projects/demo/main.md: added deployment decision."
        self.assertEqual(disclosure_errors(self.review(body), self.changes[:1], self.vault), [])

    def test_wrong_link_destination_and_substrings_do_not_count(self):
        for path in ("other/projects/demo/main.md", "projects/demo/main.md.bak",
                     "[projects/demo/main.md](other/main.md)"):
            message = self.review(f"- {path}: added deployment decision.")
            self.assertTrue(disclosure_errors(message, self.changes[:1], self.vault))

    def test_unicode_spaces_and_table_entries(self):
        changes = [("modified", "项目/demo notes/分支.md")]
        message = self.review("| 项目/demo notes/分支.md | 修改部署验证结果 |", "## 知识库回写审查")
        self.assertEqual(disclosure_errors(message, changes, self.vault), [])
        self.assertTrue(disclosure_errors(self.review("- 项目/demo notes/分支.md：已更新记忆",
                                                     "## 知识库回写审查"), changes, self.vault))


if __name__ == "__main__":
    unittest.main()
