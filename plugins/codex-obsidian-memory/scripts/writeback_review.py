"""Check visible per-file disclosures without persisting or comparing note bodies.

This is a coverage and minimum-description check, not a semantic truth checker.
The documented format is one bullet per file, with a vault-relative path and facts.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

from memory_core import REVIEW_MARKER, WRITEBACK_DISCLOSURE_MARKER


def visible_markdown(text: str) -> str:
    """Exclude comments, fenced examples and blockquotes from review evidence."""
    text = re.sub(r"<!--.*?(?:-->|\Z)", "", text, flags=re.DOTALL)
    lines = []
    fence = ""
    for line in text.splitlines():
        marker = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if not fence:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = ""
            continue
        if not fence and not re.match(r"^\s*>|^(?: {4}|\t)", line):
            lines.append(line)
    return "\n".join(lines)


def review_section(text: str) -> str:
    lines = text.splitlines()
    start = None
    level = 0
    for index, line in enumerate(lines):
        cleaned = line.strip().strip("#* :：")
        if cleaned in {"Knowledge-base writeback review", "知识库回写审查",
                       "Knowledge-base writeback review / 知识库回写审查"}:
            start = index + 1
            heading = re.match(r"^(#{1,6})\s", line)
            level = len(heading.group(1)) if heading else 6
            break
    if start is None:
        return ""
    end = len(lines)
    for index in range(start, len(lines)):
        heading = re.match(r"^(#{1,6})\s", lines[index])
        if heading and len(heading.group(1)) <= level:
            end = index
            break
    return "\n".join(lines[start:end])


def meaningful_summary(text: str) -> bool:
    # A path and a generic operation alone do not explain what the user must review.
    text = re.sub(r"<[^>]*>|https?://\S+", " ", text)
    text = re.sub(r"[^\s`|\[\]()]+\.md(?::\d+)?", " ", text)
    text = re.sub(r"\b(?:added|created|modified|updated|deleted|removed|changed|file|note|memory|done)\b",
                  " ", text, flags=re.IGNORECASE)
    text = re.sub(r"新增|新建|修改|更新|删除|移除|已完成|文件|笔记|记忆", " ", text)
    words = re.findall(r"[A-Za-z0-9]+", text)
    han = re.findall(r"[\u3400-\u9fff]", text)
    return len(words) >= 2 or len(han) >= 4


def disclosure_errors(message: str, changes: list[tuple[str, str]], vault: Path) -> list[str]:
    errors = []
    disclosure = message.find(WRITEBACK_DISCLOSURE_MARKER)
    reviewed = message.find(REVIEW_MARKER)
    if disclosure < 0 or reviewed < disclosure:
        errors.append("Put disclosure and review markers after the visible review, in that order.")
    # Only content preceding the disclosure marker can fulfill the contract.
    visible = visible_markdown(message[:disclosure] if disclosure >= 0 else message)
    section = review_section(visible)
    if not section.strip():
        return errors + ["Missing a visible writeback review section with file entries."]

    # Include unchanged notes when checking basename ambiguity. Deleted files exist
    # only in the change list. Relative paths remain the preferred stable identity.
    paths = {relative for _, relative in changes}
    paths.update(path.relative_to(vault).as_posix() for path in vault.rglob("*.md"))
    basenames = Counter(Path(path).name for path in paths)
    entries = [line.strip() for line in section.splitlines()
               if re.match(r"^\s*(?:[-*+]\s|\d+[.)]\s|\|)", line)]
    for _, relative in changes:
        basename = Path(relative).name
        aliases = {relative, (vault.resolve() / relative).as_posix()}
        if basenames[basename] == 1:
            aliases.add(basename)
        found = False
        for entry in entries:
            entry = unquote(entry).replace("\\", "/")
            # Strip links after replacing their destination with its path, so the
            # label cannot falsely identify one file while linking another.
            entry = re.sub(r"\[([^\]]*)\]\(<?([^)>]+)>?\)", r"\2", entry)
            for alias in sorted(aliases, key=len, reverse=True):
                pattern = r"(?<![\w./-])" + re.escape(alias) + r"(?::\d+)?(?![\w./-])"
                match = re.search(pattern, entry)
                if match and meaningful_summary(entry[:match.start()] + entry[match.end():]):
                    found = True
                    break
            if found:
                break
        if not found:
            errors.append(f"Missing a concrete per-file summary for: {relative}")
    return errors
