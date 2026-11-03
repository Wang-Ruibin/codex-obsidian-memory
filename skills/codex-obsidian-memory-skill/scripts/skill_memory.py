"""Hook-free, explicitly invoked memory workflow. Python 3.11+, standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]
HOME = Path(os.environ.get("CODEX_HOME") or Path.home() / ".codex").resolve()
PROFILE = Path(os.environ.get("CODEX_OBSIDIAN_SKILL_CONFIG") or
               HOME / "obsidian-memory-skill/config.json").resolve()
HOOK_PROFILE = Path(os.environ.get("CODEX_OBSIDIAN_MEMORY_CONFIG") or
                    HOME / "obsidian-memory/config.json").resolve()
if PROFILE == HOOK_PROFILE or PROFILE == (HOME / "config.toml").resolve():
    raise SystemExit("The standalone Skill must use its own configuration, separate from hooks and Codex settings.")
os.environ["CODEX_OBSIDIAN_MEMORY_CONFIG"] = str(PROFILE)
os.environ["CODEX_OBSIDIAN_NO_WATCHER"] = "1"
sys.path.insert(0, str(SKILL_ROOT / "scripts/runtime"))

import conversations
from local_projects import (acquire_lock, clear_local_review, command_local,
                            command_register_github, local_for_workspace, local_registry,
                            registered_project)
from memory_context import Scope, build_context, resolve_scope
from memory_core import (DEFAULT_PATHS, REVIEW_MARKER, WRITEBACK_DISCLOSURE_MARKER,
                         atomic_write, claim_shared_file, clear_review_snapshot,
                         load_config, normalized_repository, path_is_within,
                         redact_secrets, review_changes, review_snapshot_path,
                         save_config, save_review_snapshot, validated_paths)
from reuse_memory import read_reference, search
from writeback_review import disclosure_errors


def output(value: object) -> int:
    print(json.dumps(value, ensure_ascii=False, indent=2))
    return 0


def configured(*, enabled: bool = True) -> tuple[dict, Path]:
    config = load_config()
    if not PROFILE.is_file() or config.get("integration_mode") != "skill":
        raise ValueError("Initialize the standalone Skill's own profile first; hook configuration is not reused.")
    if enabled and not config.get("enabled"):
        raise ValueError("Standalone memory is disabled; no content was loaded.")
    vault = Path(config["vault"]).resolve(strict=True)
    if not vault.is_dir():
        raise ValueError("Configured vault is unavailable")
    return config, vault


def current_session(args: argparse.Namespace) -> str:
    return conversations.session_id(getattr(args, "session_id", None))


def scope_for(args: argparse.Namespace, config: dict, vault: Path) -> Scope:
    value = current_session(args)
    scope = resolve_scope({"cwd": str(args.cwd.resolve()), "session_id": value}, config, vault)
    # Retained disabled chats still synchronize filenames when this Skill is invoked.
    # This route never loads their factual content or global context.
    if scope.kind == "none" and not scope.repository and local_for_workspace(args.cwd.resolve(), config) is None:
        entry = conversations.registered(value)
        if entry:
            return Scope("conversation", args.cwd.resolve(), session_id=value,
                         project_page=conversations.note_path(vault, config, entry))
    return scope


def content_allowed(scope: Scope) -> bool:
    if scope.kind == "conversation":
        return bool(conversations.registered(scope.session_id)["enabled"])
    return scope.eligible


def init(args: argparse.Namespace) -> int:
    if PROFILE.exists():
        raise ValueError("A standalone profile already exists. Use status; do not initialize an existing setup twice.")
    owners = sorted({v.strip() for v in args.github_owner or [] if v.strip()}, key=str.casefold)
    if bool(owners) == bool(args.local_only):
        raise ValueError("Choose --local-only or at least one --github-owner")
    if args.local_only and args.exclude:
        raise ValueError("--local-only cannot be combined with GitHub exclusions")
    overrides = {}
    for item in args.path or []:
        if "=" not in item:
            raise ValueError("Expected --path KEY=RELATIVE_PATH")
        key, value = item.split("=", 1)
        overrides[key.strip()] = value.strip().replace("\\", "/")
    paths = validated_paths(overrides)
    if overrides and not args.no_template:
        raise ValueError("Use --no-template with custom path mappings to preserve an existing layout")
    exclusions = sorted({normalized_repository(v) for v in args.exclude or []})
    vault = args.vault.expanduser().resolve()
    if vault == Path(vault.anchor) or vault == Path.home().resolve():
        raise ValueError("Select a specific vault directory, not a drive or user home")
    planned = {}
    if not args.no_template:
        for locale in ("shared", args.locale):
            root = SKILL_ROOT / "assets/vault-template" / locale
            for source in sorted(root.rglob("*")):
                if source.is_file():
                    target = vault / source.relative_to(root)
                    if not path_is_within(target, vault) or target.is_symlink():
                        raise ValueError("Template destination escapes the vault or is a symlink")
                    if not target.exists():
                        planned[target] = source
    vault.mkdir(parents=True, exist_ok=True)
    for target, source in planned.items():
        target.parent.mkdir(parents=True, exist_ok=True)
        # Exclusive creation preserves a file created concurrently after planning.
        try:
            with target.open("xb") as handle:
                handle.write(source.read_bytes())
        except FileExistsError:
            planned[target] = None
    changed = [p.relative_to(vault).as_posix() for p, source in planned.items()
               if source and p.suffix == ".md"]
    config = {"integration_mode": "skill", "enabled": True, "vault": str(vault),
              "locale": args.locale, "scope_mode": "local-only" if args.local_only else "github-owner",
              "github_owners": owners, "included_repositories": [], "excluded_repositories": exclusions,
              "local_projects": [], "paths": paths, "setup_pending": changed,
              "updated_at": datetime.now(timezone.utc).isoformat()}
    save_config(config)
    return output({"mode": "skill", "config": str(PROFILE), "vault": str(vault),
                   "changed_notes": changed, "next": "Run start, review setup changes, then finish. No hooks or global settings were installed."})


def task_path(value: str) -> Path:
    if not re.fullmatch(r"[0-9a-f]{32}", value):
        raise ValueError("Use the task_id returned by start")
    return PROFILE.parent / "tasks" / f"{value}.json"


def event_for(task: dict) -> dict:
    return {"session_id": task["session_id"], "turn_id": "skill:" + task["task_id"]}


def load_task(args: argparse.Namespace, config: dict, vault: Path) -> tuple[dict, Scope]:
    path = task_path(args.task_id)
    task = json.loads(path.read_text(encoding="utf-8"))
    if task["vault"] != str(vault) or task["cwd"] != str(args.cwd.resolve()) or task["session_id"] != current_session(args):
        raise ValueError("This task belongs to another vault, workspace or conversation")
    scope = scope_for(args, config, vault)
    if scope.owner != task["owner"] or scope.branch != task["branch"]:
        raise ValueError("Project identity or branch changed; return to the original workspace to finish its memory review")
    snapshot = review_snapshot_path(event_for(task))
    if not snapshot.is_file():
        raise ValueError("The task's original review baseline is missing; do not silently create a new one")
    return task, scope


def start(args: argparse.Namespace) -> int:
    config, vault = configured()
    value = current_session(args)
    if not args.task_id:
        matches = []
        for path in (PROFILE.parent / "tasks").glob("*.json"):
            item = json.loads(path.read_text(encoding="utf-8"))
            if item["session_id"] == value and item["cwd"] == str(args.cwd.resolve()):
                matches.append(item["task_id"])
        if len(matches) > 1:
            raise ValueError("Several unfinished tasks exist; resume one explicitly with --task-id")
        if matches:
            args.task_id = matches[0]
    if args.task_id:
        task, scope = load_task(args, config, vault)
    else:
        scope = scope_for(args, config, vault)
        if not scope.eligible:
            return output({"eligible": False, "context": "", "reason": "Outside configured project scope; ordinary conversation memory is off by default."})
        task = {"task_id": uuid.uuid4().hex, "session_id": value, "cwd": str(args.cwd.resolve()),
                "vault": str(vault), "owner": scope.owner, "branch": scope.branch}
        save_review_snapshot(event_for(task), vault, owner=scope.owner,
                             project_root=scope.review_root, files=scope.review_files)
        atomic_write(task_path(task["task_id"]), json.dumps(task, ensure_ascii=False) + "\n")
    if scope.kind == "conversation":
        conversations.sync_titles(config, only=value)
        scope = scope_for(args, config, vault)
    return output({"eligible": True, "content_memory": content_allowed(scope), **task,
                   "review_token": review_snapshot_path(event_for(task)).stem,
                   "context": build_context(scope, config, vault) if content_allowed(scope) else "",
                   "next": "Search applicable experience, do the task, inspect changes, then finish with a visible per-file review."})


def pending_changes(task: dict, scope: Scope, config: dict, vault: Path) -> tuple[list, dict]:
    changes = review_changes(event_for(task), vault, owner=scope.owner,
                             project_root=scope.review_root, files=scope.review_files)
    entry = (conversations.registered(scope.session_id) if scope.kind == "conversation" else
             registered_project(config, scope.project_id) if scope.project_id else {}) or {}
    pending = list(entry.get("pending_review", [])) + config.get("setup_pending", [])
    for relative in pending:
        target = vault / relative
        if (Path(relative).is_absolute() or ".." in Path(relative).parts or target.suffix != ".md"
                or target.is_symlink() or not path_is_within(target, vault)):
            raise ValueError("A pending review receipt is not a safe vault-relative Markdown path")
        if not any(path == relative for _, path in changes):
            changes.append(("modified" if (vault / relative).is_file() else "deleted", relative))
    hashes = {relative: hashlib.sha256((vault / relative).read_bytes()).hexdigest()
              if (vault / relative).is_file() else None for _, relative in changes}
    return changes, hashes


def review(args: argparse.Namespace) -> int:
    config, vault = configured(enabled=False)
    task, scope = load_task(args, config, vault)
    lock = task_path(task["task_id"]).with_suffix(".lock")
    fd = acquire_lock(lock, "This task's memory review is already running", wait_seconds=2)
    try:
        os.close(fd)
        initial_entry = (conversations.registered(scope.session_id) if scope.kind == "conversation" else
                         registered_project(config, scope.project_id) if scope.project_id else {}) or {}
        expected_pending = list(initial_entry.get("pending_review", []))
        changes, hashes = pending_changes(task, scope, config, vault)
        if args.command == "changes":
            return output({"task_id": task["task_id"], "changes": changes,
                           "next": "Write a concrete per-file review in the user's language; run finish --review-file with that draft."})
        if changes:
            if not args.review_file:
                raise ValueError("Memory changed. Provide --review-file with the visible per-file writeback review")
            message = args.review_file.read_text(encoding="utf-8-sig")
            # Standalone reviews do not require user-facing hidden Hook markers.
            message = message.replace(WRITEBACK_DISCLOSURE_MARKER, "").replace(REVIEW_MARKER, "")
            errors = disclosure_errors(message + "\n" + WRITEBACK_DISCLOSURE_MARKER + "\n" + REVIEW_MARKER, changes, vault)
            if errors:
                return output({"completed": False, "errors": errors, "changes": changes}) or 1
        if pending_changes(task, scope, load_config(), vault) != (changes, hashes):
            raise ValueError("Memory changed during review. Refresh changes and review the latest files")
        if scope.kind == "conversation":
            if not conversations.clear_review(scope.session_id, expected_pending):
                raise ValueError("Conversation filenames changed during review; refresh changes")
        if scope.project_id:
            if not clear_local_review(scope.project_id, expected_pending):
                raise ValueError("Local registration receipts changed during review; refresh changes")
        if config.get("setup_pending"):
            # Local receipt cleanup may have just saved a newer profile.
            latest = load_config()
            if latest.get("setup_pending") == config["setup_pending"]:
                latest.pop("setup_pending")
                save_config(latest)
        clear_review_snapshot(event_for(task))
        if review_snapshot_path(event_for(task)).exists():
            raise ValueError("Review state could not be cleared; the original task is retained")
        task_path(task["task_id"]).unlink()
        return output({"completed": True, "changes": changes,
                       "next": "Show the validated review in the final reply and invite corrections. The host has no automatic Stop gate."})
    finally:
        lock.unlink(missing_ok=True)


def retrieval(args: argparse.Namespace) -> int:
    config, vault = configured()
    scope = scope_for(args, config, vault)
    if not content_allowed(scope):
        raise ValueError("Memory content is disabled or outside scope; no notes were loaded")
    if scope.kind == "conversation":
        relative = scope.project_page.relative_to(vault).as_posix()
        if args.command == "read" and args.path != relative:
            raise ValueError("Conversation reads are limited to its own note")
        text = redact_secrets(conversations.own_text(scope.project_page, scope.session_id))
        if args.command == "search":
            return output({"results": [{"path": relative}] if any(t.casefold() in text.casefold() for t in args.query.split()) else []})
        return output({"path": relative, "lines": [{"line": i, "text": line[:1000]}
                       for i, line in enumerate(text.splitlines(), 1)
                       if args.start_line <= i < args.start_line + args.line_count]})
    return output(search(vault, config, args.query, args.scope, args.limit) if args.command == "search" else
                  read_reference(vault, config, args.path, args.start_line, args.line_count))


def manage(args: argparse.Namespace) -> int:
    config, vault = configured(enabled=args.command not in {"status", "enable", "disable", "validate", "local-list"})
    if args.command == "status":
        return output({"mode": "skill", "config": str(PROFILE), **config})
    if args.command in {"enable", "disable"}:
        config["enabled"] = args.command == "enable"
        save_config(config)
        return output({"enabled": config["enabled"], "notes_retained": True})
    if args.command == "validate":
        import validate_vault
        return validate_vault.main()
    if args.command in {"include", "exclude"}:
        value = normalized_repository(args.repository)
        for key in ("included_repositories", "excluded_repositories"):
            config[key] = [v for v in config[key] if v.casefold() != value.casefold()]
        config["excluded_repositories" if args.command == "exclude" else "included_repositories"].append(value)
        save_config(config)
        return output({"repository": value, "excluded": args.command == "exclude"})
    if args.command == "local-list":
        return output(local_registry(config))
    if args.command.startswith("local-"):
        return command_local(args)
    if args.command.startswith("conversation-"):
        if args.command == "conversation-sync":
            return output({"changed_notes": conversations.sync_titles(config, only=current_session(args))})
        return conversations.command(args)
    task, scope = load_task(args, config, vault)
    args.review_token = review_snapshot_path(event_for(task)).stem
    if args.command == "register-github":
        return command_register_github(args)
    if scope.kind not in {"github-project", "local-project"}:
        raise ValueError("Shared claims require an eligible project task")
    return output({"claimed": claim_shared_file(args.review_token, scope.owner, args.path, vault, config)})


def parser() -> argparse.ArgumentParser:
    cli = argparse.ArgumentParser(description="Standalone Obsidian memory Skill; no hooks or background processes.")
    sub = cli.add_subparsers(dest="command", required=True)
    setup = sub.add_parser("init")
    setup.add_argument("--vault", type=Path, required=True)
    setup.add_argument("--github-owner", action="append")
    setup.add_argument("--local-only", action="store_true")
    setup.add_argument("--locale", choices=("en", "zh-CN"), default="en")
    setup.add_argument("--exclude", action="append")
    setup.add_argument("--path", action="append", help="KEY=RELATIVE_PATH for existing layouts")
    setup.add_argument("--no-template", action="store_true")
    setup.set_defaults(handler=init)
    for name in ("start", "changes", "finish", "register-github", "claim-shared", "search", "read"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--cwd", type=Path, default=Path.cwd())
        cmd.add_argument("--session-id", help="Actual host session ID; defaults to CODEX_THREAD_ID")
        if name in {"start", "changes", "finish", "register-github", "claim-shared"}:
            cmd.add_argument("--task-id", required=name != "start")
        if name == "finish":
            cmd.add_argument("--review-file", type=Path)
        if name == "claim-shared":
            cmd.add_argument("path")
        if name == "search":
            cmd.add_argument("query")
            cmd.add_argument("--scope", choices=("auto", "shared", "projects"), default="auto")
            cmd.add_argument("--limit", type=int, choices=range(1, 11), default=5)
        if name == "read":
            cmd.add_argument("path")
            cmd.add_argument("--start-line", type=int, default=1)
            cmd.add_argument("--line-count", type=int, choices=range(1, 81), default=40)
        cmd.set_defaults(handler=start if name == "start" else review if name in {"changes", "finish"} else
                          retrieval if name in {"search", "read"} else manage)
    for name in ("status", "enable", "disable", "validate", "local-list", "include", "exclude", "local-register",
                 "local-enable", "local-disable", "local-move", "conversation-enable", "conversation-disable",
                 "conversation-list", "conversation-sync"):
        cmd = sub.add_parser(name)
        if name in {"include", "exclude"}:
            cmd.add_argument("repository")
        if name == "local-register":
            cmd.add_argument("--path", type=Path, required=True)
            cmd.add_argument("--name")
            cmd.add_argument("--project-id")
        elif name.startswith("local-") and name != "local-list":
            cmd.add_argument("project_id")
            if name == "local-move":
                cmd.add_argument("--path", type=Path, required=True)
        if name.startswith("conversation-"):
            cmd.add_argument("--cwd", type=Path, default=Path.cwd())
            cmd.add_argument("--session-id")
            cmd.add_argument("--title")
            cmd.add_argument("--freeze-title", action="store_true")
        cmd.set_defaults(handler=manage)
    return cli


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    try:
        args = parser().parse_args()
        raise SystemExit(args.handler(args))
    except (OSError, ValueError, KeyError) as exc:
        print(f"error={exc}", file=sys.stderr)
        raise SystemExit(1)
