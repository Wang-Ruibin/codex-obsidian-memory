"""Explicit per-conversation memory and local title synchronization.

Only opted-in session IDs are queried. Chat transcripts and credentials are never
read. Host metadata is an optional, read-only adapter, not a public Codex API.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import sqlite3
import subprocess
import sys
import time
import unicodedata
from contextlib import closing, contextmanager
from datetime import date
from pathlib import Path
from typing import Any

from local_projects import acquire_lock, local_for_workspace
from memory_core import (atomic_write, codex_home, config_path, frontmatter_value,
                         integration_dir, load_config, path_is_within, redact_secrets,
                         repository_identity, vault_path)


def session_id(value: str | None = None) -> str:
    value = value or os.environ.get("CODEX_THREAD_ID", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}", value):
        raise ValueError("The current Codex conversation ID is unavailable; supply its actual session ID")
    return value


def identity(value: str) -> str:
    return "codex:" + session_id(value)


def state_path() -> Path:
    return integration_dir() / "conversations.json"


def load_state() -> dict[str, Any]:
    path = state_path()
    state = json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"version": 1, "entries": {}}
    if not isinstance(state, dict) or not isinstance(state.get("entries"), dict):
        raise ValueError("Invalid conversation memory registry")
    for key, entry in state["entries"].items():
        session_id(key)
        if (not isinstance(entry, dict) or not isinstance(entry.get("enabled"), bool)
                or not isinstance(entry.get("title"), str) or not isinstance(entry.get("note"), str)
                or not isinstance(entry.get("pending_review", []), list)
                or not isinstance(entry.get("title_sync", True), bool)):
            raise ValueError("Invalid conversation memory registration")
        for relative in [entry["note"], *entry.get("pending_review", [])]:
            if (not isinstance(relative, str) or Path(relative).is_absolute()
                    or ".." in Path(relative).parts or Path(relative).suffix != ".md"):
                raise ValueError("Invalid conversation note or review path")
    return state


def registered(value: str) -> dict[str, Any] | None:
    return load_state()["entries"].get(session_id(value))


def display_title(value: str) -> str:
    value = re.sub(r"\s+", " ", str(value)).strip()
    value = redact_secrets(value)
    return value[:1000]


def markdown_title(value: str) -> str:
    return re.sub(r"([\\`*_{}\[\]()#+.!|])", r"\\\1", html.escape(value, quote=False))


def metadata_title(value: str, home: Path | None = None) -> str:
    """Prefer the displayed name; SQLite's older title can be the first prompt."""
    value = session_id(value)
    home = home or codex_home()
    databases = sorted(home.glob("state_*.sqlite"),
                       key=lambda p: int(re.search(r"state_(\d+)", p.name).group(1))
                       if re.fullmatch(r"state_\d+\.sqlite", p.name) else -1, reverse=True)
    for path in databases:
        if path.is_symlink():
            continue
        try:
            with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=0.2)) as connection:
                connection.execute("PRAGMA query_only=ON")
                columns = {row[1] for row in connection.execute("PRAGMA table_info(threads)")}
                if "name" not in columns or "id" not in columns:
                    continue
                row = connection.execute("SELECT name FROM threads WHERE id=?",
                                         (value,)).fetchone()
                if row and row[0]:
                    return display_title(row[0])
        except (OSError, sqlite3.Error):
            continue
    index = home / "session_index.jsonl"
    latest = ""
    try:
        if index.is_symlink() or index.stat().st_size > 32 * 1024 * 1024:
            return ""
        with index.open(encoding="utf-8") as handle:
            for line in handle:
                if len(line) > 65536:
                    continue
                try:
                    record = json.loads(line)
                    if record.get("id") == value and record.get("thread_name"):
                        latest = display_title(record["thread_name"])
                except (ValueError, AttributeError):
                    continue
    except (OSError, UnicodeError):
        pass
    return latest


def filename(title: str) -> str:
    name = unicodedata.normalize("NFC", title)
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f\x7f\[\]#^]', "-", name).strip(" .")[:100].rstrip(" .")
    # POSIX limits a component by bytes; Windows also accepts this smaller bound.
    name = name.encode("utf-8")[:180].decode("utf-8", errors="ignore").rstrip(" .")
    if not name:
        name = "Conversation"
    if re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", name):
        name = "_" + name
    return name + ".md"


def same_file(first: Path, second: Path) -> bool:
    """Compare file identity, including case-insensitive POSIX filesystems."""
    try:
        return os.path.samefile(first, second)
    except OSError:
        return False


