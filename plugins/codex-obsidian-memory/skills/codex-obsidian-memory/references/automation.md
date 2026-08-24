# Recurring briefs and audits / 周期简报与体检

## English

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

## 中文

周期任务是可选功能，默认关闭。

### Windows

在插件根目录审阅并运行：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1
```

安装器把 runner 和提示词复制到 Codex 状态目录下的稳定路径，然后创建两个当前用户任务。每个任务每天触发，但 `routine_runner.py` 会记录成功的 ISO 周和日历月，因此每个工作流每周期只运行一次。错过的触发会在下次可用时重试；失败不推进状态。

只删除这两个任务：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1 -Uninstall
```

移除插件状态或插件包前先运行该卸载命令。

### macOS 与 Linux

使用 launchd、systemd timer 或 cron 调度：

```text
0 9 * * * python3 /path/to/plugin/scripts/routine_runner.py weekly
15 9 * * * python3 /path/to/plugin/scripts/routine_runner.py monthly
```

机器必须具有可用的非交互 `codex exec` 登录，且插件 Hook 已被信任。
