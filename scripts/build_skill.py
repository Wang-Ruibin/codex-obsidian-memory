"""Assemble/check the self-contained Skill from the canonical shared runtime."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/codex-obsidian-memory"
SKILL = ROOT / "skills/codex-obsidian-memory-skill"
MODULES = ("memory_core.py", "memory_context.py", "local_projects.py", "conversations.py",
           "reuse_memory.py", "validate_vault.py", "writeback_review.py")


def generated_files() -> dict[Path, bytes]:
    files = {Path("scripts/runtime") / name: (PLUGIN / "scripts" / name).read_bytes().replace(b"\r\n", b"\n")
             for name in MODULES}
    files[Path("LICENSE")] = (ROOT / "LICENSE").read_bytes().replace(b"\r\n", b"\n")
    for source in (PLUGIN / "assets/vault-template").rglob("*"):
        if not source.is_file() or source.name == "AGENTS.md":
            continue
        text = source.read_text(encoding="utf-8").replace("memoryctl.py", "skillctl")
        text = text.replace("--review-token <current-turn-token>", "--task-id <task-id-from-start>")
        files[Path("assets/vault-template") / source.relative_to(PLUGIN / "assets/vault-template")] = text.encode("utf-8")
    files[Path("assets/runtime/uv-assets.txt")] = (PLUGIN / "assets/runtime/uv-assets.txt").read_bytes().replace(b"\r\n", b"\n")
    ps = (PLUGIN / "scripts/memoryctl.ps1").read_text(encoding="utf-8")
    ps = ps[:ps.index("switch ($Action) {")] + """if ($Action -eq 'python-path') { Write-Output $selected; exit 0 }
$result = Invoke-Program $selected (@('-X', 'utf8', '-B', (Join-Path $PSScriptRoot 'skill_memory.py'), $Action) + $Arguments)
[Console]::Out.Write($result.Out)
[Console]::Error.Write($result.Err)
exit $result.Code
"""
    ps = ps.replace("memoryctl.ps1", "skillctl.ps1").replace("obsidian-memory\\runtime", "obsidian-memory-skill\\runtime")
    ps = ps.replace("CODEX_OBSIDIAN_RUNTIME_DIR", "CODEX_OBSIDIAN_SKILL_RUNTIME_DIR")
    ps = ps.replace("python-path | hook | routine ARGS | COMMAND ARGS", "python-path | COMMAND ARGS")
    ps = ps.replace("this plugin", "this Skill").replace("Plugin runtime", "Skill runtime")
    files[Path("scripts/skillctl.ps1")] = ps.encode("utf-8")
    sh = (PLUGIN / "scripts/memoryctl.sh").read_text(encoding="utf-8")
    sh = sh[:sh.rindex('case "$action" in')] + """case "$action" in
    python-path) printf '%s\\n' "$selected" ;;
    *) exec "$selected" -X utf8 -B "$script_dir/skill_memory.py" "$action" "$@" ;;
esac
"""
    sh = sh.replace("memoryctl.sh", "skillctl.sh").replace("obsidian-memory/runtime", "obsidian-memory-skill/runtime")
    sh = sh.replace("CODEX_OBSIDIAN_RUNTIME_DIR", "CODEX_OBSIDIAN_SKILL_RUNTIME_DIR")
    sh = sh.replace("python-path | hook | routine ARGS | COMMAND ARGS", "python-path | COMMAND ARGS")
    sh = sh.replace("this plugin", "this Skill").replace("Plugin runtime", "Skill runtime")
    files[Path("scripts/skillctl.sh")] = sh.encode("utf-8")
    manifest = {
        "version": json.loads((PLUGIN / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))["version"],
        "mode": "skill", "generated_by": "scripts/build_skill.py",
        "files": {path.as_posix(): hashlib.sha256(data).hexdigest()
                  for path, data in sorted(files.items(), key=lambda item: item[0].as_posix())},
    }
    files[Path("bundle.json")] = (json.dumps(manifest, indent=2) + "\n").encode("utf-8")
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail on stale/missing generated files without writing")
    args = parser.parse_args()
    mismatches = []
    expected = generated_files()
    for relative, data in expected.items():
        target = SKILL / relative
        actual = target.read_bytes().replace(b"\r\n", b"\n") if target.is_file() else None
        if actual != data:
            mismatches.append(relative.as_posix())
            if not args.check:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
    # Unexpected runtime modules can silently reintroduce Hook/background dependencies.
    extra = {p.name for p in (SKILL / "scripts/runtime").glob("*.py")} - set(MODULES)
    if extra:
        raise ValueError("Remove obsolete generated modules after reviewing them: " + ", ".join(sorted(extra)))
    print(json.dumps({"checked_files": len(expected), "stale": mismatches if args.check else []}))
    return 1 if args.check and mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
