"""Explicit local registrations. Project files and Git configuration are never written."""
from __future__ import annotations

import json
import os
import re
import time
import uuid
from datetime import date
from pathlib import Path
from typing import Any

from memory_core import (
    atomic_write, config_path, frontmatter_value, git_value, load_config,
    find_project_page, note_identity, path_is_within, record_registered_index,
    repository_allowed, repository_identity, review_payload_for_token, vault_path,
)


def local_registry(config: dict[str, Any]) -> list[dict[str, Any]]:
    entries = config.get("local_projects", [])
    if not isinstance(entries, list):
        raise ValueError("local_projects must be a list")
    ids, roots = set(), set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Invalid local project registration")
        identity, root = entry.get("project_id", ""), entry.get("root", "")
        if (not isinstance(identity, str) or not re.fullmatch(r"local:[0-9a-f]{32}", identity)
                or not isinstance(root, str) or not Path(root).is_absolute()
                or not isinstance(entry.get("enabled"), bool)
                or not isinstance(entry.get("name"), str)
                or not isinstance(entry.get("project_home"), str)):
            raise ValueError("Invalid local project identity, root, name, state or home")
        pending = entry.get("pending_review", [])
        if not isinstance(pending, list) or not all(isinstance(path, str) for path in pending):
            raise ValueError("Invalid local project review receipt")
        canonical = os.path.normcase(str(Path(root).resolve()))
        if identity in ids or canonical in roots:
            raise ValueError("Duplicate local project identity or root")
        ids.add(identity)
        roots.add(canonical)
    return entries


def registered_project(config: dict[str, Any], identity: str) -> dict[str, Any] | None:
    return next((entry for entry in local_registry(config) if entry["project_id"] == identity), None)


def local_home_path(vault: Path, config: dict[str, Any], entry: dict[str, Any]) -> Path:
    relative = Path(entry["project_home"])
    if relative.is_absolute() or ".." in relative.parts or relative.suffix != ".md":
        raise ValueError("Local project home must be a vault-relative Markdown path")
    target = (vault / relative).resolve()
    if not path_is_within(target, vault_path(vault, config, "projects_dir")):
        raise ValueError("Local project home must stay in projects_dir")
    return target


def find_local_home(vault: Path, config: dict[str, Any], entry: dict[str, Any]) -> Path | None:
    target = local_home_path(vault, config, entry)
    if not target.is_file():
        return None
    text = target.read_text(encoding="utf-8-sig")
    if frontmatter_value(text, "type") != "project" or note_identity(text) != entry["project_id"]:
        raise ValueError("Registered local project home has a different identity")
    return target


def local_for_workspace(cwd: Path, config: dict[str, Any]) -> dict[str, Any] | None:
    candidates = [entry for entry in local_registry(config) if path_is_within(cwd, Path(entry["root"]))]
    if not candidates:
        return None
    entry = max(candidates, key=lambda value: len(Path(value["root"]).resolve().parts))
    top = git_value(cwd, "rev-parse", "--show-toplevel")
    root = Path(entry["root"]).resolve()
    # Do not let a parent folder registration capture an independent nested repository.
    if top and Path(top).resolve() != root and path_is_within(Path(top), root):
        return None
    return entry  # A disabled nearest registration blocks fallback to its parent.


def local_source_allowed(entry: dict[str, Any], config: dict[str, Any]) -> bool:
    if not entry["enabled"]:
        return False
    repository, _ = repository_identity(Path(entry["root"]))
    return repository.casefold() not in {
        str(value).casefold() for value in config.get("excluded_repositories", [])
    }


def checked_root(path: Path, vault: Path, config: dict[str, Any]) -> Path:
    root = path.expanduser().resolve(strict=True)
    if not root.is_dir() or root == Path(root.anchor) or root == Path.home().resolve():
        raise ValueError("Select a specific existing project directory, not a drive or user home")
    if path_is_within(root, vault) or path_is_within(vault, root):
        raise ValueError("A local project must not contain or be inside the memory vault")
    repository, _ = repository_identity(root)
    if repository.casefold() in {str(value).casefold() for value in config.get("excluded_repositories", [])}:
        raise ValueError("This repository is explicitly excluded; local registration cannot bypass it")
    return root


