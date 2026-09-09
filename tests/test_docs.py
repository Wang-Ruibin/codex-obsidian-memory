from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-obsidian-memory"
SKILL = PLUGIN / "skills" / "codex-obsidian-memory"


def heading_levels(path: Path) -> list[int]:
    return [
        len(match.group(1))
        for match in re.finditer(r"(?m)^(#{1,6})\s+", path.read_text(encoding="utf-8-sig"))
    ]


class DocumentationTests(unittest.TestCase):
    def assert_document_pair(self, english: Path, chinese: Path) -> None:
        self.assertTrue(english.is_file(), english)
        self.assertTrue(chinese.is_file(), chinese)
        english_text = english.read_text(encoding="utf-8-sig")
        chinese_text = chinese.read_text(encoding="utf-8-sig")
        self.assertRegex(english_text, r"[A-Za-z]{3,}")
        self.assertRegex(chinese_text, r"[\u3400-\u9fff]")
        self.assertEqual(heading_levels(english), heading_levels(chinese))

    def test_public_explanatory_documents_have_separate_localizations(self) -> None:
        pairs = [
            (ROOT / "README.md", ROOT / "README.zh-CN.md"),
            (ROOT / "CONTRIBUTING.md", ROOT / "docs" / "zh-CN" / "CONTRIBUTING.md"),
            (ROOT / "SECURITY.md", ROOT / "docs" / "zh-CN" / "SECURITY.md"),
            (ROOT / "docs" / "case-study.md", ROOT / "docs" / "zh-CN" / "case-study.md"),
            (SKILL / "SKILL.md", SKILL / "SKILL.zh-CN.md"),
        ]
        for english, chinese in pairs:
            with self.subTest(document=str(english.relative_to(ROOT))):
                self.assert_document_pair(english, chinese)
        for name in ("automation.md", "migration.md", "security.md", "structure.md"):
            self.assert_document_pair(
                SKILL / "references" / name,
                SKILL / "references" / "zh-CN" / name,
            )

    def test_template_and_prompt_locale_file_sets_match(self) -> None:
        template_root = PLUGIN / "assets" / "vault-template"
        english = {
            path.relative_to(template_root / "en")
            for path in (template_root / "en").rglob("*.md")
        }
        chinese = {
            path.relative_to(template_root / "zh-CN")
            for path in (template_root / "zh-CN").rglob("*.md")
        }
        self.assertEqual(english, chinese)
        prompt_root = PLUGIN / "assets" / "prompts"
        self.assertEqual(
            {path.name for path in (prompt_root / "en").glob("*.md")},
            {path.name for path in (prompt_root / "zh-CN").glob("*.md")},
        )

    def test_license_and_author_identity(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8-sig")
        self.assertIn("Copyright (c) 2026 Wang-Ruibin", license_text)
        self.assertNotRegex(license_text, r"[\u3400-\u9fff]")
        self.assertFalse((ROOT / "LICENSE.zh-CN").exists())
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8-sig")
        )
        self.assertEqual(manifest["author"]["name"], "Wang-Ruibin")
        self.assertEqual(manifest["interface"]["developerName"], "misakimei0331")
        self.assertEqual(manifest["version"], "0.4.0")

    def test_agents_is_single_operational_source(self) -> None:
        self.assertTrue((ROOT / "AGENTS.md").is_file())
        self.assertFalse((ROOT / "AGENTS.zh-CN.md").exists())

    def test_chinese_docs_avoid_ambiguous_bold_boundaries(self) -> None:
        case_study = (ROOT / "docs" / "zh-CN" / "case-study.md").read_text(
            encoding="utf-8-sig"
        )
        self.assertNotRegex(case_study, r"\*\*[^*]+\*\*[^\s]")

    def test_readmes_end_with_star_invitation(self) -> None:
        self.assertIn("a little ⭐", (ROOT / "README.md").read_text(encoding="utf-8-sig"))
        self.assertIn(
            "一颗小星星 ⭐",
            (ROOT / "README.zh-CN.md").read_text(encoding="utf-8-sig"),
        )


if __name__ == "__main__":
    unittest.main()
