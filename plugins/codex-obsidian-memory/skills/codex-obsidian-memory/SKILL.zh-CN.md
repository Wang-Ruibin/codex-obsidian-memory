# Codex Obsidian 长期记忆

[English source / 英文原文](SKILL.md)

管理本插件提供的本地优先长期记忆集成。普通项目任务由生命周期 Hook 自动处理，无需显式调用本 Skill。

## 选择操作

- 设置前自动准备：macOS/Linux 执行 `sh ../../scripts/memoryctl.sh prepare-runtime`；Windows 执行 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action prepare-runtime`。复用合适的 Python 或准备插件私有环境，不要求用户手动安装 Python/pip 或配置 PATH。支持平台和排错见[运行环境参考](references/zh-CN/runtime.md)。
- 命令统一通过 `sh ../../scripts/memoryctl.sh <command> <args>`，或 Windows 的 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action <command> <args>` 执行。首次设置使用 `init --vault <absolute-path> --github-owner <owner> [--locale en|zh-CN]`。
- 没有 GitHub：使用 `init --vault <absolute-path> --local-only [--locale en|zh-CN]`。已有安装无需重新初始化即可增加本地项目。
- 明确启用当前本地项目：阅读[本地项目参考](references/zh-CN/local-projects.md)，然后执行 `local-register --path <confirmed-root>`。立即在本轮使用返回的记忆上下文，并执行当前任务的回写审查；不得延迟到新会话才生效。仅提及记忆而未要求启用，不构成登记授权。
- 本地控制：使用 `local-list`、`local-disable <id>`、`local-enable <id>` 和 `local-move <id> --path <new-root>`，保留自动生成的 ID 和笔记。`context --cwd <workspace>` 可在同一会话重新加载记忆。
- 当前状态：通过启动入口运行 `status`。
- 结构检查：通过启动入口运行 `validate`。
- 可逆控制：使用 `enable` 或 `disable`。
- 移除活动集成：先卸载可选自动化，再运行 `uninstall`；永远不要删除知识库。说明周期状态、日志或中断任务快照可能继续保留在 `$CODEX_HOME/obsidian-memory` 中。
- 仓库范围：使用 `exclude OWNER/REPO` 或 `include OWNER/REPO`。
- 周期简报或体检：安装操作系统调度器前阅读[自动化参考](references/zh-CN/automation.md)。
- 接管现有知识库：修改文件前阅读[迁移参考](references/zh-CN/migration.md)。

参考资料里的 Python 源码命令是开发者等效入口；面向用户使用上述平台启动器，包括本地登记、search、read 和 context。Hook 使用同一已准备环境，绝不自行下载。Hook 定义更新后，通过宿主正常流程审阅并信任新的启动命令，不复制或伪造信任哈希。

## 跨项目经验复用

在实质实现前、失败后或改变方案前，先检索共享经验，未命中再查合格项目笔记；候选不适用时显式检索项目。使用 `search` 和 `read` 按需读取，核对适用条件和来源，历史分支只作参考。提炼已验证经验、适配旧知识库或处理冲突时，阅读 [经验复用参考](references/zh-CN/reuse.md)。

## 安全不变量

- 修改全局 Codex 配置、创建计划任务或移除集成状态前立即取得批准。
- 永远不得读取、复制、输出或保存密码、私钥、令牌、Cookie 或其他凭据。
- 永远不得删除或移动知识库。模板安装默认为增量式；仅在用户审阅冲突并明确批准 `--force-template` 时覆盖。
- 非默认现有布局使用 `--no-template` 和可重复 `--path KEY=RELATIVE_PATH` 映射，然后执行验证。
- 每个 GitHub 仓库只保留一个文件夹和一个项目主页；仅为持久分支进度创建分支页。`working_branch` 按大小写精确匹配，`github_repo` 不区分大小写。在不区分文件名大小写的系统上，为 `Release` 和 `release` 等分支使用不同文件名。
- 未解决说法放入开放问题；不要保留猜测、对话流水账或一次性输出。
- Hook 在已配置 GitHub 范围和明确启用的本地根目录之外保持静默。本地项目使用固定 `project_id`，不虚构 `github_repo`；没有具名 Git 分支时进度写在项目主页。知识库自身是维护例外，明确的 GitHub 排除项仍然有效。
- 只要回写了知识库 Markdown，最终回复必须包含可见的 **知识库回写审查**。每个修改文件单独列一条，包含相对知识库的路径和新增、修改或删除的具体事实或章节。仅当文件名在知识库与变更清单中唯一时，才允许省略目录。邀请用户纠正后，依次追加披露标记和审查标记。Stop Hook 在首次和重试时都检查文件覆盖与最低说明要求，但无法验证事实准确性或详尽语义。不要把条目藏在引用、注释或代码块中。没有回写时不显示该部分。

## 设置完成标准

运行 `init` 后：

1. 使用 `status` 审阅配置、语言和知识库路径。
2. 打开 `/hooks`，审阅并信任命令。
3. 打开合格的 GitHub 仓库，或明确登记本地项目。登记后当前会话立即加载记忆，之后再用新会话验证持久性。
4. 确认全局记忆、匹配的仓库主页，以及已经存在的匹配分支页均被加载。
5. 运行 `validate`，保持断链、重复项目主页和重复分支身份均为 0。

图谱或结构变更阅读[结构参考](references/zh-CN/structure.md)；信任、writable root 或凭据审查阅读[安全参考](references/zh-CN/security.md)。
