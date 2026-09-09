from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from memory_core import (
    REVIEW_MARKER,
    WRITEBACK_DISCLOSURE_MARKER,
    clear_review_snapshot,
    find_project_page,
    frontmatter_value,
    load_config,
    path_is_within,
    redact_secrets,
    repository_identity,
    review_changes,
    review_snapshot_path,
    save_review_snapshot,
    vault_path,
)


for stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


@dataclass(frozen=True)
class Scope:
    kind: str
    cwd: Path
    repository: str = ""
    branch: str = ""
    project_page: Path | None = None

    @property
    def eligible(self) -> bool:
        return self.kind in {"vault", "github-project"}


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=True, separators=(",", ":")))


def load_event() -> dict[str, Any]:
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}


def resolve_scope(event: dict[str, Any], config: dict[str, Any], vault: Path) -> Scope:
    cwd_text = str(event.get("cwd") or "")
    cwd = Path(cwd_text) if cwd_text else Path.cwd()
    if path_is_within(cwd, vault):
        return Scope(kind="vault", cwd=cwd)

    repository, branch = repository_identity(cwd)
    if not repository:
        return Scope(kind="none", cwd=cwd, branch=branch)

    normalized = repository.casefold()
    exclusions = {str(value).casefold() for value in config.get("excluded_repositories", [])}
    if normalized in exclusions:
        return Scope(kind="none", cwd=cwd, repository=repository, branch=branch)

    inclusions = {str(value).casefold() for value in config.get("included_repositories", [])}
    owners = {str(value).casefold() for value in config.get("github_owners", [])}
    owner = repository.split("/", 1)[0].casefold()
    project_page = find_project_page(vault, config, repository) if vault.is_dir() else None
    mode = str(config.get("scope_mode") or "github-owner")
    eligible = normalized in inclusions or (mode == "github-owner" and owner in owners)
    if mode == "indexed-only" and project_page is not None:
        eligible = True
    if not eligible:
        return Scope(kind="none", cwd=cwd, repository=repository, branch=branch)
    return Scope(
        kind="github-project",
        cwd=cwd,
        repository=repository,
        branch=branch,
        project_page=project_page,
    )


def build_context(scope: Scope, config: dict[str, Any], vault: Path) -> str:
    vault = vault.resolve()
    chunks: list[str] = []
    included: set[Path] = set()

    def add_note(path: Path) -> str:
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(vault.resolve())
        except (OSError, RuntimeError, ValueError):
            return ""
        if not resolved.is_file() or resolved in included:
            return ""
        included.add(resolved)
        try:
            note = redact_secrets(resolved.read_text(encoding="utf-8"))
        except OSError:
            return ""
        relative = resolved.relative_to(vault)
        chunks.append(f"### {relative}\n{note}")
        return note

    protocol = vault / "AGENTS.md"
    if protocol.is_file():
        add_note(protocol)

    add_note(vault_path(vault, config, "global_memory"))
    unregistered = False
    if scope.kind == "vault":
        add_note(vault_path(vault, config, "home"))
        add_note(vault_path(vault, config, "maintenance"))
        add_note(vault_path(vault, config, "project_index"))
    elif scope.project_page is not None:
        project_text = add_note(scope.project_page)
        link_source = re.sub(r"```.*?```", "", project_text, flags=re.DOTALL)
        for link in re.findall(r"\[\[([^|\]#]+)", link_source):
            link = link.strip()
            target = (
                vault / f"{link}.md"
                if "/" in link or "\\" in link
                else scope.project_page.parent / f"{link}.md"
            )
            try:
                resolved = target.resolve(strict=True)
                resolved.relative_to(scope.project_page.parent.resolve())
                target_text = resolved.read_text(encoding="utf-8")
            except (OSError, RuntimeError, ValueError):
                continue
            if frontmatter_value(target_text, "type").casefold() == "branch":
                working_branch = frontmatter_value(target_text, "working_branch")
                if not scope.branch or working_branch.casefold() != scope.branch.casefold():
                    continue
            add_note(resolved)
    else:
        unregistered = True
        add_note(vault_path(vault, config, "project_index"))
        add_note(vault_path(vault, config, "template"))

    owners = ", ".join(config.get("github_owners", [])) or "explicit inclusions only"
    registration = ""
    if unregistered:
        registration = (
            "\nThis eligible GitHub repository is not indexed yet. Before the task ends, "
            "create one project folder and project home from the template, then link it from "
            "the project index. Create a branch page only when durable branch-specific progress exists."
        )
    identity = (
        f"cwd={scope.cwd}; repository={scope.repository or 'unidentified'}; "
        f"branch={scope.branch or 'unidentified'}"
    )
    return (
        "[Codex Obsidian Memory loaded before this task]\n"
        f"Vault: {vault}\nWorkspace: {identity}{registration}\n"
        f"Automatic GitHub owner scope: {owners}. The vault itself is the maintenance exception.\n\n"
        + "\n\n".join(chunks)
        + "\n\n[End-of-task memory contract]\n"
        "Keep only durable goals, constraints, background, decisions, verified outcomes, reusable "
        "failure lessons, blockers, and next steps. Update only the exact current branch page for "
        "branch progress. Do not store chat transcripts, one-off output, passwords, keys, tokens, "
        "cookies, or other credentials. If any vault Markdown is written, the final reply must contain "
        "a visible 'Knowledge-base writeback review / 知识库回写审查' section that lists every changed "
        "file and the concrete facts added, changed, or removed, so the user can review and correct it. "
        "Do not add that section when nothing was written. Finish the visible review before appending "
        "the hidden review markers."
    )


