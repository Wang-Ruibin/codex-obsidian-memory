---
name: codex-obsidian-memory
description: Set up, validate, troubleshoot, or remove local Codex-to-Obsidian memory, including hooks, GitHub scope, vault routing, and routines / 设置、验证、排查或移除本地 Codex-to-Obsidian 长期记忆，包括 Hook、GitHub 范围、知识库路由与周期任务；普通项目工作由已安装 Hook 自动处理。
---

# Codex Obsidian Memory / Codex Obsidian 长期记忆

## English

Manage the local-first memory integration packaged with this plugin. The lifecycle Hook handles ordinary project tasks without requiring this Skill.

## Choose the operation

- First-time setup: run `python ../../scripts/memoryctl.py init --vault <absolute-vault-path> --github-owner <owner>` from this Skill directory.
- Current state: run `python ../../scripts/memoryctl.py status`.
- Structural check: run `python ../../scripts/memoryctl.py validate`.
- Reversible control: use `enable` or `disable`.
- Complete integration-state removal: uninstall optional automation first, then run `uninstall`. Never remove the vault.
- Repository scope: use `exclude OWNER/REPO` or `include OWNER/REPO`.
- Recurring briefs or audits: read [automation.md](references/automation.md) before installing an OS scheduler.
- Existing vault adoption: read [migration.md](references/migration.md) before changing files.

On Windows, prefer `py.exe` when `python` is unavailable.

## Safety invariants

- Obtain user approval immediately before changing global Codex configuration, creating scheduler entries, or removing integration state.
- Never read, copy, print, or store passwords, private keys, tokens, cookies, or other credentials. Store only paths, GitHub repository names, and memory policy.
- Do not delete or move an existing vault during setup, disable, or plugin removal. Template installation is additive unless the user explicitly requests `--force-template` after reviewing conflicts.
- For an existing non-default layout, use `--no-template` plus repeatable `--path KEY=RELATIVE_PATH` mappings. Validate before enabling ordinary work.
- Keep one repository folder and one project home per GitHub repository. Put branch-specific progress only in a same-folder page whose `working_branch` exactly matches the current Git branch.
- Treat unresolved claims as open questions. Do not convert guesses, raw chat logs, or one-off debugging output into durable memory.
- The Hook must be silent outside configured GitHub scope. The vault itself is the only maintenance exception.

## Setup outcome

After `init`:

1. Review configuration and vault paths with `status`.
2. Open `/hooks`, review the plugin commands, and trust them.
3. Start a new thread inside one configured GitHub repository.
4. Verify that global memory plus the exact repository and branch pages load.
5. Run `validate` and keep zero broken links, duplicate repository homes, and duplicate branch identities.

Read [structure.md](references/structure.md) when changing the graph model or note schema. Read [security.md](references/security.md) when reviewing trust, writable roots, or credential boundaries.

## 中文

管理本插件提供的本地优先长期记忆集成。普通项目任务由生命周期 Hook 自动处理，无需显式调用本 Skill。

### 选择操作

- 首次设置：在本 Skill 目录运行 `python ../../scripts/memoryctl.py init --vault <知识库绝对路径> --github-owner <owner>`。
- 当前状态：运行 `python ../../scripts/memoryctl.py status`。
- 结构检查：运行 `python ../../scripts/memoryctl.py validate`。
- 可逆控制：使用 `enable` 或 `disable`。
- 完整移除集成状态：先卸载可选自动化，再运行 `uninstall`；永远不要删除知识库。
- 仓库范围：使用 `exclude OWNER/REPO` 或 `include OWNER/REPO`。
- 周期简报或体检：安装操作系统调度器前阅读 [automation.md](references/automation.md)。
- 接管现有知识库：修改文件前阅读 [migration.md](references/migration.md)。

Windows 上没有 `python` 时优先使用 `py.exe`。

### 安全不变量

- 修改全局 Codex 配置、创建计划任务或移除集成状态前立即取得用户批准。
- 永远不得读取、复制、输出或保存密码、私钥、令牌、Cookie 或其他凭据；只保存路径、GitHub 仓库名和记忆策略。
- 设置、停用或移除插件时不得删除或移动现有知识库。模板安装默认为增量式；仅在用户审阅冲突并明确要求 `--force-template` 时覆盖。
- 现有非默认布局使用 `--no-template` 和可重复的 `--path KEY=RELATIVE_PATH` 映射；启用普通工作前先验证。
- 每个 GitHub 仓库只保留一个仓库文件夹和一个项目主页；分支进度只写在同文件夹、`working_branch` 与当前 Git 分支精确匹配的页面。
- 未解决的说法放入开放问题，不把猜测、原始对话或一次性调试输出变成持久记忆。
- Hook 在已配置 GitHub 范围外必须静默；知识库自身是唯一维护例外。

### 设置完成标准

运行 `init` 后：

1. 使用 `status` 审阅配置和知识库路径。
2. 打开 `/hooks`，审阅并信任插件命令。
3. 在一个已配置 GitHub 仓库中新开会话。
4. 确认全局记忆、精确仓库主页和精确分支页均被加载。
5. 运行 `validate`，保持断链、重复项目主页和重复分支身份均为 0。

修改图谱模型或笔记结构时阅读 [structure.md](references/structure.md)；审查信任、writable root 或凭据边界时阅读 [security.md](references/security.md)。
