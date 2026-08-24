<div align="center">

# Codex Obsidian Memory

**面向 Codex 的本地优先、分支感知长期记忆，由 Obsidian 组织。**

[English](README.md) · [构建案例](docs/case-study.md) · [安全策略](SECURITY.md)

</div>

它把普通 Markdown 知识库变成可持续的项目上下文：任务开始前自动加载，压缩后与子 agent 启动时重新加载，结束前只沉淀真正值得跨会话保留的内容。

不需要向量数据库，不依赖云端记忆服务，也不应把凭据写入知识库。

> [!IMPORTANT]
> 当前是早期公开版本。迁移现有知识库前请先备份，并在 `/hooks` 中逐条审阅 Hook 后再信任。

## 核心特点

- 本地优先：记忆保存在你拥有的 Markdown 文件中。
- 精确准入：根据 GitHub `origin` 判断范围，普通目录不触发。
- 分支隔离：只加载 `working_branch` 与当前 checkout 精确匹配的页面。
- 图谱清晰：一个仓库一个文件夹和主页，不同分支使用同目录独立页面。
- 内容克制：只保存稳定目标、决策、结果、可复用失败经验和下一步。
- 可逆：停用或卸载不会删除知识库。
- 轻依赖：运行代码只使用 Python 标准库。

## 快速开始

要求：Codex CLI 或 ChatGPT 桌面端中的 Codex、Python 3.11+、带 GitHub `origin` 的 Git 仓库。Obsidian 用于浏览和编辑，但运行时处理的是普通 Markdown。

```bash
codex plugin marketplace add Wang-Ruibin/codex-obsidian-memory
codex plugin add codex-obsidian-memory@codex-obsidian-memory
```

安装后新开一个会话，并输入：

```text
使用 $codex-obsidian-memory，在 D:\path\to\memory 初始化知识库，
GitHub owner 是 my-account。
```

然后打开 `/hooks`，审阅并信任四个生命周期 Hook；进入一个符合范围的 GitHub 仓库新开会话，运行 `$codex-obsidian-memory status` 和 `$codex-obsidian-memory validate`。

## 记忆模型

```text
知识库首页 ── 全局记忆 / 维护 / 模板
    │
    └── 项目总览 ── 仓库主页 ── 精确分支页
```

默认只保留一条“知识库首页—项目总览”跨簇桥。仓库级稳定事实写项目主页，分支进度只写当前精确分支页；未知信息进入“开放问题”，不写成事实。

## 安全与卸载

- Hook 只执行只读 Git 身份命令，并限制笔记路径不能逃逸知识库根目录。
- 注入前再次遮蔽常见令牌与私钥模式。
- `uninstall` 只删除集成状态和由本插件添加的 writable root，不删除或移动知识库。
- 完全移除插件：

```bash
codex plugin remove codex-obsidian-memory@codex-obsidian-memory
```

现有知识库迁移、自定义路径、周报/月检自动化、架构和开发说明请查看[英文 README](README.md)。三天完整构建过程、纠错与最终指标见[构建案例](docs/case-study.md)。

## 许可证

[MIT](LICENSE)
