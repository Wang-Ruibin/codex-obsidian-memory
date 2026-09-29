# 本地项目记忆

[English](../local-projects.md)

用户明确要求为本地项目启用记忆时使用，包括没有 Git 或 GitHub 账号的普通文件夹。仅提及记忆、引用示例或询问工作原理，不代表同意登记项目。下列命令从 Skill 目录运行，解释器使用当前环境已安装的版本。

## 在当前会话启用

先检查 `status`。已经配置记忆时保留现有配置，不要重跑 `init`。尚未配置时，询问知识库存放位置，以及用户希望仅管理本地项目，还是同时使用 GitHub 和明确登记的本地项目。仅本地初始化不需要 owner 或安装 Git：

```bash
python ../../scripts/memoryctl.py init --vault /absolute/path/to/memory --local-only --locale en
python ../../scripts/memoryctl.py local-register --path /absolute/path/to/project --name "My project"
```

从工作区确认用户要管理的项目根目录。已登记项目里的普通子目录无需再次登记。登记由 Agent 明确执行；Hook 不扫描提示词关键词来自动启用。用户明确要求启用当前项目，就已经授权这次登记，不要重复询问同一授权。全局 writable root 等独立设置变更仍遵循初始化规则。

登记返回固定项目 ID、根目录、修改的笔记和完整的适用记忆上下文。立即读取返回内容并在本轮任务使用，不要让用户重启或新开对话才激活已登记的本地项目。当前任务的 Stop 事件会识别新登记并要求记忆检查。登记会留下新建／修改笔记路径的待审查记录，即使登记前没有任务开始快照，也要求可见的逐文件回写审查。其他笔记变更仍依赖可用的常规任务开始快照。

同一会话内需要再次加载记忆时：

```bash
python ../../scripts/memoryctl.py context --cwd /absolute/path/to/project
```

后续提问、压缩和子 agent 会自动使用登记信息。首次安装插件本身，宿主仍可能需要重新加载 Skill 并信任 Hook 定义；项目登记不能绕过安装要求。如果 Hook 尚未加载／信任，先使用返回上下文，并明确执行当前任务的回写检查，再说明剩余宿主设置步骤。

## 身份与目录识别

集成配置的 `local_projects` 保存自动生成的 `project_id: local:<32 lowercase hex digits>`、解析后的绝对路径 `root`、显示名 `name`、开关 `enabled` 和相对知识库的 `project_home`。本地绝对路径不写入共享笔记。每个 ID 对应一个主页，通常为 `20-projects/local-<id>/project.md`，使用 `type: project`、`source_kind: local` 和 `project_id`，不填写 `github_repo`。同名文件夹分配不同 ID，同一路径重复登记则复用原 ID 和笔记。

普通子目录属于最近的已登记根目录。另行登记的嵌套项目覆盖父项目；停用的嵌套项目不会回退到父项目。独立的嵌套 Git 仓库不继承父目录的本地登记。路径规范化会解析符号链接，避免为同一实际目录创建两套身份。不得登记磁盘根目录、用户主目录、知识库本身或包含知识库的上级目录。

在 Git 仓库根目录登记的项目，其分支页使用精确区分大小写的 `working_branch` 和相同 `project_id`，不使用 `github_repo`。只有产生持久分支进度才创建。普通文件夹和 detached HEAD 没有具名当前分支：进度保留在项目主页，不虚构 `main` 或 `detached-head` 页面。

本地登记优先于自动 GitHub 范围，因此后来添加 GitHub origin 不会悄悄改变本地身份。明确的 GitHub 排除项优先于两条入口。已有 GitHub 项目主页时，登记命令拒绝另建一份本地主页。现有 GitHub 身份保持不变。仅本地模式不启用自动 GitHub 识别；混合使用可以保留原 GitHub 配置，再登记指定本地根目录。

## 停止、恢复与迁移

从 `local-list` 获取真实 ID。下面的示例 ID 必须替换成返回的值，不得自行编造。

```bash
python ../../scripts/memoryctl.py local-list
python ../../scripts/memoryctl.py local-disable local:0123456789abcdef0123456789abcdef
python ../../scripts/memoryctl.py local-enable local:0123456789abcdef0123456789abcdef
python ../../scripts/memoryctl.py local-move local:0123456789abcdef0123456789abcdef --path /absolute/path/to/new-location
```

停用本地登记会保留笔记和身份，同时停止自动加载、Stop 检查和参考检索，包括由该来源提炼的共享经验。恢复时返回记忆上下文，可立即使用。`local-move` 只在用户移动项目后更新登记路径，不移动项目文件或知识库笔记。不同目录不能占用已有登记根目录。登记更新通过集成配置旁的短期锁串行执行；中断命令遗留锁时，先检查对应操作，再删除那一个已失效锁文件。

Windows 和 WSL 配置相互独立。另一环境共享同一知识库时，若要沿用同一本地项目身份，用该环境的路径明确关联已有 ID：

```bash
python ../../scripts/memoryctl.py local-register --path /absolute/path/visible/here --project-id local:0123456789abcdef0123456789abcdef
```

该 ID 必须在知识库中恰好对应一个现有项目主页。不能仅凭文件夹同名就猜测是同一项目。不得跨环境复制凭据或整份配置。

## 共享经验与验证

启用的本地项目主页及已链接子页可参与 `search` 和 `read`。结果携带 `project_id`，`repository` 为空。本地来源的共享经验使用 `source_project_id` 替代 `source_repo`，`source_note`、`source_branch` 和 `verified_on` 仍遵循精确来源规则。两种来源身份字段必须且只能填一种。停用来源会让其活跃衍生经验不可检索；验证会报告这些来源问题，直到完成审查或将经验停用。

检查登记是否立即返回全局／项目上下文、当前任务 Stop 是否要求逐文件审查，以及后续提问能否回忆已保存事实。验证本地 Git 的精确分支、无 GitHub 普通文件夹、同名目录、嵌套边界、迁移和停用。运行 `validate`，列出每个修改的知识库文件并邀请纠正。未确认说法留在“开放问题”，不要虚构记忆事实。
