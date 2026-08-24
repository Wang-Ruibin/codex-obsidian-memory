from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

from memory_core import atomic_write, integration_dir, load_config, vault_path


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_ROUTINE = "runner"
CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


class RoutineBusy(RuntimeError):
    pass


def prompt_path(routine: str, locale: str) -> Path:
    installed_copy = (
        Path(__file__).resolve().parent / "prompts" / locale / f"{routine}.md"
    )
    if installed_copy.is_file():
        return installed_copy
    return PLUGIN_ROOT / "assets" / "prompts" / locale / f"{routine}.md"


def validator_path() -> Path:
    installed_copy = Path(__file__).resolve().parent / "validate_vault.py"
    if installed_copy.is_file():
        return installed_copy
    return PLUGIN_ROOT / "scripts" / "validate_vault.py"


def current_period(routine: str, now: datetime) -> str:
    if routine == "weekly":
        year, week, _ = now.isocalendar()
        return f"{year}-W{week:02d}"
    return now.strftime("%Y-%m")


@contextmanager
def routine_lock(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        if time.time() - path.stat().st_mtime <= 6 * 60 * 60:
            raise RoutineBusy(f"Routine is already running: {path.name}")
        path.unlink()
        descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        yield
    finally:
        os.close(descriptor)
        path.unlink(missing_ok=True)


def load_state(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8-sig"))


def append_failure_log(routine: str, error: BaseException) -> None:
    try:
        log_dir = integration_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{routine}.log"
        with log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"\nfailed={datetime.now().astimezone().isoformat()}\n")
            handle.write("".join(traceback.format_exception(error)))
    except OSError:
        pass


def main() -> int:
    global ACTIVE_ROUTINE
    parser = argparse.ArgumentParser(description="Run a deduplicated memory routine.")
    parser.add_argument("routine", choices=("weekly", "monthly"))
    parser.add_argument("--force", action="store_true", help="Run even if this period succeeded.")
    parser.add_argument("--dry-run", action="store_true", help="Show the decision without running Codex.")
    parser.add_argument("--codex", help="Override the Codex executable for testing.")
    args = parser.parse_args()
    ACTIVE_ROUTINE = args.routine

    config = load_config()
    if not config.get("enabled"):
        raise ValueError("Integration is disabled or not configured.")
    vault_text = str(config.get("vault") or "")
    vault = Path(vault_text).resolve() if vault_text else None
    if vault is None or not vault.is_dir():
        raise ValueError(f"Configured vault is unavailable: {vault_text or '(missing)'}")

    now = datetime.now().astimezone()
    period = current_period(args.routine, now)
    state_path = integration_dir() / "routines.json"
    state_key = f"last_{args.routine}_period"
    lock_path = integration_dir() / f"{args.routine}.lock"
    with routine_lock(lock_path):
        state = load_state(state_path)
        should_run = args.force or state.get(state_key) != period
        print(json.dumps({"routine": args.routine, "period": period, "run": should_run}))
        if args.dry_run or not should_run:
            return 0

        log_dir = integration_dir() / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"{args.routine}.log"
        atomic_write(
            log_path,
            f"started={now.isoformat()}\nroutine={args.routine}\nperiod={period}\n",
        )

        codex = args.codex or shutil.which("codex")
        if not codex:
            raise ValueError("Codex executable was not found on PATH.")
        locale = str(config.get("locale") or "en")
        prompt_file = prompt_path(args.routine, locale)
        if not prompt_file.is_file():
            raise ValueError(f"Routine prompt was not found: {prompt_file}")
        output_key = "weekly_brief" if args.routine == "weekly" else "monthly_audit"
        output = vault_path(vault, config, output_key)
        output_content_before = output.read_bytes() if output.is_file() else None
        prompt = (
            prompt_file.read_text(encoding="utf-8")
            + f"\n\nConfigured vault: {vault}\n"
            + f"Update this exact report path: {output}\n"
        )
        preflight = ""
        if args.routine == "monthly":
            validation = subprocess.run(
                [sys.executable, str(validator_path())],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
                creationflags=CREATE_NO_WINDOW,
            )
            preflight = validation.stdout + validation.stderr
            prompt += "\nPre-audit validator output:\n```json\n" + preflight + "\n```\n"
        command = [
            codex,
            "exec",
            "--cd",
            str(vault),
            "--skip-git-repo-check",
            "--approve-for-me",
            "--ephemeral",
            "--color",
            "never",
            "-",
        ]
        completed = subprocess.run(
            command,
            input=prompt,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
            creationflags=CREATE_NO_WINDOW,
        )
        log = ("[preflight]\n" + preflight + "\n" if preflight else "")
        log += completed.stdout + ("\n[stderr]\n" + completed.stderr if completed.stderr else "")
        failure_reason = ""
        if completed.returncode == 0:
            if not output.is_file():
                failure_reason = f"Expected report was not created: {output}"
            elif output.read_bytes() == output_content_before:
                failure_reason = (
                    "Codex exited successfully but did not update the expected report: "
                    f"{output}"
                )
        if completed.returncode == 0 and not failure_reason:
            postflight = subprocess.run(
                [sys.executable, str(validator_path())],
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
                creationflags=CREATE_NO_WINDOW,
            )
            log += "\n[postflight]\n" + postflight.stdout + postflight.stderr
            if postflight.returncode != 0:
                failure_reason = (
                    f"Vault validation failed after {args.routine} routine with exit code "
                    f"{postflight.returncode}."
                )
        if failure_reason:
            log += "\n[validation-error]\n" + failure_reason + "\n"
        with log_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(log)
        if completed.returncode != 0:
            raise RuntimeError(f"Codex routine failed with exit code {completed.returncode}.")
        if failure_reason:
            raise RuntimeError(failure_reason)
        state[state_key] = period
        state["updated_at"] = now.isoformat()
        atomic_write(state_path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RoutineBusy as exc:
        print(json.dumps({"routine": ACTIVE_ROUTINE, "busy": True, "message": str(exc)}))
        raise SystemExit(0)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        append_failure_log(ACTIVE_ROUTINE, exc)
        print(f"error={exc}", file=sys.stderr)
        raise SystemExit(1)