def destination(root: Path, title: str, value: str, old: Path | None = None) -> Path:
    occupied = {unicodedata.normalize("NFC", path.name).casefold(): path for path in root.iterdir()} if root.is_dir() else {}
    target = root / filename(title)
    found = occupied.get(target.name.casefold())
    if found is None and target.exists():
        found = target  # Filesystem aliases must never bypass collision protection.
    if found is not None and (found.is_symlink() or old is None or not same_file(found, old)):
        target = root / (Path(filename(title)).stem + " [" + hashlib.sha256(value.encode()).hexdigest()[:10] + "].md")
        found = occupied.get(target.name.casefold())
        if found is None and target.exists():
            found = target
    if found is not None and (found.is_symlink() or old is None or not same_file(found, old)):
        raise ValueError("The conversation filename is occupied; no file was overwritten")
    return target


def note_path(vault: Path, config: dict[str, Any], entry: dict[str, Any]) -> Path:
    relative = Path(entry["note"])
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".md":
        raise ValueError("Conversation note must be a vault-relative Markdown file")
    path = vault / relative
    directory = vault_path(vault, config, "conversations_dir")
    if path.is_symlink() or not path_is_within(path, directory) or path.resolve() == directory:
        raise ValueError("Conversation note escapes its configured directory")
    return path


def own_text(path: Path, value: str) -> str:
    from reuse_memory import read_header
    header = read_header(path) or ""
    if (frontmatter_value(header, "type") != "conversation"
            or frontmatter_value(header, "conversation_id") != identity(value)):
        raise ValueError("Conversation note has a different identity; no file was overwritten")
    return path.read_text(encoding="utf-8-sig")


@contextmanager
def locked(vault: Path):
    if not vault.is_dir():
        raise ValueError("Configured vault is unavailable; no directory was created")
    state_path().parent.mkdir(parents=True, exist_ok=True)
    state_lock = state_path().with_suffix(".lock")
    fd = acquire_lock(state_lock, "Another conversation memory update is running")
    os.close(fd)
    vault_lock = vault / ".codex-obsidian-memory" / "conversations.lock"
    try:
        if (vault / ".codex-obsidian-memory" / "layout.lock").exists():
            raise ValueError("A vault layout migration is running; retry afterwards")
        if not path_is_within(vault_lock, vault):
            raise ValueError("Conversation lock escapes vault")
        vault_lock.parent.mkdir(parents=True, exist_ok=True)
        fd = acquire_lock(vault_lock, "Another environment is updating conversation notes")
        os.close(fd)
        try:
            yield
        finally:
            vault_lock.unlink(missing_ok=True)
    finally:
        state_lock.unlink(missing_ok=True)


