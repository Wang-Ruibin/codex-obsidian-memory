from __future__ import annotations

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "codex-obsidian-memory"


class DocumentationTests(unittest.TestCase):
    def test_every_markdown_document_is_bilingual(self) -> None:
        documents = sorted(
            path
            for path in ROOT.rglob("*.md")
            if ".git" not in path.relative_to(ROOT).parts
        )
        self.assertGreater(len(documents), 10)
        for document in documents:
            text = document.read_text(encoding="utf-8-sig")
            with self.subTest(document=str(document.relative_to(ROOT))):
                self.assertRegex(text, r"[A-Za-z]{3,}", "English content is missing")
                self.assertRegex(text, r"[\u3400-\u9fff]", "Chinese content is missing")

    def test_license_and_author_identity(self) -> None:
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8-sig")
        self.assertIn("Copyright (c) 2026 Wang-Ruibin", license_text)
        self.assertIn("MIT 许可证非官方中文译文", license_text)
        manifest = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8-sig")
        )
        self.assertEqual(manifest["author"]["name"], "Wang-Ruibin")
        self.assertEqual(manifest["interface"]["developerName"], "misakimei0331")
        self.assertEqual(manifest["version"], "0.1.2")


if __name__ == "__main__":
    unittest.main()
