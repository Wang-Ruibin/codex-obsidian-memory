# Recurring briefs and audits

[简体中文](zh-CN/automation.md)

Recurring jobs are optional and disabled by default.

For the easiest setup, tell Codex:

```text
Use $codex-obsidian-memory to set up the weekly brief and monthly audit on this machine. Explain when they will run, ask me before creating scheduled tasks, and verify the result.
```

Codex should choose the matching installer, locate the installed plugin and ask immediately before creating operating-system scheduler entries. Use the commands below only when you prefer manual setup; replace every path placeholder first.

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File "<plugin-root>\scripts\install-windows-tasks.ps1"
```

The installer creates two tasks for your Windows account. They run without opening a console window. Each task checks daily, but an already completed week or month is not generated twice. Missed runs retry later, and failures do not mark the period complete.

You can trust a period as complete only when the report really changed and the vault still passes validation. Failures are kept in a local diagnostic log.

The installer fixes the Python and Codex executable paths at setup time. Use `-CodexPath` if Codex is not discoverable as an application on PATH. UTF-8 mode and the hidden launcher also apply to validator subprocesses.

After a plugin update, rerun the installer to refresh the copied runtime and prompts. Reuse the existing `-TaskPrefix` so it updates the same two tasks, and retain `routines.json` in the integration state directory. Before switching older custom tasks, migrate their completed-period state and confirm their schedule; do not leave a second scheduler enabled. A task exit code of zero can mean that this week or month was already complete, so check the report and routine log to confirm an actual generation.

Both routines use configured paths for the four vault areas. Briefs draw tasks from eligible GitHub and registered local projects; audits check exact identities, reusable-lesson provenance and conversation structure. Conversation bodies are not inputs to either report, and routines do not enable conversation memory or change consent settings.

```powershell
powershell -ExecutionPolicy Bypass -File "<plugin-root>\scripts\install-windows-tasks.ps1" -Uninstall
```

Run the uninstall before removing plugin state or the package.

## Linux with systemd user services

```bash
bash "/absolute/path/to/plugin/scripts/install-linux-systemd.sh"
```

The installer requires no `sudo`. It creates persistent user-level timers, so a missed check can run after you sign in again. It automatically prepares a plugin runtime if needed and fixes its interpreter and Codex locations at setup time instead of depending on a later shell environment.

Rerun the installer after a plugin update to refresh the copied runtime and prompts while retaining completed periods. When Windows and WSL share one vault, keep only the chosen host's scheduler enabled.

```bash
bash "/absolute/path/to/plugin/scripts/install-linux-systemd.sh" --uninstall
```

If `systemctl --user` is unavailable, use another user-level scheduler.

## macOS and other schedulers

```text
0 9 * * * /absolute/path/to/python3 -X utf8 -B /absolute/path/to/plugin/scripts/routine_runner.py weekly --codex /absolute/path/to/codex
15 9 * * * /absolute/path/to/python3 -X utf8 -B /absolute/path/to/plugin/scripts/routine_runner.py monthly --codex /absolute/path/to/codex
```

The machine needs a working non-interactive Codex login and trusted hooks. Use absolute paths for the selected interpreter, Codex and the runner in scheduler definitions. The agent can obtain the interpreter with `sh <plugin-root>/scripts/memoryctl.sh python-path` after automatic preparation; the user does not need to install Python. After setup, run each routine once with `--dry-run` or ask Codex to verify the next scheduled time.
