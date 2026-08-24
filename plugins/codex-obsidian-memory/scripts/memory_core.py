from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


CONFIG_VERSION = 1
REVIEW_MARKER = "<!-- obsidian-memory-reviewed -->"
DEFAULT_PATHS = {
    "home": "00-memory-home.md",
    "global_memory": "10-memory/global-memory.md",
    "maintenance": "10-memory/maintenance.md",
    "template": "10-memory/project-template.md",
    "project_index": "20-projects/project-index.md",
    "projects_dir": "20-projects",
    "weekly_brief": "10-memory/weekly-brief.md",
    "monthly_audit": "10-memory/monthly-audit.md",
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


def redact_secrets(text: str) -> str:
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
        result = re.sub(pattern, replacement, result, flags=re.DOTALL | re.IGNORECASE)
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
    relative = Path(str((config.get("paths") or DEFAULT_PATHS)[key]))
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
        rf"(?m)^{re.escape(key)}:\s*['\"]?([^'\"\r\n]+)", frontmatter.group("body")
    )
    return match.group(1).strip() if match else ""


def find_project_page(vault: Path, config: dict[str, Any], repository: str) -> Path | None:
    projects_dir = vault_path(vault, config, "projects_dir")
    if not repository or not projects_dir.is_dir():
        return None
    for candidate in sorted(projects_dir.rglob("*.md"), key=lambda path: str(path).casefold()):
        try:
            note = candidate.read_text(encoding="utf-8")
        except OSError:
            continue
        if frontmatter_value(note, "type").casefold() != "project":
            continue
        if frontmatter_value(note, "github_repo").casefold() == repository.casefold():
            return candidate
    return None


def branch_slug(branch: str) -> str:
    slug = re.sub(r"[<>:\"/\\|?*]+", "--", branch.strip())
    slug = re.sub(r"-+", "-", slug).strip(" .-")
    return slug or "detached-head"
