# 不用 Hook 的记忆方式

[English](../skill-only.md) · [README](../../README.zh-CN.md)

独立的 `codex-obsidian-memory-skill` 是 Hook 插件的另一种选择，包含自身指引、本地脚本和模板。完整复制该文件夹即可使用，不需要已安装的插件或源码仓库。

## 安装与配置

把下面这段发给 Codex：

```text
请用 $skill-installer 安装 Wang-Ruibin/codex-obsidian-memory 中的
skills/codex-obsidian-memory-skill。只安装这个 Skill，保持现有 Hook 集成不变。
验证完整 Skill 文件夹已经可用。
```

若 Skill 选择器里未出现，重启 Codex。也可将完整的 [Skill 文件夹](../../skills/codex-obsidian-memory-skill) 复制到宿主支持的个人或仓库 Skill 目录，脚本、模板和参考资料须保持完整。宿主发现方式及 `$skill-installer` 支持见[官方 Skill 文档](https://learn.chatgpt.com/docs/build-skills)。

然后发送：

```text
请用 $codex-obsidian-memory-skill 配置记忆。先检查状态，必要时准备私有运行时。
帮助我选择知识库位置，以及使用 GitHub 项目还是只使用明确登记的本地项目。
笔记使用简体中文，保留已有知识库，并向我展示配置产生的笔记变化。
```

Codex 会复用兼容的 Python 3.11+ 或准备私有运行时，不修改 PATH、Codex 设置、全局指导、Hook、信任记录或系统任务。只有配置时需要下载解释器才要求联网。纯 Skill 配置独立保存在 `~/.codex/obsidian-memory-skill` 或你的 `CODEX_HOME` 下，初始化不覆盖原笔记。Skill 确认了正确知识库且结构检查健康，即可使用。

## 在项目中使用

可以这样说：

```text
请用 $codex-obsidian-memory-skill 继续这个项目。加载相关记忆，检索可复用经验，
完成工作，并在回复前检查和展示记忆变化。
```

没有 GitHub 的本地目录，需要先明确让 Skill 登记该项目。登记立即生效，保留稳定的本地项目 ID。GitHub 项目使用精确仓库身份与配置范围，已排除仓库保持排除；分支进度只写当前分支页。

Skill 会开始记忆任务、加载当前上下文、检索相关经验，最后完成回写审查。工作中断或上下文压缩后，让它用相同任务 ID 恢复未完成记忆任务，原审查基线会保留。你无需自己维护底层哈希或命令。

笔记有变化时，最终回复按你的语言逐个说明修改文件及具体事实或章节。请核对事实，需要时让它修正。审查命令检查文件覆盖与最低说明要求，不证明事实准确性。

## 记住一个普通对话

普通对话默认不记忆。说“用 $codex-obsidian-memory-skill 记住这个对话”，只为当前对话开启；说“停止记住这个对话”，停止内容加载与保存，保留已有笔记。GitHub 和已登记本地项目记忆保留各自路由。

文件名在 Skill 下次执行或你明确要求同步时跟随界面显示标题变化，改名不会丢失事实。关闭内容记忆后仍可显式更新文件名；如需暂停改名，可以同时要求冻结标题同步。Skill 空闲时没有后台进程。

## 选择或切换版本

Hook 插件自动加载上下文并检查结束前披露；纯 Skill 只在被调用时执行这些步骤，不能强制每次提示或压缩后调用，也不能在未调用时拦截宿主回复。两版共用路由、检索和校验代码；纯 Skill 没有持续标题监听、定时例行任务安装器或目录迁移命令。直接提及 Skill，可明确控制何时运行。

安装 Skill 不会停用或替换现有 Hook 集成。同一任务选择一种方式回写。想切换时，让 Codex 检查两边配置、说明切换内容，并在修改现有安装前取得所需授权。复用已有知识库时显式映射路径，不覆盖模板；关联原本地项目 ID，不重复创建主页。两版分别保留各自环境配置和对话授权状态。

暂停本版时，让它停用自身记忆配置；移除时使用宿主正常 Skill 管理，知识库笔记保留。清理残留任务状态需单独审查。详细命令与笔记字段见 [Skill 参考](../../skills/codex-obsidian-memory-skill/references/zh-CN/usage.md)。