def publish(state: dict[str, Any], writes: dict[Path, str], removed: dict[Path, bytes] | None = None) -> None:
    """Publish metadata last and roll back only files still equal to our writes."""
    removed = removed or {}
    originals = {path: path.read_bytes() if path.exists() else None for path in writes}
    completed, deleted = [], []
    try:
        for path, text in writes.items():
            atomic_write(path, text)
            completed.append(path)
        for path, original in removed.items():
            if path.read_bytes() != original:
                raise ValueError("Conversation note changed while renaming; retry without overwriting it")
            path.unlink()
            deleted.append(path)
        atomic_write(state_path(), json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    except BaseException:
        for path in deleted:
            if not path.exists():
                path.write_bytes(removed[path])
        for path in reversed(completed):
            if path.is_file() and path.read_bytes() == writes[path].encode("utf-8"):
                if originals[path] is None:
                    path.unlink()
                else:
                    path.write_bytes(originals[path])
        raise


def index_text(vault: Path, config: dict[str, Any], state: dict[str, Any]) -> tuple[Path, str]:
    path = vault_path(vault, config, "conversation_index")
    chinese = config.get("locale") == "zh-CN"
    if path.exists():
        text = path.read_text(encoding="utf-8")
    else:
        home = vault_path(vault, config, "home").relative_to(vault).with_suffix("").as_posix()
        text = ("---\ntype: conversation-index\n---\n\n# "
                + ("对话记忆" if chinese else "Conversation memory") + f"\n\n← [[{home}]]\n\n"
                + "<!-- conversations:start -->\n<!-- conversations:end -->\n")
    # Another Codex home can own other entries in the same shared-vault index.
    managed = re.search(r"<!-- conversations:start -->(.*?)<!-- conversations:end -->", text, re.DOTALL)
    rows = []
    if managed:
        for line in managed.group(1).splitlines():
            found = re.search(r"<!-- conversation:codex:([A-Za-z0-9_-]+) -->", line)
            if found and found.group(1) not in state["entries"]:
                rows.append(line)
    # Include retained disabled notes as well; disabling does not erase memory.
    for value, entry in sorted(state["entries"].items()):
        label = html.escape(entry["title"].replace("|", "-").replace("[", "(").replace("]", ")"), quote=False)
        target = Path(entry["note"]).with_suffix("").as_posix()
        rows.append(f"- [[{target}|{label}]] <!-- conversation:{identity(value)} -->")
    block = "<!-- conversations:start -->\n" + "\n".join(rows) + "\n<!-- conversations:end -->"
    if "<!-- conversations:start -->" in text:
        text = re.sub(r"<!-- conversations:start -->.*?<!-- conversations:end -->", lambda _: block,
                      text, flags=re.DOTALL)
    else:
        text += "\n" + block + "\n"
    return path, text


def change_title(value: str, title: str, vault: Path, config: dict[str, Any],
                 state: dict[str, Any]) -> list[str]:
    entry = state["entries"][value]
    old = note_path(vault, config, entry)
    own_text(old, value)
    original = old.read_bytes()
    text = original.decode("utf-8-sig")
    if frontmatter_value(text, "conversation_id") != identity(value):
        raise ValueError("Conversation identity changed during rename")
    root = vault_path(vault, config, "conversations_dir")
    target = destination(root, title, value, old)
    old_relative = old.relative_to(vault).as_posix()
    new_relative = target.relative_to(vault).as_posix()
    text = re.sub(r"(?m)^conversation_title:.*$", lambda _: "conversation_title: " + json.dumps(title, ensure_ascii=False), text)
    text = re.sub(r"(?m)^# .*$", lambda _: "# " + markdown_title(title), text, count=1)
    entry.update(title=title, note=new_relative)
    pending = set(entry.get("pending_review", [])) | {old_relative, new_relative}
    entry["pending_review"] = sorted(pending)
    index, body = index_text(vault, config, state)
    writes = {target: text, index: body}
    entry["pending_review"].append(index.relative_to(vault).as_posix())
    removed = {old: original} if old_relative != new_relative else {}
    if old_relative != new_relative and same_file(old, target):
        # Case-only renames on Windows and default macOS filesystems need a temporary name.
        temporary = old.with_name(".case-" + hashlib.sha256(value.encode()).hexdigest() + ".tmp")
        if temporary.exists():
            raise ValueError("An interrupted case rename needs recovery before continuing")
        old.rename(temporary)
        try:
            temporary.rename(target)
            publish(state, writes)
        except BaseException:
            if target.exists():
                target.rename(temporary)
            temporary.rename(old)
            raise
    else:
        publish(state, writes, removed)
    return entry["pending_review"]


def sync_titles(config: dict[str, Any] | None = None, *, only: str | None = None) -> list[str]:
    config = config or load_config()
    if not config.get("enabled") or not config.get("vault") or not state_path().is_file():
        return []
    vault = Path(config["vault"]).resolve()
    changed = []
    with locked(vault):
        state = load_state()
        for value, entry in state["entries"].items():
            if not entry.get("title_sync", True) or (only and value != only):
                continue
            title = metadata_title(value)
            if title and title != entry["title"]:
                changed.extend(change_title(value, title, vault, config, state))
    return sorted(set(changed))


def clear_review(value: str, expected: list[str] | None = None) -> bool:
    config = load_config()
    with locked(Path(config["vault"]).resolve()):
        state = load_state()
        entry = state["entries"].get(value)
        if entry:
            if expected is not None and set(entry.get("pending_review", [])) != set(expected):
                return False
            entry.pop("pending_review", None)
            publish(state, {})
        return True


def command(args: Any) -> int:
    config = load_config()
    if not config.get("enabled") or not config.get("vault"):
        raise ValueError("Configure and enable a memory vault first")
    vault = Path(config["vault"]).resolve()
    if args.command == "conversation-list":
        print(json.dumps(load_state(), ensure_ascii=True, indent=2))
        return 0
    if args.command == "conversation-sync":
        print(json.dumps({"changed_notes": sync_titles(config)}, ensure_ascii=True))
        return 0
    value = session_id(args.session_id)
    if args.command == "conversation-enable":
        repository, _ = repository_identity(args.cwd.resolve())
        if repository:
            raise ValueError("This workspace has a GitHub repository; use its project memory")
        if local_for_workspace(args.cwd.resolve(), config) is not None:
            raise ValueError("This workspace has registered local project memory; its existing route is retained")
        title = metadata_title(value) or display_title(args.title or "")
        if not title:
            raise ValueError("The conversation title is unavailable; resolve its actual title and pass --title")
    with locked(vault):
        state = load_state()
        entry = state["entries"].get(value)
        if args.command == "conversation-disable":
            if not entry:
                raise ValueError("This conversation has no memory registration")
            entry["enabled"] = False
            entry["title_sync"] = not getattr(args, "freeze_title", False)
            publish(state, {})
            print(json.dumps({"conversation_id": identity(value), "enabled": False,
                              "title_sync": entry["title_sync"], "notes_retained": True}))
            return 0
        if entry:
            own_text(note_path(vault, config, entry), value)
            entry["enabled"] = True
            entry["title_sync"] = True
            publish(state, {})
            if title != entry["title"]:
                change_title(value, title, vault, config, state)
        else:
            root = vault_path(vault, config, "conversations_dir")
            from reuse_memory import read_header
            existing = [path for path in root.glob("*.md") if not path.is_symlink()
                        and frontmatter_value(read_header(path) or "", "conversation_id") == identity(value)]
            if len(existing) > 1:
                raise ValueError("Several notes claim this conversation ID; resolve the duplicate first")
            if existing:
                target = existing[0]
                entry = {"enabled": True, "title_sync": True, "title": title, "note": target.relative_to(vault).as_posix()}
                state["entries"][value] = entry
                publish(state, {})
                change_title(value, title, vault, config, state)
            else:
                target = destination(root, title, value)
                create_note(value, title, target, vault, config, state)
            entry = state["entries"][value]
    from memory_context import build_context, resolve_scope
    context = build_context(resolve_scope({"cwd": str(args.cwd), "session_id": value}, config, vault), config, vault)
    warning = ""
    try:
        ensure_watcher(force=True)
    except OSError:
        warning = "Memory is enabled, but its automatic title watcher could not start. Retry conversation-sync."
    print(json.dumps({"conversation_id": identity(value), "enabled": True, "note": entry["note"],
                      "changed_notes": entry.get("pending_review", []), "context": context,
                      **({"warning": warning} if warning else {})}, ensure_ascii=True))
    return 0


def create_note(value: str, title: str, target: Path, vault: Path, config: dict[str, Any], state: dict[str, Any]) -> None:
    entry = {"enabled": True, "title_sync": True, "title": title, "note": target.relative_to(vault).as_posix(),
             "pending_review": [target.relative_to(vault).as_posix()]}
    state["entries"][value] = entry
    index, index_body = index_text(vault, config, state)
    entry["pending_review"].append(index.relative_to(vault).as_posix())
    index_link = index.relative_to(vault).with_suffix("").as_posix()
    headings = (["目标与约束", "已确认背景", "关键决定", "已验证结果", "下一步", "开放问题"]
                if config.get("locale") == "zh-CN" else
                ["Goals and constraints", "Confirmed context", "Decisions", "Verified outcomes", "Next steps", "Open questions"])
    note = (f"---\ntype: conversation\nconversation_id: {identity(value)}\n"
            f"conversation_title: {json.dumps(title, ensure_ascii=False)}\nupdated: {date.today().isoformat()}\n---\n\n"
            f"# {markdown_title(title)}\n\n← [[{index_link}]]\n\n" + "\n\n".join("## " + h for h in headings) + "\n")
    home = vault_path(vault, config, "home")
    writes = {target: note, index: index_body}
    if home.is_file() and f"[[{index_link}" not in home.read_text(encoding="utf-8"):
        writes[home] = home.read_text(encoding="utf-8") + f"\n- [[{index_link}]]\n"
        entry["pending_review"].append(home.relative_to(vault).as_posix())
    publish(state, writes)


def ensure_watcher(*, force: bool = False) -> None:
    if load_config().get("integration_mode") == "skill":
        return  # Standalone Skills synchronize explicitly; never start a worker.
    if os.environ.get("CODEX_OBSIDIAN_NO_WATCHER") == "1" or not any(e.get("title_sync", True) for e in load_state()["entries"].values()):
        return
    marker = integration_dir() / "conversation-watcher.lock"
    if not force and marker.exists() and time.time() - marker.stat().st_mtime < 20:
        return
    executable = Path(sys.executable)
    if os.name == "nt" and executable.with_name("pythonw.exe").is_file():
        executable = executable.with_name("pythonw.exe")
    options = {"creationflags": subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS} if os.name == "nt" else {"start_new_session": True}
    subprocess.Popen([str(executable), "-X", "utf8", "-B", str(Path(__file__).with_name("conversation_watcher.py")),
                      "--config", str(config_path())], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, close_fds=True, **options)
