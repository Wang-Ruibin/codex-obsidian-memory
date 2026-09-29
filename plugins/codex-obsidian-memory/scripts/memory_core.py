from __future__ import annotations

import json
import hashlib
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CONFIG_VERSION = 1
REVIEW_MARKER = "<!-- obsidian-memory-reviewed -->"
WRITEBACK_DISCLOSURE_MARKER = "<!-- obsidian-memory-writeback-disclosed -->"
DEFAULT_PATHS = {
    "home": "00-memory-home.md",
    "global_memory": "10-memory/global-memory.md",
    "maintenance": "10-memory/maintenance.md",
    "template": "10-memory/project-template.md",
    "project_index": "20-projects/project-index.md",
    "projects_dir": "20-projects",
    "weekly_brief": "10-memory/weekly-brief.md",
    "monthly_audit": "10-memory/monthly-audit.md",
    "reuse_dir": "10-memory/reusable",
    "reuse_index": "10-memory/reusable/index.md",
    "reuse_template": "10-memory/reusable/template.md",
}


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or (Path.home() / ".codex")).resolve()


def integration_dir() -> Path:
    return config_path().parent


def config_path() -> Path:
    override = os.environ.get("CODEX_OBSIDIAN_MEMORY_CONFIG")
    return (
        Path(override).resolve()
        if override
        else codex_home() / "obsidian-memory" / "config.json"
    )


def load_config() -> dict[str, Any]:
    path = config_path()
    if not path.is_file():
        return {"version": CONFIG_VERSION, "enabled": False, "paths": dict(DEFAULT_PATHS)}
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    paths = dict(DEFAULT_PATHS)
    paths.update(document.get("paths") or {})
    document["paths"] = paths
    document.setdefault("locale", "en")
    return document


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def save_config(config: dict[str, Any]) -> None:
    config["version"] = CONFIG_VERSION
    atomic_write(config_path(), json.dumps(config, ensure_ascii=False, indent=2) + "\n")


