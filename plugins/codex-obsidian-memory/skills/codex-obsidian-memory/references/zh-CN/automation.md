# 周期简报与体检

[English](../automation.md)

周期任务是可选功能，默认关闭。

最省事的方式是直接告诉 Codex：

```text
使用 $codex-obsidian-memory 在这台机器上设置每周简报和每月体检。说明它们何时运行，创建计划任务前先询问我，并在完成后验证结果。
```

Codex 应根据系统选择安装器、定位已安装插件，并在创建操作系统计划任务前立即征求同意。只有想手工设置时才使用下面的命令；执行前请替换所有路径占位符。

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File "<plugin-root>\scripts\install-windows-tasks.ps1"
```

安装器会为当前 Windows 用户创建两个任务，运行时不会弹出控制台窗口。任务每天检查一次，但已经完成的周或月不会重复生成；错过后会补跑，失败也不会把该周期标记为完成。

只有报告确实发生变化且知识库仍通过验证，该周期才算完成。失败原因保存在本地诊断日志中。

```powershell
powershell -ExecutionPolicy Bypass -File "<plugin-root>\scripts\install-windows-tasks.ps1" -Uninstall
```

移除插件状态或插件包前先运行该卸载命令。

## 使用 systemd user service 的 Linux

```bash
bash "/absolute/path/to/plugin/scripts/install-linux-systemd.sh"
```

安装器不需要 `sudo`。它会创建持久的用户级 timer，因此错过的检查可以在你再次登录后补跑。安装时还会固定 Python 和 Codex 的位置，不依赖以后启动任务时的 shell 环境。

```bash
bash "/absolute/path/to/plugin/scripts/install-linux-systemd.sh" --uninstall
```

如果 `systemctl --user` 不可用，使用其他用户级调度器。

## macOS 与其他调度器

```text
0 9 * * * /absolute/path/to/python3 /absolute/path/to/plugin/scripts/routine_runner.py weekly --codex /absolute/path/to/codex
15 9 * * * /absolute/path/to/python3 /absolute/path/to/plugin/scripts/routine_runner.py monthly --codex /absolute/path/to/codex
```

机器需要可用的非交互 Codex 登录和已信任 Hook。调度器定义中必须为 Python、Codex 和 runner 使用绝对路径。设置后可以先用 `--dry-run` 检查一次，或让 Codex 告诉你下一次计划运行时间。
