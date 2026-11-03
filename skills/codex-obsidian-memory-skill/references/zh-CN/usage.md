# 纯 Skill 记忆命令

[English](../usage.md)

从本 Skill 文件夹通过 `sh scripts/skillctl.sh` 或 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/skillctl.ps1 -Action` 调用。下列示例使用 shell 启动器，Windows 在 `-Action` 后使用相同参数。`/absolute/project` 等是需要向用户确认的实际路径占位符。Python 辅助程序只需 Python 3.11+ 和标准库。

## 配置与已有笔记

```bash
sh scripts/skillctl.sh prepare-runtime
sh scripts/skillctl.sh status
sh scripts/skillctl.sh init --vault /absolute/vault --github-owner Example --locale en
sh scripts/skillctl.sh validate
```

没有 GitHub 的本地项目用 `--local-only` 替代 `--github-owner`。只安装不会创建知识库。模板增量安装，绝不覆盖已有文件。自定义布局使用 `--no-template` 和显式映射，例如 `--path projects_dir=20-Projects --path project_index=20-Projects/index.md`。映射必须相对知识库、互不重叠且不越界。`status` 显示已配置路径；不重复初始化已有配置。

Skill 在 `$CODEX_HOME/obsidian-memory-skill` 保存自身配置和任务哈希，不修改 `config.toml`、全局 `AGENTS.md`、Hook 定义或信任、系统调度器或其他客户端设置。仅在请求时准备运行时，普通命令不下载代码。`CODEX_OBSIDIAN_SKILL_CONFIG` 和 `CODEX_OBSIDIAN_SKILL_RUNTIME_DIR` 是隔离测试或受管部署的可选覆盖项，不需要普通用户配置。

可通过 `--no-template` 和匹配的映射复用 Hook 版知识库，Hook 配置独立保留。已有本地项目用 `local-register --project-id <existing-id> --path <root>` 关联，不给同一项目新造身份。不复制凭据或信任记录。同一任务交给另一版本回写前，先停止使用前一版本；仅安装 Skill 不会停用已有 Hook。切换或卸载 Hook 版是单独的明确请求，本 Skill 不会覆盖安装它。

## 任务生命周期与审查

```bash
sh scripts/skillctl.sh start --cwd /absolute/project
sh scripts/skillctl.sh start --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh register-github --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh search "SQLite Windows rename" --cwd /absolute/project
sh scripts/skillctl.sh search "SQLite Windows rename" --scope projects --cwd /absolute/project
sh scripts/skillctl.sh read 20-projects/example/main.md --start-line 12 --line-count 40 --cwd /absolute/project
sh scripts/skillctl.sh claim-shared 30-reusable/topic.md --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh changes --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh finish --task-id TASK_ID --cwd /absolute/project --review-file /absolute/review.md
```

`TASK_ID` 替换为 `start` 返回值。命令使用 `CODEX_THREAD_ID` 或 `--session-id` 提供的实际 ID；会话、工作区、知识库、项目身份和分支必须匹配任务记录。`start` 恢复同一会话和工作区的未完成任务，保留原始哈希。切分支后应回到原分支完成原任务，不能悄悄替换审核范围。前一任务结束后才开始新任务。没有变化时不传 `--review-file`。

`changes` 只合并当前项目文件夹、已占用共享页和明确的初始化、登记、标题同步回执。其他项目的并行修改不属于当前审查。知识库维护会覆盖全库，应避免并发维护。占用使用知识库共享租约，因此 Hook 与 Skill 不能同时占用同一共享笔记。同一项目文件的编辑另行协调。元数据只含路径、身份和哈希，不含笔记正文。旧快照可能在七天后过期；基线缺失会明确失败，不会声称审查成功。

UTF-8 审查草稿需有可见的“Knowledge-base writeback review”或“知识库回写审查”标题，每个变化路径单列一条并写清具体事实或章节。最终回复必须展示该审查并邀请纠正。`finish` 拒绝漏文件和笼统描述，失败后保留状态供重试，成功后只释放自身占用。它不验证事实准确性或语义完整性，是显式命令，不是宿主 Stop 拦截。随后删除临时草稿，无需隐藏审查标记。

## 项目控制与笔记字段

```bash
sh scripts/skillctl.sh local-register --path /absolute/local-project --name Example
sh scripts/skillctl.sh local-list
sh scripts/skillctl.sh local-disable LOCAL_ID
sh scripts/skillctl.sh local-enable LOCAL_ID
sh scripts/skillctl.sh local-move LOCAL_ID --path /absolute/new-root
sh scripts/skillctl.sh exclude Example/private-repo
sh scripts/skillctl.sh include Example/other-repo
sh scripts/skillctl.sh disable
sh scripts/skillctl.sh enable
```

本地登记需要用户明确请求。保留返回的 `local:<id>` 和已有笔记。没有具名分支时，进度放主页。GitHub 范围来自精确 origin `OWNER/REPO`，排除项优先于包含项、本地目录和对话授权。`disable` 与 `enable` 只影响本 Skill 配置。卸载通过宿主正常 Skill 管理删除本 Skill 文件夹，保留状态与知识库笔记。需要清理状态时另行审查，绝不删除或移动知识库。

默认根分区为 `10-memory`、`20-projects`、`30-reusable` 和 `40-conversations`。唯一项目主页使用 `type: project`，并有 `github_repo: OWNER/REPO` 或 `project_id: local:<id>`。分支页使用 `type: branch`、相同项目身份和大小写精确的 `working_branch`。主页直接链接子页，子页链接回主页。在 Windows/macOS 上，为仅大小写不同的分支使用不同文件名。

共享经验使用配置中的模板：`type: reusable-memory`、`status: verified`、`summary`、`keywords`、`source_repo` 或 `source_project_id`、`source_branch`、`source_note`、`verified_on`。来源必须是合格项目笔记，仓库级来源分支留空。建主题前先检索，记录条件、限制和证据，保留冲突条件，过时笔记以 `status: retired` 保留。更新索引并验证链接，不为普通对话笔记伪造验证日期或来源。

## 普通对话

```bash
sh scripts/skillctl.sh conversation-enable --cwd /absolute/ordinary-folder --session-id ACTUAL_SESSION_ID --title "Displayed title"
sh scripts/skillctl.sh conversation-sync --session-id ACTUAL_SESSION_ID
sh scripts/skillctl.sh conversation-disable --session-id ACTUAL_SESSION_ID
sh scripts/skillctl.sh conversation-disable --session-id ACTUAL_SESSION_ID --freeze-title
sh scripts/skillctl.sh conversation-list
```

命令不根据提示词关键词推断授权。用户直接要求当前真实对话后才开启，GitHub 和本地项目保留原路由。随后用 `start` 即时加载并审查当前任务。每个对话只加载、检索自己的笔记。关闭后保留文件，显式同步或下次 `start` 时仍跟随标题；`--freeze-title` 同时暂停改名。Skill 空闲时不会自动同步。

Codex 标题查询仅读取已登记 ID 的显示元数据，优先 `threads.name`，其次 `session_index.jsonl`，不读取聊天流水或认证文件。开启时缺少元数据，用 `--title` 提供实际显示标题。固定 `conversation_id` 不随改名改变；非法字符、大小写、Unicode 碰撞及重名均安全处理，不覆盖其他笔记。创建与改名回执保留至审查完成。范围路由、检索、防碰撞处理和结构校验与 Hook 插件使用同一来源生成的运行代码。
