# Recurring briefs and audits

[简体中文](zh-CN/automation.md)

Recurring jobs are optional and disabled by default.

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1
```

The installer copies the runner and localized prompts to a stable Codex state directory, then creates two current-user tasks. Each triggers daily, while successful ISO-week and calendar-month periods are deduplicated. Missed triggers retry; failures do not advance state.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1 -Uninstall
```

Run the uninstall before removing plugin state or the package.

## macOS and Linux

```text
0 9 * * * python3 /path/to/plugin/scripts/routine_runner.py weekly
15 9 * * * python3 /path/to/plugin/scripts/routine_runner.py monthly
```

The machine needs a working non-interactive `codex exec` login and trusted hooks.
