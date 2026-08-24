# Recurring briefs and audits

Recurring jobs are optional and disabled by default.

## Windows

From the plugin root, review and run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1
```

The installer copies the runner and prompts to a stable directory under the Codex state folder, then creates two current-user tasks. Each triggers daily, but `routine_runner.py` records successful ISO-week and calendar-month periods, so each workflow runs only once per period. Missed triggers retry at the next available run; failures do not advance state.

Remove only those tasks with:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1 -Uninstall
```

Run this uninstall before removing plugin state or the plugin package.

## macOS and Linux

Schedule these with launchd, systemd timers, or cron:

```text
0 9 * * * python3 /path/to/plugin/scripts/routine_runner.py weekly
15 9 * * * python3 /path/to/plugin/scripts/routine_runner.py monthly
```

The machine must have a working non-interactive `codex exec` login and trusted plugin hooks.
