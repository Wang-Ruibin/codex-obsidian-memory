"""Explicit, planned relocation of optional vault areas. Never move the vault."""
from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote

from local_projects import acquire_lock
from memory_core import (atomic_write, config_path, load_config, path_is_within,
                         review_payload_for_token, save_config, validated_paths, vault_path)


def is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def relocated(path: Path, moves: list[tuple[Path, Path]]) -> Path:
    for old, new in moves:
        if path_is_within(path, old):
            return new / path.relative_to(old)
    return path


def rewrite(text: str, source: Path, destination: Path, vault: Path,
            moves: list[tuple[Path, Path]]) -> str:
    replacements = [(old.relative_to(vault).as_posix(), new.relative_to(vault).as_posix())
                    for old, new in moves]

    def prefix(value: str) -> str:
        for old, new in replacements:
            for separator in ("/", "\\"):
                before, after = old.replace("/", separator), new.replace("/", separator)
                if value.casefold() == before.casefold() or value.casefold().startswith((before + separator).casefold()):
                    return after + value[len(before):]
                absolute = str(vault).replace("\\", separator).replace("/", separator) + separator
                if value.casefold().startswith((absolute + before).casefold()):
                    return absolute + after + value[len(absolute + before):]
        return value

    def wiki(match: re.Match[str]) -> str:
        value = match.group(1)
        target, marker, extra = value.partition("|")
        path, anchor, heading = target.partition("#")
        return "[[" + prefix(path) + (anchor + heading if anchor else "") + (marker + extra if marker else "") + "]]"

    text = re.sub(r"\[\[([^\]\n]+)\]\]", wiki, text)
    # Inline documented paths are references too; external URLs remain unchanged.
    text = re.sub(r"`([^`\n]+)`", lambda m: "`" + prefix(m.group(1)) + "`", text)

    def markdown(match: re.Match[str]) -> str:
        value = match.group(1)
        angled = value.startswith("<") and value.endswith(">")
        raw = value[1:-1] if angled else value
        if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*://|^(?:mailto:|#)", raw):
            return match.group()
        raw_path, marker, anchor = raw.partition("#")
        decoded = unquote(raw_path)
        old_target = Path(decoded)
        absolute = old_target.is_absolute()
        old_target = old_target.resolve() if absolute else (source.parent / decoded).resolve()
        if not path_is_within(old_target, vault):
            return match.group()
        new_target = relocated(old_target, moves)
        if new_target == old_target and source == destination:
            return match.group()
        result = new_target.as_posix() if absolute else os.path.relpath(new_target, destination.parent).replace("\\", "/")
        if "%" in raw_path:
            result = quote(result, safe="/:-._~")
        result += marker + anchor if marker else ""
        return "](" + ("<" + result + ">" if angled or " " in result else result) + ")"

    return re.sub(r"\]\((<[^>\n]+>|[^)\s]+)\)", markdown, text)


def plan(config: dict[str, Any], reuse_dir: str, conversations_dir: str,
         conversation_index: str | None = None) -> dict[str, Any]:
    vault = Path(config["vault"]).resolve()
    paths = dict(config["paths"])
    paths.update(reuse_dir=reuse_dir, conversations_dir=conversations_dir)
    paths["reuse_index"] = reuse_dir + "/" + Path(paths["reuse_index"]).name
    paths["reuse_template"] = reuse_dir + "/" + Path(paths["reuse_template"]).name
    paths["conversation_index"] = conversation_index or conversations_dir + "/" + Path(paths["conversation_index"]).name
    paths = validated_paths(paths)
    changed_config = {**config, "paths": paths}
    roots = [vault_path(vault, changed_config, key) for key in ("reuse_dir", "conversations_dir", "projects_dir")]
    if (any(len(root.relative_to(vault).parts) != 1 for root in roots[:2])
            or any(path_is_within(a, b) or path_is_within(b, a)
                   for i, a in enumerate(roots) for b in roots[i + 1:])):
        raise ValueError("Experience, conversations and projects must be separate root-level folders")
    moves = []
    for key in ("reuse_dir", "conversations_dir"):
        old, new = vault_path(vault, config, key), vault_path(vault, changed_config, key)
        if old == new:
            continue
        if new.exists():
            raise ValueError(f"Destination already exists; no files were overwritten: {new}")
        if old.exists():
            if is_link(old) or any(is_link(path) for path in old.rglob("*")):
                raise ValueError("Migration refuses symbolic links and junctions")
            moves.append((old, new))
    writes, before, rows = {}, {}, []
    for path in sorted(vault.rglob("*.md")):
        if any(part.startswith(".") for part in path.relative_to(vault).parts):
            continue
        if is_link(path) or not path_is_within(path, vault):
            raise ValueError("Migration refuses linked Markdown files")
        raw = path.read_bytes()
        text = raw.decode("utf-8-sig")
        target = relocated(path, moves)
        new_text = rewrite(text, path, target, vault, moves)
        if new_text != text or path != target:
            relative, new_relative = path.relative_to(vault).as_posix(), target.relative_to(vault).as_posix()
            before[relative] = hashlib.sha256(raw).hexdigest()
            if relative != new_relative:
                before.setdefault(new_relative, None)
            if new_text != text:
                writes[target] = new_text
            rows.append({"from": relative, "to": new_relative, "references_updated": new_text != text})
    # A conversation index is created even when no conversation has opted in.
    index = vault_path(vault, changed_config, "conversation_index")
    if not index.exists() and not any(row["to"] == index.relative_to(vault).as_posix() for row in rows):
        home_link = vault_path(vault, changed_config, "home").relative_to(vault).with_suffix("").as_posix()
        title = "对话记忆" if config.get("locale") == "zh-CN" else "Conversation memory"
        writes[index] = (f"---\ntype: conversation-index\n---\n\n# {title}\n\n← [[{home_link}]]\n\n"
                         "<!-- conversations:start -->\n<!-- conversations:end -->\n")
        before.setdefault(index.relative_to(vault).as_posix(), None)
        rows.append({"from": None, "to": index.relative_to(vault).as_posix(), "references_updated": True})
    home = vault_path(vault, changed_config, "home")
    home_text = writes.get(home, home.read_text(encoding="utf-8"))
    index_link = index.relative_to(vault).with_suffix("").as_posix()
    if "[[" + index_link not in home_text:
        writes[home] = home_text + "\n- [[" + index_link + "]]\n"
        before.setdefault(home.relative_to(vault).as_posix(), hashlib.sha256(home.read_bytes()).hexdigest())
        if not any(row["to"] == home.relative_to(vault).as_posix() for row in rows):
            rows.append({"from": home.relative_to(vault).as_posix(), "to": home.relative_to(vault).as_posix(),
                         "references_updated": True})
    return {"vault": vault, "config": changed_config, "moves": moves, "writes": writes, "before": before,
            "files": rows, "config_before": config_path().read_bytes()}


