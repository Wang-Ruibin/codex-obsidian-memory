# Codex Obsidian 长期记忆

[English source / 英文原文](SKILL.md)

管理本插件提供的本地优先长期记忆集成。普通项目任务由生命周期 Hook 自动处理，无需显式调用本 Skill。

## 选择操作

- 首次设置：在本 Skill 目录运行 `python ../../scripts/memoryctl.py init --vault <绝对路径> --github-owner <owner> [--locale en|zh-CN]`。
- 当前状态：运行 `python ../../scripts/memoryctl.py status`。
- 结构检查：运行 `python ../../scripts/memoryctl.py validate`。
- 可逆控制：使用 `enable` 或 `disable`。
- 移除活动集成：先卸载可选自动化，再运行 `uninstall`；永远不要删除知识库。说明周期状态、日志或中断任务快照可能继续保留在 `$CODEX_HOME/obsidian-memory` 中。
- 仓库范围：使用 `exclude OWNER/REPO` 或 `include OWNER/REPO`。
- 周期简报或体检：安装操作系统调度器前阅读[自动化参考](references/zh-CN/automation.md)。
- 接管现有知识库：修改文件前阅读[迁移参考](references/zh-CN/migration.md)。

Windows 上没有 `python` 时优先使用 `py.exe`。

## 安全不变量

- 修改全局 Codex 配置、创建计划任务或移除集成状态前立即取得批准。
- 永远不得读取、复制、输出或保存密码、私钥、令牌、Cookie 或其他凭据。
- 永远不得删除或移动知识库。模板安装默认为增量式；仅在用户审阅冲突并明确批准 `--force-template` 时覆盖。
- 非默认现有布局使用 `--no-template` 和可重复 `--path KEY=RELATIVE_PATH` 映射，然后执行验证。
- 每个 GitHub 仓库只保留一个文件夹和一个项目主页；仅为持久分支进度创建分支页。`0.4.0` 对 `working_branch` 使用不区分大小写的比较，因此要提示只在大小写上不同的分支名风险。
- 未解决说法放入开放问题；不要保留猜测、对话流水账或一次性输出。
- Hook 在已配置 GitHub 范围外必须静默；知识库自身是唯一维护例外。
- 只要回写了知识库 Markdown，最终回复必须包含可见的 **知识库回写审查**，列出每个修改文件及新增、修改或删除的具体事实或章节，邀请用户纠正后再追加披露标记。Stop Hook 只校验标题和标记，不对清单内容做语义完整性校验。没有回写时不显示该部分。

## 设置完成标准

运行 `init` 后：

1. 使用 `status` 审阅配置、语言和知识库路径。
2. 打开 `/hooks`，审阅并信任命令。
3. 在一个已配置 GitHub 仓库中新开会话。
4. 确认全局记忆、匹配的仓库主页，以及已经存在的匹配分支页均被加载。
5. 运行 `validate`，保持断链、重复项目主页和重复分支身份均为 0。

图谱或结构变更阅读[结构参考](references/zh-CN/structure.md)；信任、writable root 或凭据审查阅读[安全参考](references/zh-CN/security.md)。