def redact_secrets(text: str, *, preserve_lines: bool = False) -> str:
    patterns = (
        (r"sk-[A-Za-z0-9_-]{16,}", "[REDACTED_SECRET]"),
        (r"gh[pousr]_[A-Za-z0-9]{20,}", "[REDACTED_SECRET]"),
        (r"github_pat_[A-Za-z0-9_]{20,}", "[REDACTED_SECRET]"),
        (r"Bearer\s+[A-Za-z0-9._~+/-]{20,}", "Bearer [REDACTED_SECRET]"),
        (
            r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
            "[REDACTED_PRIVATE_KEY]",
        ),
    )
    result = text
    for pattern, replacement in patterns:
        result = re.sub(
            pattern,
            lambda match: replacement + ("\n" * match.group().count("\n") if preserve_lines else ""),
            result,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return result


def git_value(cwd: Path, *args: str) -> str:
    try:
        completed = subprocess.run(
            ["git", "-C", str(cwd), *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return completed.stdout.strip() if completed.returncode == 0 else ""


def github_repository_from_origin(origin: str) -> str:
    value = origin.strip()
    if not value:
        return ""
    scp_match = re.fullmatch(
        r"(?:git@)?github\.com:(?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?/?",
        value,
        flags=re.IGNORECASE,
    )
    if scp_match:
        owner = scp_match.group("owner")
        repository = scp_match.group("repo")
    elif "://" in value:
        parsed = urlparse(value)
        if (parsed.hostname or "").casefold() != "github.com":
            return ""
        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) != 2:
            return ""
        owner, repository = parts
    else:
        return ""
    repository = re.sub(r"\.git$", "", repository, flags=re.IGNORECASE)
    return f"{owner}/{repository}" if owner and repository else ""


def repository_identity(cwd: Path) -> tuple[str, str]:
    origin = git_value(cwd, "config", "--get", "remote.origin.url")
    branch = git_value(cwd, "branch", "--show-current")
    return github_repository_from_origin(origin), branch


def normalized_repository(value: str) -> str:
    candidate = re.sub(r"\.git$", "", value.strip().strip("/"), flags=re.IGNORECASE)
    if not re.fullmatch(r"[^/\s]+/[^/\s]+", candidate):
        raise ValueError(f"Expected OWNER/REPO, got: {value}")
    return candidate


def path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except (OSError, RuntimeError, ValueError):
        return False


def vault_path(vault: Path, config: dict[str, Any], key: str) -> Path:
    relative = Path(str({**DEFAULT_PATHS, **(config.get("paths") or {})}[key]))
    if relative.is_absolute():
        raise ValueError(f"Vault path must be relative: {key}")
    resolved = (vault / relative).resolve()
    if not path_is_within(resolved, vault):
        raise ValueError(f"Vault path escapes root: {key}")
    return resolved


def validated_paths(overrides: dict[str, str] | None = None) -> dict[str, str]:
    paths = dict(DEFAULT_PATHS)
    paths.update(overrides or {})
    unknown = sorted(set(paths) - set(DEFAULT_PATHS))
    if unknown:
        raise ValueError(f"Unknown vault path keys: {', '.join(unknown)}")
    for key, value in paths.items():
        relative = Path(str(value))
        if relative.is_absolute() or relative.anchor or ".." in relative.parts or not str(value).strip():
            raise ValueError(f"Vault path must be a non-empty relative path: {key}")
    return paths


def frontmatter_value(text: str, key: str) -> str:
    frontmatter = re.match(r"\A\ufeff?---\s*\r?\n(?P<body>.*?)\r?\n---(?:\r?\n|\Z)", text, re.DOTALL)
    if not frontmatter:
        return ""
    match = re.search(
        rf"(?m)^{re.escape(key)}:[\t ]*['\"]?([^'\"\r\n]*)", frontmatter.group("body")
    )
    return match.group(1).strip() if match else ""


def repository_allowed(repository: str, config: dict[str, Any], *, indexed: bool) -> bool:
    """Share the same exact repository scope between hooks and reference retrieval."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        return False
    key = repository.casefold()
    if key in {str(value).casefold() for value in config.get("excluded_repositories", [])}:
        return False
    if config.get("scope_mode") == "local-only":
        return False
    if key in {str(value).casefold() for value in config.get("included_repositories", [])}:
        return True
    mode = config.get("scope_mode", "github-owner")
    if mode == "indexed-only":
        return indexed
    return mode == "github-owner" and key.split("/", 1)[0] in {
        str(value).casefold() for value in config.get("github_owners", [])
    }


def note_identity(text: str) -> str:
    """A note has exactly one identity; never infer it from body text or filenames."""
    local = frontmatter_value(text, "project_id")
    repository = frontmatter_value(text, "github_repo")
    if local:
        return local if re.fullmatch(r"local:[0-9a-f]{32}", local) and not repository else ""
    if re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        return repository.casefold()
    return ""


def find_project_page(vault: Path, config: dict[str, Any], repository: str) -> Path | None:
    projects_dir = vault_path(vault, config, "projects_dir")
    if not repository or not projects_dir.is_dir():
        return None
    for candidate in sorted(projects_dir.rglob("*.md"), key=lambda path: str(path).casefold()):
        if not path_is_within(candidate, projects_dir):
            continue
        try:
            note = candidate.read_text(encoding="utf-8")
        except OSError:
            continue
        if frontmatter_value(note, "type").casefold() != "project":
            continue
        if note_identity(note) == repository.casefold():
            return candidate
    return None


def branch_slug(branch: str) -> str:
    slug = re.sub(r"[<>:\"/\\|?*]+", "--", branch.strip())
    slug = re.sub(r"-+", "-", slug).strip(" .-")
    return slug or "detached-head"


def markdown_snapshot(vault: Path, *, roots: tuple[Path, ...] | None = None,
                      files: tuple[Path, ...] = ()) -> dict[str, str]:
    vault = vault.resolve()
    resolved_roots = tuple(root.resolve() for root in roots) if roots is not None else None
    resolved_files = {path.resolve() for path in files}
    snapshot: dict[str, str] = {}
    for candidate in sorted(vault.rglob("*.md"), key=lambda path: str(path).casefold()):
        try:
            relative = candidate.relative_to(vault)
            if any(part.startswith(".") for part in relative.parts):
                continue
            resolved = candidate.resolve(strict=True)
            resolved.relative_to(vault)
            if not resolved.is_file():
                continue
            if resolved_roots is not None and not (
                    any(path_is_within(resolved, root) for root in resolved_roots)
                    or resolved in resolved_files):
                continue
            digest = hashlib.sha256(resolved.read_bytes()).hexdigest()
        except (OSError, RuntimeError, ValueError):
            continue
        snapshot[relative.as_posix()] = digest
    return snapshot


def review_snapshot_path(event: dict[str, Any]) -> Path | None:
    session_id = str(event.get("session_id") or "").strip()
    turn_id = str(event.get("turn_id") or "").strip()
    if not session_id or not turn_id:
        return None
    digest = hashlib.sha256(f"{session_id}\0{turn_id}".encode("utf-8")).hexdigest()
    return integration_dir() / "writeback-reviews" / f"{digest}.json"


def cleanup_review_snapshots(vault: Path | None = None, max_age_seconds: int = 7 * 24 * 60 * 60) -> None:
    directory = integration_dir() / "writeback-reviews"
    if not directory.is_dir():
        return
    cutoff = time.time() - max_age_seconds
    for candidate in directory.glob("*.json"):
        try:
            if candidate.stat().st_mtime < cutoff:
                candidate.unlink()
        except OSError:
            continue
    claims_dir = vault / ".codex-obsidian-memory" / "claims" if vault else None
    if claims_dir and claims_dir.is_dir() and path_is_within(claims_dir, vault):
        for candidate in claims_dir.glob("*.json"):
            try:
                if candidate.stat().st_mtime < cutoff:
                    candidate.unlink()
            except OSError:
                continue


def save_review_snapshot(event: dict[str, Any], vault: Path, *, project_root: Path | None = None,
                         owner: str = "") -> None:
    path = review_snapshot_path(event)
    if path is None or path.exists():
        return
    cleanup_review_snapshots(vault)
    restricted = bool(owner)
    payload = {
        "vault": str(vault.resolve()),
        "owner": owner,
        "project_root": str(project_root.resolve()) if project_root else "",
        "registered_index": "",
        "claimed_files": {},
        "files": markdown_snapshot(vault, roots=((project_root,) if project_root else ()) if restricted else None),
        "created_at": time.time(),
    }
    atomic_write(path, json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def review_changes(event: dict[str, Any], vault: Path, *, project_root: Path | None = None,
                   owner: str = "") -> list[tuple[str, str]]:
    path = review_snapshot_path(event)
    if path is None or not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, json.JSONDecodeError):
        return []
    if str(payload.get("vault") or "") != str(vault.resolve()):
        return []
    recorded_owner = str(payload.get("owner") or "")
    if recorded_owner and recorded_owner != owner:
        raise ValueError("Project identity changed during this task; review its memory in the correct workspace")
    recorded_root = str(payload.get("project_root") or "")
    if recorded_root and project_root and Path(recorded_root) != project_root.resolve():
        raise ValueError("Project home changed during this task; review its memory in the correct workspace")
    scoped = bool(owner)
    extra_paths = []
    claims = {str(key): value for key, value in (payload.get("claimed_files") or {}).items()}
    for relative in claims:
        extra_paths.append(vault / relative)
    roots = ((project_root,) if project_root else ()) if scoped else None
    allowed_paths = tuple(extra_paths)
    before = {str(key): str(value) for key, value in (payload.get("files") or {}).items()}
    before.update({relative: digest for relative, digest in claims.items() if isinstance(digest, str)})
    if scoped:
        allowed = {path.resolve().relative_to(vault.resolve()).as_posix() for path in allowed_paths}
        before = {relative: digest for relative, digest in before.items()
                  if relative in allowed or (project_root and path_is_within(vault / relative, project_root))}
    after = markdown_snapshot(vault, roots=roots, files=allowed_paths)
    changes: list[tuple[str, str]] = []
    for relative in sorted(set(before) | set(after), key=str.casefold):
        if relative not in before:
            changes.append(("created", relative))
        elif relative not in after:
            changes.append(("deleted", relative))
        elif before[relative] != after[relative]:
            changes.append(("modified", relative))
    registered_index = str(payload.get("registered_index") or "") if scoped else ""
    if registered_index and not any(relative == registered_index for _, relative in changes):
        changes.append(("modified", registered_index))
    return changes


def review_payload_for_token(token: str, owner: str, vault: Path) -> tuple[Path, dict[str, Any]]:
    if not re.fullmatch(r"[0-9a-f]{64}", token):
        raise ValueError("Use the current turn's exact review token")
    snapshot = integration_dir() / "writeback-reviews" / f"{token}.json"
    if not snapshot.is_file():
        raise ValueError("The current turn has no review snapshot")
    payload = json.loads(snapshot.read_text(encoding="utf-8-sig"))
    if payload.get("owner") != owner or payload.get("vault") != str(vault.resolve()):
        raise ValueError("Review token does not belong to this project and vault")
    return snapshot, payload


def record_registered_index(token: str, owner: str, vault: Path, index: Path) -> None:
    snapshot, payload = review_payload_for_token(token, owner, vault)
    payload["registered_index"] = index.resolve().relative_to(vault.resolve()).as_posix()
    atomic_write(snapshot, json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")


def claim_shared_file(token: str, owner: str, relative: str, vault: Path,
                      config: dict[str, Any]) -> str:
    """Reserve a shared note for one turn before writing; never store its body."""
    snapshot, payload = review_payload_for_token(token, owner, vault)
    if not relative or relative.startswith(".") or "\\" in relative:
        raise ValueError("Use a vault-relative Markdown path")
    candidate = Path(relative)
    if (candidate.is_absolute() or ".." in candidate.parts or candidate.suffix != ".md"
            or any(part.startswith(".") for part in candidate.parts)):
        raise ValueError("Shared note path is invalid")
    target = (vault / candidate).resolve()
    global_note = vault_path(vault, config, "global_memory")
    reusable = vault_path(vault, config, "reuse_dir")
    if target != global_note and not path_is_within(target, reusable):
        raise ValueError("Only the global-memory note or a shared lesson can be claimed")
    if (vault / candidate).is_symlink() or not path_is_within(target, vault):
        raise ValueError("Shared note path escapes the vault")
    relative = target.relative_to(vault.resolve()).as_posix()
    # Windows and WSL attached to one vault must see the same lease.
    claims_dir = vault / ".codex-obsidian-memory" / "claims"
    if not path_is_within(claims_dir, vault):
        raise ValueError("Shared reservation directory escapes the vault")
    claims_dir.mkdir(parents=True, exist_ok=True)
    lease = claims_dir / f"{hashlib.sha256(relative.encode('utf-8')).hexdigest()}.json"
    claim = {"token": token, "owner": owner, "path": relative}
    new_lease = False
    try:
        descriptor = os.open(lease, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        try:
            current = json.loads(lease.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            raise ValueError("This shared note is being reserved; retry shortly") from None
        if current != claim:
            raise ValueError("This shared note is reserved by another active conversation") from None
    else:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(claim, handle)
        new_lease = True
    # A turn snapshot may be updated by a second claim; serialize updates per token.
    turn_lock = snapshot.with_suffix(".lock")
    try:
        descriptor = os.open(turn_lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        if new_lease:
            lease.unlink(missing_ok=True)
        raise ValueError("This conversation is updating its review snapshot; retry") from None
    try:
        os.close(descriptor)
        payload = json.loads(snapshot.read_text(encoding="utf-8-sig"))
        if payload.get("owner") != owner or payload.get("vault") != str(vault.resolve()):
            raise ValueError("Review snapshot changed during claim")
        pending = payload.setdefault("claimed_files", {})
        if relative not in pending:
            pending[relative] = hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
            atomic_write(snapshot, json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
    except BaseException:
        if new_lease:
            lease.unlink(missing_ok=True)
        raise
    finally:
        turn_lock.unlink(missing_ok=True)
    return relative


def clear_review_snapshot(event: dict[str, Any]) -> None:
    path = review_snapshot_path(event)
    if path is None:
        return
    try:
        if path.is_file():
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            for relative in (payload.get("claimed_files") or {}):
                lease = Path(payload["vault"]) / ".codex-obsidian-memory" / "claims" / f"{hashlib.sha256(relative.encode('utf-8')).hexdigest()}.json"
                if lease.is_file():
                    claim = json.loads(lease.read_text(encoding="utf-8-sig"))
                    if claim.get("token") == path.stem and claim.get("path") == relative:
                        lease.unlink()
        path.unlink(missing_ok=True)
    except (OSError, ValueError, json.JSONDecodeError):
        pass
