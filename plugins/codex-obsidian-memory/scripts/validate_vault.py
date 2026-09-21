from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

from memory_core import frontmatter_value, load_config, vault_path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def markdown_files(vault: Path) -> list[Path]:
    return sorted(
        (
            path
            for path in vault.rglob("*.md")
            if not any(part.startswith(".") for part in path.relative_to(vault).parts)
        ),
        key=lambda path: str(path).casefold(),
    )


def graph_report(vault: Path, files: list[Path]) -> dict[str, object]:
    visible = [path for path in files if path.name.casefold() != "agents.md"]
    by_relative = {
        path.relative_to(vault).with_suffix("").as_posix().casefold(): path for path in visible
    }
    by_stem: dict[str, list[Path]] = defaultdict(list)
    for path in visible:
        by_stem[path.stem.casefold()].append(path)
    degree = {path: 0 for path in visible}
    broken: list[str] = []
    for source in visible:
        text = re.sub(
            r"```.*?```", "", source.read_text(encoding="utf-8"), flags=re.DOTALL
        )
        for match in re.finditer(r"\[\[([^|\]#]+)", text):
            link = match.group(1).strip()
            if "<" in link or ">" in link:
                continue
            clean_link = re.sub(r"\.md$", "", link, flags=re.IGNORECASE).replace("\\", "/")
            key = os.path.normpath(clean_link).replace("\\", "/").casefold()
            target = None
            if "/" in link or "\\" in link:
                target = by_relative.get(key)
                if target is None:
                    local_key = os.path.normpath(
                        (source.parent.relative_to(vault) / clean_link).as_posix()
                    ).replace("\\", "/").casefold()
                    target = by_relative.get(local_key)
            else:
                local_key = (source.parent.relative_to(vault) / key).as_posix().casefold()
                target = by_relative.get(local_key)
                if target is None and len(by_stem[key]) == 1:
                    target = by_stem[key][0]
            if target is None:
                broken.append(f"{source.relative_to(vault)} -> {link}")
                continue
            degree[source] += 1
            degree[target] += 1
    return {
        "visible_nodes": len(visible),
        "broken_links": broken,
        "orphans": [str(path.relative_to(vault)) for path, count in degree.items() if count == 0],
    }


def main() -> int:
    config = load_config()
    vault_text = str(config.get("vault") or "")
    if not vault_text:
        print(json.dumps({"error": "Integration is not configured."}, indent=2))
        return 1
    vault = Path(vault_text).resolve()
    if not vault.is_dir():
        print(json.dumps({"error": f"Vault not found: {vault}"}, indent=2))
        return 1

    required = ["home", "global_memory", "maintenance", "template", "project_index"]
    missing = [key for key in required if not vault_path(vault, config, key).is_file()]
    files = markdown_files(vault)
    projects_dir = vault_path(vault, config, "projects_dir")
    project_homes: dict[str, list[str]] = defaultdict(list)
    branch_identities: dict[tuple[str, str], list[str]] = defaultdict(list)
    for path in files:
        try:
            path.relative_to(projects_dir)
        except ValueError:
            continue
        text = path.read_text(encoding="utf-8")
        page_type = frontmatter_value(text, "type").casefold()
        repository = frontmatter_value(text, "github_repo")
        if page_type == "project" and repository:
            project_homes[repository.casefold()].append(str(path.relative_to(vault)))
        elif page_type == "branch" and repository:
            branch = frontmatter_value(text, "working_branch")
            if branch:
                branch_identities[(repository.casefold(), branch)].append(
                    str(path.relative_to(vault))
                )

    duplicate_projects = {
        repository: paths for repository, paths in project_homes.items() if len(paths) > 1
    }
    duplicate_branches = {
        f"{repository}:{branch}": paths
        for (repository, branch), paths in branch_identities.items()
        if len(paths) > 1
    }
    graph = graph_report(vault, files)
    report = {
        "vault": str(vault),
        "required_files_missing": missing,
        "project_homes": sum(len(paths) for paths in project_homes.values()),
        "branch_pages": sum(len(paths) for paths in branch_identities.values()),
        "duplicate_project_homes": duplicate_projects,
        "duplicate_branch_identities": duplicate_branches,
        **graph,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    healthy = not (
        missing
        or duplicate_projects
        or duplicate_branches
        or graph["broken_links"]
        or graph["orphans"]
    )
    return 0 if healthy else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
