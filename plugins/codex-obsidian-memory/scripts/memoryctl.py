from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from local_projects import command_local, command_register_github, local_registry

from memory_core import (
    DEFAULT_PATHS,
    atomic_write,
    codex_home,
    config_path,
    integration_dir,
    load_config,
    normalized_repository,
    save_config,
    claim_shared_file,
    validated_paths,
    vault_path,
)


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
VAULT_TEMPLATE_ROOT = PLUGIN_ROOT / "assets" / "vault-template"


def install_template(vault: Path, force: bool, locale: str) -> tuple[int, int]:
    created = 0
    skipped = 0
    for template_root in (VAULT_TEMPLATE_ROOT / "shared", VAULT_TEMPLATE_ROOT / locale):
        if not template_root.is_dir():
            raise ValueError(f"Vault template locale is unavailable: {locale}")
        for source in sorted(template_root.rglob("*"), key=lambda path: str(path).casefold()):
            relative = source.relative_to(template_root)
            target = vault / relative
            if source.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if target.exists() and not force:
                skipped += 1
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            created += 1
    return created, skipped


def toml_array(values: list[str]) -> str:
    return "[" + ", ".join(json.dumps(value, ensure_ascii=False) for value in values) + "]"


def normalized_path(value: str) -> str:
    return os.path.normcase(os.path.normpath(value))


def configure_writable_root(vault: Path) -> tuple[str, bool]:
    config_toml = codex_home() / "config.toml"
    if not config_toml.is_file():
        return "Codex config.toml was not found; add the vault as a writable root manually.", False
    text = config_toml.read_text(encoding="utf-8")
    parsed = tomllib.loads(text)
    if parsed.get("sandbox_mode") != "workspace-write":
        return 'sandbox_mode is not "workspace-write"; no global setting was changed.', False

    section = re.search(
        r"(?ms)^\[sandbox_workspace_write\]\s*\n(?P<body>.*?)(?=^\[|\Z)", text
    )
    target = normalized_path(str(vault))
    if not section:
        addition = f"\n[sandbox_workspace_write]\nwritable_roots = {toml_array([str(vault)])}\n"
        new_text = text.rstrip() + "\n" + addition
    else:
        body = section.group("body")
        roots_match = re.search(
            r"(?m)^writable_roots[\t ]*=[\t ]*(\[[^\r\n]*\])[\t ]*$", body
        )
        if roots_match:
            roots = list(tomllib.loads("roots = " + roots_match.group(1))["roots"])
            if any(normalized_path(str(root)) == target for root in roots):
                return "Vault writable root already present.", False
            roots.append(str(vault))
            new_body = (
                body[: roots_match.start()]
                + f"writable_roots = {toml_array(roots)}"
                + body[roots_match.end() :]
            )
        else:
            if "writable_roots" in body:
                return "writable_roots uses a multiline form; no automatic edit was attempted.", False
            new_body = body.rstrip() + f"\nwritable_roots = {toml_array([str(vault)])}\n"
        new_text = text[: section.start("body")] + new_body + text[section.end("body") :]

    backup = config_toml.with_name("config.toml.obsidian-memory.bak")
    if not backup.exists():
        shutil.copy2(config_toml, backup)
    atomic_write(config_toml, new_text)
    tomllib.loads(config_toml.read_text(encoding="utf-8"))
    return f"Added vault writable root; backup: {backup}", True


def remove_writable_root(vault: Path) -> str:
    config_toml = codex_home() / "config.toml"
    if not config_toml.is_file():
        return "Codex config.toml was not found."
    text = config_toml.read_text(encoding="utf-8")
    parsed = tomllib.loads(text)
    roots = list(parsed.get("sandbox_workspace_write", {}).get("writable_roots", []))
    target = normalized_path(str(vault))
    retained = [root for root in roots if normalized_path(str(root)) != target]
    if len(retained) == len(roots):
        return "Vault writable root was already absent."
    section = re.search(
        r"(?ms)^\[sandbox_workspace_write\]\s*\n(?P<body>.*?)(?=^\[|\Z)", text
    )
    if not section:
        return "sandbox_workspace_write section was not found; no edit was attempted."
    body = section.group("body")
    roots_match = re.search(
        r"(?m)^writable_roots[\t ]*=[\t ]*(\[[^\r\n]*\])[\t ]*$", body
    )
    if not roots_match:
        return "writable_roots uses an unsupported form; no edit was attempted."
    new_body = (
        body[: roots_match.start()]
        + f"writable_roots = {toml_array(retained)}"
        + body[roots_match.end() :]
    )
    new_text = text[: section.start("body")] + new_body + text[section.end("body") :]
    backup = config_toml.with_name("config.toml.obsidian-memory-uninstall.bak")
    shutil.copy2(config_toml, backup)
    atomic_write(config_toml, new_text)
    tomllib.loads(config_toml.read_text(encoding="utf-8"))
    return f"Removed plugin-added writable root; backup: {backup}"


