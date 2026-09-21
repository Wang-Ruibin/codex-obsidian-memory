"""Exercise real vault adoption on a temporary Markdown-only copy.

No source note contents or credentials are printed or included in the result.
No global Codex configuration, installed plugin or source vault is modified.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "plugins" / "codex-obsidian-memory" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from memory_core import REVIEW_MARKER, WRITEBACK_DISCLOSURE_MARKER, repository_identity


def inventory(root: Path) -> dict[str, str]:
    result = {}
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if not path.resolve().is_relative_to(root.resolve()):
            raise ValueError("Vault contains a Markdown link outside its root.")
        result[relative.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def verify(args: argparse.Namespace) -> dict:
    source = args.source_vault.resolve(strict=True)
    before = inventory(source)
    if not before:
        raise ValueError("Source vault contains no visible Markdown files.")
    repository, branch = repository_identity(args.project.resolve())
    if not repository or not branch:
        raise ValueError("Project needs a GitHub origin and a checked-out branch.")
    with tempfile.TemporaryDirectory(prefix="memory-adoption-") as temporary:
        root = Path(temporary)
        vault = root / "vault"
        for relative in before:
            target = vault / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((source / relative).read_bytes())
        environment = os.environ.copy()
        environment.update(CODEX_HOME=str(root / "codex-home"),
                           CODEX_OBSIDIAN_MEMORY_CONFIG=str(root / "state" / "config.json"),
                           PYTHONUTF8="1")

        def run(script, *arguments, event=None):
            result = subprocess.run([sys.executable, str(SCRIPTS / script), *arguments],
                                    input=json.dumps(event) if event else None,
                                    text=True, encoding="utf-8", capture_output=True,
                                    env=environment, timeout=60)
            if result.returncode:
                # Do not print captured note context or private filenames on failure.
                raise RuntimeError(f"{script} {arguments[:1]} failed (exit {result.returncode}); "
                                   "inspect the source vault locally with validate.")
            return result.stdout

        command = ["init", "--vault", str(vault), "--github-owner", repository.split("/")[0],
                   "--no-template", "--no-writable-root"]
        for mapping in args.path:
            command.extend(["--path", mapping])
        run("memoryctl.py", *command)
        if inventory(vault) != before:
            raise AssertionError("Adoption modified existing Markdown.")
        status = json.loads(run("memoryctl.py", "status"))
        assert status["enabled"] and status["vault_exists"]
        validation = json.loads(run("memoryctl.py", "validate"))
        event = {"hook_event_name": "UserPromptSubmit", "cwd": str(args.project.resolve()),
                 "session_id": "adoption-check", "turn_id": "first-turn"}
        context = json.loads(run("hook.py", event=event))["hookSpecificOutput"]["additionalContext"]
        if "not indexed yet" in context:
            raise ValueError("Source vault must already contain this project's linked home and branch page.")
        from memory_core import find_project_page
        config = json.loads((root / "state" / "config.json").read_text(encoding="utf-8"))
        project = find_project_page(vault, config, repository)
        if project is None or project.name not in context:
            raise AssertionError("Project memory was not loaded.")
        token = "Adoption verification: instructions should include an observable success condition."
        project.write_text(project.read_text(encoding="utf-8") + "\n- " + token + "\n", encoding="utf-8")
        relative = project.relative_to(vault).as_posix()
        stop = {**event, "hook_event_name": "Stop", "last_assistant_message": REVIEW_MARKER}
        assert json.loads(run("hook.py", event=stop))["decision"] == "block"
        stop.update(stop_hook_active=True, last_assistant_message=(
            "## Knowledge-base writeback review\n- Memory updated.\n"
            + WRITEBACK_DISCLOSURE_MARKER + "\n" + REVIEW_MARKER))
        assert json.loads(run("hook.py", event=stop))["decision"] == "block"
        stop["last_assistant_message"] = (
            f"## Knowledge-base writeback review\n- `{relative}`: added the instruction success-condition preference.\n"
            "Please review and correct it.\n" + WRITEBACK_DISCLOSURE_MARKER + "\n" + REVIEW_MARKER)
        assert json.loads(run("hook.py", event=stop))["continue"]
        new_session = {**event, "session_id": "adoption-next-session", "turn_id": "next-turn"}
        loaded = json.loads(run("hook.py", event=new_session))["hookSpecificOutput"]["additionalContext"]
        assert token in loaded
        run("memoryctl.py", "validate")
        run("memoryctl.py", "disable")
        assert not run("hook.py", event=new_session).strip()
        run("memoryctl.py", "enable")
        assert token in json.loads(run("hook.py", event=new_session))["hookSpecificOutput"]["additionalContext"]
        preserved = inventory(vault)
        run("memoryctl.py", "uninstall")
        assert inventory(vault) == preserved
        assert inventory(source) == before
        return {"platform": platform.system(), "python": platform.python_version(),
                "source_markdown_files": len(before),
                "project_homes": validation["project_homes"], "branch_pages": validation["branch_pages"],
                "visible_nodes": validation["visible_nodes"],
                "checks": {name: True for name in (
                    "adoption_preserves_notes", "status_enabled", "graph_valid", "project_context_loaded",
                    "missing_disclosure_blocked", "incomplete_retry_blocked", "complete_review_accepted",
                    "new_session_hook_loads_saved_fact", "disable_silent", "enable_restores_context",
                    "uninstall_preserves_notes", "source_unchanged")},
                "scope": "CLI and hook subprocesses against a copy of an existing vault; not an interactive Codex session"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-vault", required=True, type=Path)
    parser.add_argument("--project", required=True, type=Path)
    parser.add_argument("--path", action="append", default=[], metavar="KEY=RELATIVE_PATH")
    arguments = parser.parse_args()
    print(json.dumps(verify(arguments), ensure_ascii=True, indent=2))
