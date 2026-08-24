# 周期简报与体检

[English](../automation.md)

周期任务是可选功能，默认关闭。

## Windows

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1
```

安装器把 runner 和本地化提示词复制到稳定的 Codex 状态目录，然后创建两个当前用户任务。任务每天触发，成功的 ISO 周和日历月会去重；错过后补跑，失败不推进状态。

```powershell
powershell -ExecutionPolicy Bypass -File scripts/install-windows-tasks.ps1 -Uninstall
```

移除插件状态或插件包前先运行该卸载命令。

## macOS 与 Linux

```text
0 9 * * * python3 /path/to/plugin/scripts/routine_runner.py weekly
15 9 * * * python3 /path/to/plugin/scripts/routine_runner.py monthly
```

机器需要可用的非交互 `codex exec` 登录和已信任 Hook。