def config_has_writable_root(vault: Path) -> bool:
    config_toml = codex_home() / "config.toml"
    if not config_toml.is_file():
        return False
    parsed = tomllib.loads(config_toml.read_text(encoding="utf-8"))
    roots = parsed.get("sandbox_workspace_write", {}).get("writable_roots", [])
    target = normalized_path(str(vault))
    return any(normalized_path(str(root)) == target for root in roots)


def command_init(args: argparse.Namespace) -> int:
    vault = args.vault.resolve()
    if vault.exists() and not vault.is_dir():
        raise ValueError(f"Vault path is not a directory: {vault}")
    vault.mkdir(parents=True, exist_ok=True)
    owners = sorted({owner.strip() for owner in (args.github_owner or []) if owner.strip()}, key=str.casefold)
    if not owners and not args.local_only:
        raise ValueError("Choose --local-only or provide at least one --github-owner.")
    if args.local_only and (owners or args.exclude or args.scope_mode != "github-owner"):
        raise ValueError("--local-only cannot be combined with GitHub scope options")
    exclusions = sorted(
        {normalized_repository(value) for value in (args.exclude or [])}, key=str.casefold
    )
    path_overrides: dict[str, str] = {}
    for item in args.path or []:
        if "=" not in item:
            raise ValueError(f"Expected --path KEY=RELATIVE_PATH, got: {item}")
        key, value = item.split("=", 1)
        path_overrides[key.strip()] = value.strip().replace("\\", "/")
    paths = validated_paths(path_overrides)
    if args.no_template and args.force_template:
        raise ValueError("--no-template and --force-template cannot be combined.")
    created, skipped = (
        (0, 0)
        if args.no_template
        else install_template(vault, args.force_template, args.locale)
    )
    previous = load_config()
    config = {
        "version": 1,
        "enabled": True,
        "vault": str(vault),
        "locale": args.locale,
        "scope_mode": "local-only" if args.local_only else args.scope_mode,
        "github_owners": owners,
        "included_repositories": [],
        "excluded_repositories": exclusions,
        "paths": paths,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "writable_root_added": False,
        "local_projects": previous.get("local_projects", []) if previous.get("vault")
            and Path(previous["vault"]).resolve() == vault else [],
    }
    save_config(config)
    writable = "Skipped by request."
    writable_added = False
    if not args.no_writable_root:
        writable, writable_added = configure_writable_root(vault)
    config["writable_root_added"] = writable_added
    save_config(config)
    print(f"enabled=True\nvault={vault}\nlocale={args.locale}\ngithub_owners={','.join(owners)}")
    print(f"template_files_written={created}\ntemplate_files_skipped={skipped}")
    print(f"writable_root={writable}")
    print("next=Review and trust the plugin hooks with /hooks, then start a new thread.")
    return 0