def home_text(name: str, identity: str, index: str, chinese: bool) -> str:
    headings = (["项目目标与约束", "稳定背景", "开发分支", "已验证结果", "下一步", "开放问题"]
                if chinese else ["Goal and constraints", "Stable context", "Development branches",
                                 "Verified results", "Next steps", "Open questions"])
    return (f"---\ntype: project\nsource_kind: local\nproject_id: {identity}\nstatus: active\n"
            f"updated: {date.today().isoformat()}\n---\n\n# {name}\n\n← [[{index}]]\n\n"
            + "\n\n".join(f"## {heading}" for heading in headings) + "\n")


def commit_registration(config: dict[str, Any], writes: dict[Path, str]) -> None:
    """Publish config last. Roll back only our own note writes if publication fails."""
    originals = {path: path.read_text(encoding="utf-8") if path.exists() else None for path in writes}
    completed = []
    try:
        for path, text in writes.items():
            atomic_write(path, text)
            completed.append(path)
        atomic_write(config_path(), json.dumps(config, ensure_ascii=False, indent=2) + "\n")
    except BaseException:
        for path in reversed(completed):
            if path.read_text(encoding="utf-8") != writes[path]:
                continue  # Preserve another writer's newer edit.
            if originals[path] is None:
                path.unlink()
            else:
                atomic_write(path, originals[path])
        raise


def commit_notes_only(writes: dict[Path, str]) -> None:
    originals = {path: path.read_text(encoding="utf-8") if path.is_file() else None for path in writes}
    completed = []
    try:
        for path, text in writes.items():
            atomic_write(path, text)
            completed.append(path)
    except BaseException:
        for path in reversed(completed):
            if not path.is_file() or path.read_text(encoding="utf-8") != writes[path]:
                continue
            if originals[path] is None:
                path.unlink()
            else:
                atomic_write(path, originals[path])
        raise


def command_local(args: Any) -> int:
    # Serialize registration updates; normal Hooks and reads never create this lock.
    if not config_path().is_file():
        raise ValueError("Initialize a vault first; use init --local-only if you do not use GitHub")
    lock = config_path().with_suffix(".local-projects.lock")
    descriptor = acquire_lock(lock, "A local registration update is already running")
    try:
        os.close(descriptor)
        return update_local(args)
    finally:
        lock.unlink(missing_ok=True)


def acquire_lock(path: Path, busy_message: str, wait_seconds: float = 10) -> int:
    deadline = time.monotonic() + wait_seconds
    while True:
        try:
            return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise ValueError(busy_message + "; retry after it finishes") from None
            time.sleep(0.05)


def clear_local_review(identity: str) -> None:
    lock = config_path().with_suffix(".local-projects.lock")
    try:
        fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return  # Keep the receipt for the next review; do not overwrite another updater.
    try:
        os.close(fd)
        config = load_config()
        entry = registered_project(config, identity)
        if entry and entry.get("pending_review"):
            entry.pop("pending_review")
            commit_registration(config, {})
    finally:
        lock.unlink(missing_ok=True)


def update_local(args: Any) -> int:
    config = load_config()
    if not config.get("enabled") or not config.get("vault"):
        raise ValueError("Memory is disabled or not configured; enable it before registering projects")
    vault = Path(config["vault"]).resolve()
    if not vault.is_dir():
        raise ValueError("Configured vault is unavailable")
    lock_dir = vault / ".codex-obsidian-memory"
    if not path_is_within(lock_dir, vault):
        raise ValueError("Vault registration lock directory escapes the vault")
    lock_dir.mkdir(parents=True, exist_ok=True)
    shared_lock = lock_dir / "registration.lock"
    descriptor = acquire_lock(shared_lock, "Another environment is updating this vault's project index")
    try:
        os.close(descriptor)
        return update_local_locked(args, config, vault)
    finally:
        shared_lock.unlink(missing_ok=True)