def apply(planned: dict[str, Any], review_token: str | None = None, owner: str = "") -> dict[str, Any]:
    config_lock = config_path().with_suffix(".local-projects.lock")
    descriptor = acquire_lock(config_lock, "Another registration or configuration update is running")
    os.close(descriptor)
    try:
        return apply_locked(planned, review_token, owner)
    finally:
        config_lock.unlink(missing_ok=True)


def apply_locked(planned: dict[str, Any], review_token: str | None, owner: str) -> dict[str, Any]:
    vault, moves, writes = planned["vault"], planned["moves"], planned["writes"]
    directory = vault / ".codex-obsidian-memory"
    if not path_is_within(directory, vault):
        raise ValueError("Layout lock escapes vault")
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "layout.lock"
    descriptor = acquire_lock(lock, "Another vault layout migration is running")
    os.close(descriptor)
    originals, completed, moved = {}, [], []
    old_config = config_path().read_text(encoding="utf-8")
    from conversations import state_path
    conversation_state = state_path()
    old_state = conversation_state.read_bytes() if conversation_state.is_file() else None
    state_published = False
    try:
        if config_path().read_bytes() != planned["config_before"]:
            raise ValueError("Configuration changed after migration planning; produce a fresh plan")
        if (directory / "conversations.lock").exists():
            raise ValueError("A conversation update is active; retry migration after it finishes")
        for claim in (directory / "claims").glob("*.json"):
            data = json.loads(claim.read_text(encoding="utf-8"))
            if data.get("token") != review_token:
                raise ValueError("Another conversation holds a shared-note claim; finish it before migration")
        for relative, digest in planned["before"].items():
            path = vault / relative
            actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            if actual != digest:
                raise ValueError("Vault changed after migration planning; produce a fresh plan")
        if review_token:
            snapshot, payload = review_payload_for_token(review_token, owner, vault)
            payload.setdefault("maintenance_files", {}).update(planned["before"])
            atomic_write(snapshot, json.dumps(payload, ensure_ascii=False) + "\n")
        for old, new in moves:
            # Both absolute paths were resolved inside this vault before any move.
            if not path_is_within(old, vault) or not path_is_within(new, vault) or new.exists():
                raise ValueError("Unsafe or occupied migration destination")
            old.rename(new)
            moved.append((old, new))
        for path, text in writes.items():
            originals[path] = path.read_bytes() if path.exists() else None
            atomic_write(path, text)
            completed.append(path)
        if old_state is not None:
            state = json.loads(old_state)
            for entry in state["entries"].values():
                entry["note"] = relocated(vault / entry["note"], moves).relative_to(vault).as_posix()
                pending = set(entry.get("pending_review", []))
                pending.update(relocated(vault / relative, moves).relative_to(vault).as_posix()
                               for relative in tuple(pending))
                if pending:
                    entry["pending_review"] = sorted(pending)
            atomic_write(conversation_state, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
            state_published = True
        save_config(planned["config"])
    except BaseException:
        if state_published:
            conversation_state.write_bytes(old_state)
        for path in reversed(completed):
            if path.is_file() and path.read_bytes() == writes[path].encode("utf-8"):
                if originals[path] is None:
                    path.unlink()
                else:
                    path.write_bytes(originals[path])
        for old, new in reversed(moved):
            if new.exists() and not old.exists():
                new.rename(old)
        atomic_write(config_path(), old_config)
        raise
    finally:
        lock.unlink(missing_ok=True)
    return {"moved": [{"from": a.relative_to(vault).as_posix(), "to": b.relative_to(vault).as_posix()}
                      for a, b in moves], "files": planned["files"]}


def command(args: Any) -> int:
    config = load_config()
    if not config.get("enabled") or not config.get("vault"):
        raise ValueError("Configure and enable a vault before layout migration")
    planned = plan(config, args.reuse_dir, args.conversations_dir, args.conversation_index)
    if args.apply:
        owner = ""
        if args.review_token:
            from hook import resolve_scope
            scope = resolve_scope({"cwd": str(args.cwd.resolve()),
                                   "session_id": args.session_id or os.environ.get("CODEX_THREAD_ID", "")}, config, planned["vault"])
            owner = scope.owner
        result = apply(planned, args.review_token, owner)
    else:
        result = {"dry_run": True, "moves": [{"from": str(a), "to": str(b)} for a, b in planned["moves"]],
                  "files": planned["files"]}
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0
