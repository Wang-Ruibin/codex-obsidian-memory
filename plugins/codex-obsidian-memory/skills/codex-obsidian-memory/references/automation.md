# Recurring briefs and audits

[简体中文](zh-CN/automation.md)

Recurring jobs are optional and disabled by default.

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1
```

The installer copies the runner and localized prompts to a stable Codex state directory, then creates two current-user tasks. Windows tasks launch through `wscript.exe` and `run-hidden.vbs`, so normal execution and errors remain windowless. Each task triggers daily, while successful ISO-week and calendar-month periods are deduplicated. Missed triggers retry; failures do not advance state.

The runner records entry-level failures, requires the configured report content to change after a successful Codex exit, and runs graph validation before recording the period as successful.

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1 -Uninstall
```

Run the uninstall before removing plugin state or the package.

## Linux with systemd user services

```bash
bash scripts/install-linux-systemd.sh
```

The installer requires no `sudo`. It copies the runner and localized prompts to `${XDG_DATA_HOME:-$HOME/.local/share}/codex-obsidian-memory/automation`, writes user units under `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user`, resolves absolute `python3` and `codex` paths, and enables persistent daily timers.

```bash
bash scripts/install-linux-systemd.sh --uninstall
```

If `systemctl --user` is unavailable, use another user-level scheduler.

## macOS and other schedulers

```text
0 9 * * * python3 /path/to/plugin/scripts/routine_runner.py weekly
15 9 * * * python3 /path/to/plugin/scripts/routine_runner.py monthly
```

The machine needs a working non-interactive `codex exec` login and trusted hooks. Use absolute executable paths in scheduler definitions.