def update_local_locked(args: Any, config: dict[str, Any], vault: Path) -> int:
    entries = local_registry(config)
    config["local_projects"] = entries
    writes: dict[Path, str] = {}
    if args.command == "local-register":
        root = checked_root(args.path, vault, config)
        exact = next((entry for entry in entries if Path(entry["root"]).resolve() == root), None)
        if exact and args.project_id and exact["project_id"] != args.project_id:
            raise ValueError("This path is already registered to another project")
        entry = exact
        if args.project_id and entry is None:
            if not re.fullmatch(r"local:[0-9a-f]{32}", args.project_id):
                raise ValueError("Use the exact local project ID returned by local-list")
            if registered_project(config, args.project_id):
                raise ValueError("This project has another path; use local-move")
            # Explicit attachment from another environment using the same vault.
            matches = []
            for candidate in vault_path(vault, config, "projects_dir").rglob("*.md"):
                if not path_is_within(candidate, vault) or candidate.is_symlink():
                    continue
                text = candidate.read_text(encoding="utf-8-sig")
                if frontmatter_value(text, "type") == "project" and note_identity(text) == args.project_id:
                    matches.append(candidate)
            if len(matches) != 1:
                raise ValueError("The requested local ID must have one existing project home in this vault")
            entry = {"project_id": args.project_id, "project_home": matches[0].relative_to(vault).as_posix(),
                     "root": str(root), "name": args.name or root.name, "enabled": True}
            entries.append(entry)
        if entry is None:
            # Avoid creating two homes for an already indexed GitHub project.
            from memory_core import find_project_page
            repository, _ = repository_identity(root)
            if repository and find_project_page(vault, config, repository):
                raise ValueError("This GitHub project already has a memory home; keep its existing identity")
            identity = "local:" + uuid.uuid4().hex
            folder = vault_path(vault, config, "projects_dir") / identity.replace(":", "-")
            entry = {"project_id": identity, "project_home": (folder / "project.md").relative_to(vault).as_posix(),
                     "root": str(root), "name": args.name or root.name, "enabled": True}
            entries.append(entry)
        entry["enabled"] = True
        name = str(entry["name"])
        if not name.strip() or len(name) > 120 or re.search(r"[\r\n\[\]|\x00]", name):
            raise ValueError("Use a short single-line project name without Wiki-link delimiters")
        page = local_home_path(vault, config, entry)
        index_path = vault_path(vault, config, "project_index")
        if not index_path.is_file():
            raise ValueError("The configured project index is missing; validate the vault before registration")
        if page.exists():
            find_local_home(vault, config, entry)
        else:
            index = index_path.relative_to(vault).with_suffix("").as_posix()
            writes[page] = home_text(name, entry["project_id"], index, config.get("locale") == "zh-CN")
        index_text = index_path.read_text(encoding="utf-8")
        target = page.relative_to(vault).with_suffix("").as_posix()
        links = re.findall(r"\[\[([^|\]#]+)", re.sub(r"```.*?```", "", index_text, flags=re.DOTALL))
        if target not in links:
            writes[index_path] = index_text.rstrip() + f"\n\n- [[{target}|{name}]]\n"
    else:
        entry = registered_project(config, args.project_id)
        if entry is None:
            raise ValueError("Local project ID is not registered in this environment")
        if args.command == "local-move":
            root = checked_root(args.path, vault, config)
            if any(other is not entry and Path(other["root"]).resolve() == root for other in entries):
                raise ValueError("The destination is already registered to another local project")
            entry["root"] = str(root)
        else:
            entry["enabled"] = args.command == "local-enable"
            if entry["enabled"]:
                checked_root(Path(entry["root"]), vault, config)
    local_registry(config)
    if writes:
        entry["pending_review"] = sorted(set(entry.get("pending_review", [])) | {
            path.relative_to(vault).as_posix() for path in writes
        })
    commit_registration(config, writes)
    result = {"project": entry, "changed_notes": [path.relative_to(vault).as_posix() for path in writes],
              "note": ("Effective now in this conversation. Use the returned context immediately and review memory at this task's end."
                       if entry["enabled"] else "Local memory is disabled. Existing notes and project identity are retained.")}
    if args.command in {"local-register", "local-enable", "local-move"} and entry["enabled"]:
        from hook import build_context, resolve_scope
        scope = resolve_scope({"cwd": entry["root"]}, config, vault)
        result["context"] = build_context(scope, config, vault) if scope.eligible else ""
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


