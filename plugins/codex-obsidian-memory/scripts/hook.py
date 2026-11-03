from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from memory_context import Scope, build_context, resolve_scope
from writeback_review import disclosure_errors
from local_projects import find_local_home, local_for_workspace, registered_project, clear_local_review
import conversations

from memory_core import (
    REVIEW_MARKER,
    WRITEBACK_DISCLOSURE_MARKER,
    clear_review_snapshot,
    find_project_page,
    frontmatter_value,
    git_value,
    note_identity,
    load_config,
    path_is_within,
    redact_secrets,
    repository_identity,
    repository_allowed,
    review_changes,
    review_snapshot_path,
    save_review_snapshot,
    vault_path,
)


for stream in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


def emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=True, separators=(",", ":")))


def load_event() -> dict[str, Any]:
    raw = sys.stdin.read()
    return json.loads(raw) if raw.strip() else {}


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
    try:
        scope = resolve_scope(event, config, vault)
        if scope.kind == "conversation":
            conversations.sync_titles(config, only=scope.session_id)
            scope = resolve_scope(event, config, vault)
    except (OSError, ValueError) as exc:
        print(f"Codex Obsidian Memory scope error: {exc}", file=sys.stderr)
        return 1
    watcher_warning = ""
    try:
        conversations.ensure_watcher()
    except (OSError, ValueError):
        if scope.kind == "conversation":
            watcher_warning = "Automatic title watcher could not start; the current note is retained. Retry conversation-sync or the next prompt."
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
        owner = scope.owner
        try:
            changes = review_changes(event, vault, project_root=scope.review_root,
                                     owner=owner, files=scope.review_files)
        except ValueError as exc:
            emit({"decision": "block", "reason": str(exc)})
            return 0
        local = registered_project(config, scope.project_id) if scope.project_id else None
        conversation = conversations.registered(scope.session_id) if scope.kind == "conversation" else None
        pending = (conversation or local or {}).get("pending_review", [])
        for relative in pending:
            if not any(path == relative for _, path in changes):
                changes.append(("modified" if (vault / relative).exists() else "deleted", relative))
        reviewed = REVIEW_MARKER in last_message
        errors = disclosure_errors(last_message, changes, vault) if changes else []
        disclosed = not errors
        if changes and reviewed and disclosed:
            if conversation and not conversations.clear_review(scope.session_id, pending):
                emit({"decision": "block", "reason": "The conversation title changed during review. Review its latest note paths again."})
                return 0
            clear_review_snapshot(event)
            if local:
                clear_local_review(scope.project_id)
            emit({"continue": True})
            return 0
        if not changes and reviewed:
            clear_review_snapshot(event)
            emit({"continue": True})
            return 0
        if bool(event.get("stop_hook_active")) and not changes:
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
                        + "\nReview problems:\n- " + "\n- ".join(errors)
                        + "\nBefore finishing, add a visible section titled 'Knowledge-base writeback review' "
                        "or '知识库回写审查'. List every changed file and summarize the exact facts or "
                        "sections added, changed, or removed. Use one bullet per file with its "
                        "vault-relative path and a concrete summary, not just 'updated'; invite the user to review and request "
                        f"corrections. Then append {WRITEBACK_DISCLOSURE_MARKER} and {REVIEW_MARKER}. "
                        "Do not expose credentials or paste the full note contents."
                    ),
                }
            )
            return 0
        registration = ""
        if scope.kind == "github-project" and scope.project_page is None:
            registration = "Register this eligible repository in the project index. "
        if scope.kind == "local-project" and scope.project_page is None:
            registration = "Restore the registered local project home using its existing project_id. "
        emit(
            {
                "decision": "block",
                "reason": (
                    "Review durable Obsidian memory before ending. "
                    + registration
                    + "Write only durable facts in this scope's own note, using exact-branch pages for projects; do not write "
                    "unverified shared lessons. Consider distilling verified cross-project methods "
                    "with sources and applicability, updating the shared index without duplicating facts. Do not write "
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
            owner = scope.owner
            save_review_snapshot(event, vault, owner=owner,
                                 project_root=scope.review_root, files=scope.review_files)
        context = build_context(scope, config, vault)
        if event_name == "UserPromptSubmit" and scope.kind != "vault":
            snapshot = review_snapshot_path(event)
            if snapshot is not None:
                shared_guidance = (
                    "\n[Concurrent shared-note editing]\n"
                    "Before editing global memory or a shared lesson, reserve its vault-relative path with "
                    f"claim-shared <path> --review-token {snapshot.stem} --cwd <workspace>. "
                    "Only this turn may then modify and review that shared note; concurrent claims fail. "
                    "If a claim cannot be made, record the finding on this project's page and retry shared "
                    "distillation after the other conversation finishes. Project reviews cover this project's "
                    "folder and explicitly claimed shared notes; other projects' edits are never this review.\n"
                )
                context = context.replace("\n\n[Cross-project reference discovery]",
                                          shared_guidance + "\n[Cross-project reference discovery]", 1)
    emit(
        {
            **({"systemMessage": watcher_warning} if watcher_warning else {}),
            "hookSpecificOutput": {
                "hookEventName": event_name,
                "additionalContext": context,
            }
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
