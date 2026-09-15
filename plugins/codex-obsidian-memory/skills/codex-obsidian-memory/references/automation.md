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

```powershell
powershell -ExecutionPolicy Bypass -File "<plugin-root>\scripts\install-windows-tasks.ps1" -Uninstall
```

Run the uninstall before removing plugin state or the package.

## Linux with systemd user services

```bash
bash "/absolute/path/to/plugin/scripts/install-linux-systemd.sh"
```

The installer requires no `sudo`. It creates persistent user-level timers, so a missed check can run after you sign in again. It also fixes the Python and Codex locations at setup time instead of depending on a later shell environment.

```bash
bash "/absolute/path/to/plugin/scripts/install-linux-systemd.sh" --uninstall
```

If `systemctl --user` is unavailable, use another user-level scheduler.

## macOS and other schedulers

```text
0 9 * * * /absolute/path/to/python3 /absolute/path/to/plugin/scripts/routine_runner.py weekly --codex /absolute/path/to/codex
15 9 * * * /absolute/path/to/python3 /absolute/path/to/plugin/scripts/routine_runner.py monthly --codex /absolute/path/to/codex
```

The machine needs a working non-interactive Codex login and trusted hooks. Use absolute paths for Python, Codex and the runner in scheduler definitions. After setup, run each routine once with `--dry-run` or ask Codex to verify the next scheduled time.