def command_register_github(args: Any) -> int:
    """Register one eligible GitHub home and its index link under the shared vault lock."""
    config = load_config()
    vault_text = str(config.get("vault") or "")
    if not config.get("enabled") or not vault_text:
        raise ValueError("Memory is disabled or not configured")
    vault = Path(vault_text).resolve()
    root = args.cwd.resolve(strict=True)
    if not root.is_dir() or path_is_within(root, vault) or path_is_within(vault, root):
        raise ValueError("Select an existing project outside the memory vault")
    repository, _ = repository_identity(root)
    if not repository or not repository_allowed(repository, config, indexed=False):
        raise ValueError("This workspace is not an eligible GitHub repository")
    if local_for_workspace(root, config) is not None:
        raise ValueError("This workspace already has an explicit local project identity")
    owner_identity = repository.casefold()
    review_payload_for_token(args.review_token, owner_identity, vault)
    project_dir = vault_path(vault, config, "projects_dir")
    index_path = vault_path(vault, config, "project_index")
    if not index_path.is_file():
        raise ValueError("Configured project index is missing")
    lock_dir = vault / ".codex-obsidian-memory"
    if not path_is_within(lock_dir, vault):
        raise ValueError("Vault registration lock directory escapes the vault")
    lock_dir.mkdir(parents=True, exist_ok=True)
    lock = lock_dir / "registration.lock"
    descriptor = acquire_lock(lock, "Another environment is updating this vault's project index")
    try:
        os.close(descriptor)
        home = find_project_page(vault, config, repository)
        changed = []
        writes: dict[Path, str] = {}
        name = repository.split("/", 1)[1]
        if home is None:
            owner = repository.split("/", 1)[0]
            folder = project_dir / name
            if folder.exists():
                folder = project_dir / f"{owner}-{name}"
            if folder.exists():
                folder = project_dir / f"{owner}-{name}-{uuid.uuid4().hex[:8]}"
            home = folder / f"{name}.md"
            index_name = index_path.relative_to(vault).with_suffix("").as_posix()
            headings = (["项目目标与约束", "稳定背景", "开发分支", "仓库级关键决策", "开放问题"]
                        if config.get("locale") == "zh-CN" else
                        ["Goal and constraints", "Stable context", "Development branches",
                         "Repository-level decisions", "Open questions"])
            body = (f"---\ntype: project\nstatus: tracked\nupdated: {date.today().isoformat()}\n"
                    f"github_repo: {repository}\nsource_kind: owned\n---\n\n# {name}\n\n"
                    f"← [[{index_name}]]\n\n" + "\n\n".join(f"## {heading}" for heading in headings) + "\n")
            writes[home] = body
            changed.append(home.relative_to(vault).as_posix())
        old_index = index_path.read_text(encoding="utf-8")
        link = home.relative_to(vault).with_suffix("").as_posix()
        existing_links = re.findall(r"\[\[([^|\]#]+)", re.sub(r"```.*?```", "", old_index, flags=re.DOTALL))
        if link not in existing_links:
            writes[index_path] = old_index.rstrip() + f"\n\n- [[{link}|{name}]]\n"
            changed.append(index_path.relative_to(vault).as_posix())
        commit_notes_only(writes)
        if index_path in writes:
            record_registered_index(args.review_token, owner_identity, vault, index_path)
        from hook import build_context, resolve_scope
        scope = resolve_scope({"cwd": str(root)}, config, vault)
        result = {"repository": repository, "project_home": home.relative_to(vault).as_posix(),
                  "changed_notes": changed, "context": build_context(scope, config, vault)}
        print(json.dumps(result, ensure_ascii=True, indent=2))
        return 0
    finally:
        lock.unlink(missing_ok=True)