def change_summary(changes: list[tuple[str, str]]) -> str:
    labels = {"created": "created / 新建", "modified": "modified / 修改", "deleted": "deleted / 删除"}
    lines = [f"- {labels.get(kind, kind)}: {relative}" for kind, relative in changes[:20]]
    if len(changes) > 20:
        lines.append(f"- ... and {len(changes) - 20} more files / 另有 {len(changes) - 20} 个文件")
    return "\n".join(lines)


def main() -> int:
    try:
        event = load_event()
        config = load_config()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Codex Obsidian Memory failed to load: {exc}", file=sys.stderr)
        return 1

    if not config.get("enabled"):
        return 0
    event_name = str(event.get("hook_event_name") or "")
    if event_name not in {"UserPromptSubmit", "SessionStart", "SubagentStart", "Stop"}:
        return 0

    vault_text = str(config.get("vault") or "")
    if not vault_text:
        return 0
    vault = Path(vault_text).resolve()
    scope = resolve_scope(event, config, vault)
    if not scope.eligible:
        if event_name == "Stop":
            emit({"continue": True})
        return 0

    if event_name == "Stop" and not vault.is_dir():
        emit(
            {
                "continue": True,
                "systemMessage": (
                    f"The configured Obsidian memory vault is unavailable: {vault}. "
                    "No memory review was performed."
                ),
            }
        )
        return 0

    if event_name == "Stop":
        last_message = str(event.get("last_assistant_message") or "")
        changes = review_changes(event, vault)
        reviewed = REVIEW_MARKER in last_message
        disclosure_heading = (
            "Knowledge-base writeback review" in last_message
            or "知识库回写审查" in last_message
        )
        disclosed = WRITEBACK_DISCLOSURE_MARKER in last_message and disclosure_heading
        if changes and reviewed and disclosed:
            clear_review_snapshot(event)
            emit({"continue": True})
            return 0
        if not changes and reviewed:
            clear_review_snapshot(event)
            emit({"continue": True})
            return 0
        if bool(event.get("stop_hook_active")):
            clear_review_snapshot(event)
            emit({"continue": True})
            return 0
        if changes and not disclosed:
            emit(
                {
                    "decision": "block",
                    "reason": (
                        "The knowledge base changed during this turn:\n"
                        + change_summary(changes)
                        + "\nBefore finishing, add a visible section titled 'Knowledge-base writeback review' "
                        "or '知识库回写审查'. List every changed file and summarize the exact facts or "
                        "sections added, changed, or removed; invite the user to review and request "
                        f"corrections. Then append {WRITEBACK_DISCLOSURE_MARKER} and {REVIEW_MARKER}. "
                        "Do not expose credentials or paste the full note contents."
                    ),
                }
            )
            return 0
        registration = ""
        if scope.kind == "github-project" and scope.project_page is None:
            registration = "Register this eligible repository in the project index. "
        emit(
            {
                "decision": "block",
                "reason": (
                    "Review durable Obsidian memory before ending. "
                    + registration
                    + "Write only reusable project facts and exact-branch progress; do not write "
                    "chat logs or credentials. If nothing durable changed, do not edit notes. "
                    f"After the review, append {REVIEW_MARKER} to the final reply."
                ),
            }
        )
        return 0

    if not vault.is_dir():
        context = (
            f"The configured Obsidian memory vault is unavailable: {vault}. "
            "Do not claim memory was loaded or updated; continue safely and report the problem."
        )
    else:
        if event_name == "UserPromptSubmit":
            save_review_snapshot(event, vault)
        context = build_context(scope, config, vault)
    emit(
        {
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": context,
            }
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