def command_status(_: argparse.Namespace) -> int:
    config = load_config()
    vault_text = str(config.get("vault") or "")
    vault = Path(vault_text).resolve() if vault_text else None
    result = {
        "config": str(config_path()),
        "configured": config_path().is_file(),
        "enabled": bool(config.get("enabled")),
        "vault": vault_text,
        "vault_exists": bool(vault and vault.is_dir()),
        "locale": config.get("locale", "en"),
        "scope_mode": config.get("scope_mode"),
        "github_owners": config.get("github_owners", []),
        "included_repositories": config.get("included_repositories", []),
        "excluded_repositories": config.get("excluded_repositories", []),
        "local_projects": local_registry(config),
        "writable_root": bool(vault and config_has_writable_root(vault)),
        "reuse_index": str(vault_path(vault, config, "reuse_index")) if vault else None,
        "reuse_index_exists": bool(vault and vault_path(vault, config, "reuse_index").is_file()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["configured"] and result["vault_exists"] else 1


def set_enabled(enabled: bool) -> int:
    if not config_path().is_file():
        raise ValueError("Integration is not configured. Run init first.")
    config = load_config()
    config["enabled"] = enabled
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_config(config)
    print(f"enabled={str(enabled).lower()}")
    return 0


def change_repository(repository: str, excluded: bool) -> int:
    config = load_config()
    if not config_path().is_file():
        raise ValueError("Integration is not configured. Run init first.")
    canonical = normalized_repository(repository)
    exclusions = {str(value).casefold(): str(value) for value in config.get("excluded_repositories", [])}
    inclusions = {str(value).casefold(): str(value) for value in config.get("included_repositories", [])}
    key = canonical.casefold()
    if excluded:
        exclusions[key] = canonical
        inclusions.pop(key, None)
    else:
        exclusions.pop(key, None)
        inclusions[key] = canonical
    config["excluded_repositories"] = sorted(exclusions.values(), key=str.casefold)
    config["included_repositories"] = sorted(inclusions.values(), key=str.casefold)
    config["updated_at"] = datetime.now(timezone.utc).isoformat()
    save_config(config)
    print(f"repository={canonical}\nexcluded={str(excluded).lower()}")
    return 0


def command_validate(_: argparse.Namespace) -> int:
    from validate_vault import main as validate_main
    return validate_main()


def command_retrieval(args: argparse.Namespace) -> int:
    from hook import resolve_scope
    from reuse_memory import read_reference, search

    config = load_config()
    if not config.get("enabled") or not config.get("vault"):
        raise ValueError("Memory is disabled or not configured; no notes were searched.")
    vault = Path(config["vault"]).resolve()
    if not vault.is_dir():
        raise ValueError("Configured vault is unavailable; no notes were searched.")
    scope = resolve_scope({"cwd": str(args.cwd.resolve())}, config, vault)
    if not scope.eligible:
        raise ValueError("Workspace is not an eligible GitHub or enabled local project; no notes were searched.")
    if args.command == "search":
        result = search(vault, config, args.query, args.scope, args.limit)
    elif args.command == "context":
        from hook import build_context
        result = {"context": build_context(scope, config, vault)}
    else:
        result = read_reference(vault, config, args.path, args.start_line, args.line_count)
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0


def command_claim_shared(args: argparse.Namespace) -> int:
    from hook import resolve_scope

    config = load_config()
    if not config.get("enabled") or not config.get("vault"):
        raise ValueError("Memory is disabled or not configured")
    vault = Path(config["vault"]).resolve()
    scope = resolve_scope({"cwd": str(args.cwd.resolve())}, config, vault)
    owner = scope.project_id or scope.repository.casefold()
    if not scope.eligible or scope.kind == "vault" or not owner:
        raise ValueError("Shared claims require an eligible current project conversation")
    relative = claim_shared_file(args.review_token, owner, args.path, vault, config)
    print(json.dumps({"claimed": relative, "owner": owner,
                      "next": "Edit only this claimed shared note, then disclose it in this turn's writeback review."},
                     ensure_ascii=True))
    return 0


def command_uninstall(_: argparse.Namespace) -> int:
    if not config_path().is_file():
        print("configured=false\nvault_untouched=true")
        return 0
    config = load_config()
    automation_present = (integration_dir() / "automation").exists()
    vault_text = str(config.get("vault") or "")
    writable = "Not removed because this plugin did not add it."
    if vault_text and config.get("writable_root_added"):
        writable = remove_writable_root(Path(vault_text).resolve())
    config_path().unlink(missing_ok=True)
    state_dir = integration_dir()
    try:
        state_dir.rmdir()
    except OSError:
        pass
    print("configured=false")
    print(f"writable_root={writable}")
    print("vault_untouched=true")
    print(f"automation_present={str(automation_present).lower()}")
    if automation_present:
        print("warning=Remove scheduled tasks with install-windows-tasks.ps1 -Uninstall.")
    print("next=Remove the plugin from Codex after starting a new thread.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Codex Obsidian Memory.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    init = subparsers.add_parser("init", help="Create or adopt a vault and enable memory.")
    init.add_argument("--vault", type=Path, required=True)
    init.add_argument("--github-owner", action="append")
    init.add_argument("--local-only", action="store_true", help="Use explicitly registered local projects without a GitHub account.")
    init.add_argument("--locale", choices=("en", "zh-CN"), default="en")
    init.add_argument("--exclude", action="append")
    init.add_argument("--scope-mode", choices=("github-owner", "indexed-only"), default="github-owner")
    init.add_argument(
        "--path",
        action="append",
        metavar="KEY=RELATIVE_PATH",
        help=f"Override a vault path. Keys: {', '.join(DEFAULT_PATHS)}",
    )
    init.add_argument("--no-template", action="store_true", help="Adopt existing notes without copying defaults.")
    init.add_argument("--force-template", action="store_true")
    init.add_argument("--no-writable-root", action="store_true")
    init.set_defaults(handler=command_init)
    subparsers.add_parser("status", help="Show integration state.").set_defaults(handler=command_status)
    subparsers.add_parser("enable", help="Enable hooks.").set_defaults(handler=lambda _: set_enabled(True))
    subparsers.add_parser("disable", help="Disable hooks without deleting data.").set_defaults(handler=lambda _: set_enabled(False))
    exclude = subparsers.add_parser("exclude", help="Exclude one OWNER/REPO.")
    exclude.add_argument("repository")
    exclude.set_defaults(handler=lambda args: change_repository(args.repository, True))
    include = subparsers.add_parser("include", help="Explicitly include one OWNER/REPO.")
    include.add_argument("repository")
    include.set_defaults(handler=lambda args: change_repository(args.repository, False))
    subparsers.add_parser("validate", help="Validate vault structure.").set_defaults(handler=command_validate)
    register = subparsers.add_parser("local-register", help="Explicitly enable a local project and load its memory now.")
    register.add_argument("--path", type=Path, default=Path.cwd(), help="Confirmed project root directory.")
    register.add_argument("--name", help="Human-readable project name.")
    register.add_argument("--project-id", help="Attach an existing local project from this vault in another environment.")
    register.set_defaults(handler=command_local)
    github = subparsers.add_parser("register-github", help="Register one eligible GitHub repository under the vault's shared project-index lock.")
    github.add_argument("--cwd", type=Path, default=Path.cwd())
    github.add_argument("--review-token", required=True, help="Token injected by this turn's UserPromptSubmit Hook.")
    github.set_defaults(handler=command_register_github)
    for operation in ("local-disable", "local-enable", "local-move"):
        command = subparsers.add_parser(operation, help="Manage an explicitly registered local project; notes are retained.")
        command.add_argument("project_id")
        if operation == "local-move":
            command.add_argument("--path", type=Path, required=True)
        command.set_defaults(handler=command_local)
    subparsers.add_parser("local-list", help="List local project identities and path registrations.").set_defaults(
        handler=lambda _: (print(json.dumps(local_registry(load_config()), ensure_ascii=True, indent=2)) or 0))
    context = subparsers.add_parser("context", help="Load eligible workspace memory into this conversation immediately.")
    context.add_argument("--cwd", type=Path, default=Path.cwd())
    context.set_defaults(handler=command_retrieval)
    claim = subparsers.add_parser("claim-shared", help="Reserve one shared note for this project's current turn before editing.")
    claim.add_argument("path", help="Exact vault-relative global-memory or shared-lesson Markdown path.")
    claim.add_argument("--review-token", required=True, help="Token injected by this turn's UserPromptSubmit Hook.")
    claim.add_argument("--cwd", type=Path, default=Path.cwd())
    claim.set_defaults(handler=command_claim_shared)
    search = subparsers.add_parser("search", help="Find reusable lessons, falling back to eligible project notes.")
    search.add_argument("query", help="Short space-separated problem, technology and environment keywords.")
    search.add_argument("--cwd", type=Path, default=Path.cwd(), help="Task workspace, not the plugin directory.")
    search.add_argument("--scope", choices=("auto", "shared", "projects"), default="auto")
    search.add_argument("--limit", type=int, choices=range(1, 11), default=5)
    search.set_defaults(handler=command_retrieval)
    read = subparsers.add_parser("read", help="Read a bounded excerpt of an eligible reference note.")
    read.add_argument("path", help="Exact vault-relative path returned by search.")
    read.add_argument("--cwd", type=Path, default=Path.cwd())
    read.add_argument("--start-line", type=int, default=1)
    read.add_argument("--line-count", type=int, choices=range(1, 81), default=40)
    read.set_defaults(handler=command_retrieval)
    subparsers.add_parser(
        "uninstall", help="Remove plugin state and its own writable-root entry; never delete the vault."
    ).set_defaults(handler=command_uninstall)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    return int(args.handler(args))


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        print(f"error={exc}", file=sys.stderr)
        raise SystemExit(1)
