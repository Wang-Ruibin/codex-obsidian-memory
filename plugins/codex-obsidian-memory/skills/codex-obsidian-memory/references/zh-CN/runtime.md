# 自动准备运行环境

[English](../runtime.md)

用户安装记忆插件，无需处理 Python 依赖。在已授权的设置流程中、初始化和信任 Hook 之前准备运行环境。这个步骤与知识库登记分离，不创建或修改笔记。

## 运行入口

从 Skill 目录执行：

```bash
sh ../../scripts/memoryctl.sh prepare-runtime
sh ../../scripts/memoryctl.sh status
sh ../../scripts/memoryctl.sh local-register --path /absolute/path/to/project
```

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action prepare-runtime
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action status
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action local-register --path C:\projects\example
```

启动器接受所有记忆 CLI 命令。`hook` 处理生命周期 JSON 协议，`routine` 运行周期任务，`python-path` 输出选定解释器路径供调度器安装使用。嵌入这些入口时保留标准输入、参数、标准输出和退出码。

Windows 原生兼容集成还可用 `-Action manage` 通过已准备的解释器调用其管理器。未安装原生管理器时会报告错误；普通 marketplace 插件不含此管理器。

## 选择与下载

准备时先检查缓存的解释器，再查找已有 Python 3.11+。没有合适版本时，从官方 `astral-sh/uv` GitHub Release 下载固定版本的 uv 启动工具，按 `assets/runtime/uv-assets.txt` 中记录的 SHA-256 校验，再通过 uv 准备 Astral 分发的私有 Python 3.12。不安装 pip 包。启动工具和下载／解压暂存目录通过 finally/trap 清理；仅保留选定的运行环境和解释器路径记录。

私有目录默认为 `$CODEX_HOME/obsidian-memory/runtime/<OS>-<architecture>`，或用户常规 `.codex` 目录下的对应位置。Windows、Linux、macOS 使用各自目录；隔离测试或部署可通过 `CODEX_OBSIDIAN_RUNTIME_DIR` 指定。不会替换系统 Python、修改全局 PATH 或 shell 配置，也不写入 Windows Python 注册表或安装命令别名。启动参数禁用 uv 项目配置和持久下载缓存，不上传笔记或凭据。

自动下载支持 Windows x64/ARM64、glibc Linux x64/ARM64（含 WSL）以及 macOS Intel/Apple Silicon。其他平台可以使用已有合适解释器，未经验证不得宣称支持自动准备私有环境。首次私有准备需要通过 HTTPS 访问 GitHub/Astral 分发文件。离线时可使用已有合适运行环境；如果没有，报告下载阻碍，不把手动配置依赖的工作转交用户。

## 日常运行与清理

Hook 和普通 CLI 命令只使用缓存或已有合适解释器，不自行下载。不可用时由 Agent 显式执行准备，并说明网络或权限问题。重复准备会复用有效环境。`prepare-runtime --managed` 用于即使已有系统 Python 也明确选择私有运行环境，适合受控安装测试；私有缓存有效时不强制重新下载。

短期 `prepare.lock` 目录防止并发设置。准备中断后，先检查对应操作，再清理失效锁。已配置的运行环境可能仍被 Hook 和周期任务使用，不能当测试临时文件删除。测试必须使用独立运行目录并在验证后清理。卸载会与其他集成残留一起保留运行环境；只有集成及引用它的任务都不再使用时，才清理这一精确私有目录，不删除知识库或系统 Python。

## 开发与验证

开发仍使用 Python 3.11+ 和标准库。验证 Windows/POSIX 设置、已有 Python 复用、PATH 中没有 Python 时的缓存运行、Hook 标准输入、中文与空格参数、退出码传递、校验失败和临时文件清理。对支持的发布平台另外执行真实私有下载检查。`hooks.json` 的启动命令变化后需要正常的宿主审阅与信任，不持久绕过审查。

来源：[uv Python 管理](https://docs.astral.sh/uv/guides/install-python/)、[uv 命令参考](https://docs.astral.sh/uv/reference/cli/)。
