# 周期简报与体检

[English](../automation.md)

周期任务是可选功能，默认关闭。

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1
```

安装器把 runner 和本地化提示词复制到稳定的 Codex 状态目录，然后创建两个当前用户任务。Windows 任务通过 `wscript.exe` 和 `run-hidden.vbs` 启动，因此正常执行与错误退出都保持无窗口。任务每天触发，成功的 ISO 周和日历月会去重；错过后补跑，失败不推进状态。

Runner 会记录入口级失败；Codex 成功退出后，必须确认目标报告内容已变化，并通过图谱验证，才记录该周期成功。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1 -Uninstall
```

移除插件状态或插件包前先运行该卸载命令。

## 使用 systemd user service 的 Linux

```bash
bash scripts/install-linux-systemd.sh
```

安装器不需要 `sudo`。它把 runner 和本地化提示词复制到 `${XDG_DATA_HOME:-$HOME/.local/share}/codex-obsidian-memory/automation`，把用户 unit 写入 `${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user`，解析 `python3` 与 `codex` 绝对路径，并启用持久每日 timer。

```bash
bash scripts/install-linux-systemd.sh --uninstall
```

如果 `systemctl --user` 不可用，使用其他用户级调度器。

## macOS 与其他调度器

```text
0 9 * * * python3 /path/to/plugin/scripts/routine_runner.py weekly
15 9 * * * python3 /path/to/plugin/scripts/routine_runner.py monthly
```

机器需要可用的非交互 `codex exec` 登录和已信任 Hook。调度器定义中使用可执行文件绝对路径。
