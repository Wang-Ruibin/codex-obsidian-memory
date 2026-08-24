from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


SCRIPTS = Path(__file__).resolve().parents[1] / "plugins" / "codex-obsidian-memory" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from memory_core import (  # noqa: E402
    branch_slug,
    frontmatter_value,
    github_repository_from_origin,
    redact_secrets,
    validated_paths,
)


class MemoryCoreTests(unittest.TestCase):
    def test_github_origin_formats(self) -> None:
        accepted = {
            "git@github.com:Example/Repo.git": "Example/Repo",
            "https://github.com/Example/Repo.git": "Example/Repo",
            "ssh://git@github.com/Example/Repo.git": "Example/Repo",
        }
        for origin, expected in accepted.items():
            with self.subTest(origin=origin):
                self.assertEqual(github_repository_from_origin(origin), expected)
        self.assertEqual(github_repository_from_origin("https://gitlab.com/Example/Repo.git"), "")
        self.assertEqual(github_repository_from_origin("https://github.com/Example/Repo/extra"), "")

    def test_secret_redaction(self) -> None:
        source = (
            "token=" + "ghp_" + "a" * 30 + "\n"
            "Authorization: Bearer " + "b" * 30 + "\n"
            "-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----"
        )
        result = redact_secrets(source)
        self.assertNotIn("ghp_", result)
        self.assertNotIn("b" * 30, result)
        self.assertNotIn("BEGIN PRIVATE KEY", result)

    def test_paths_cannot_escape_vault(self) -> None:
        self.assertEqual(validated_paths({"home": "custom/home.md"})["home"], "custom/home.md")
        for invalid in ("../outside.md", "/absolute.md", ""):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validated_paths({"home": invalid})
        with self.assertRaises(ValueError):
            validated_paths({"unknown": "note.md"})

    def test_branch_slug_preserves_identity_in_frontmatter_only(self) -> None:
        self.assertEqual(branch_slug("feature/api-v2"), "feature-api-v2")
        self.assertEqual(branch_slug(""), "detached-head")

    def test_identity_values_are_read_only_from_frontmatter(self) -> None:
        note = "---\ntype: project\ngithub_repo: Example/right\n---\nbody github_repo: Example/wrong\n"
        self.assertEqual(frontmatter_value(note, "github_repo"), "Example/right")
        self.assertEqual(frontmatter_value("body github_repo: Example/wrong\n", "github_repo"), "")


if __name__ == "__main__":
    unittest.main()
