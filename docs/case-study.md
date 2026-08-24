# Case study / 案例：在 Obsidian 中构建确定性项目记忆

## English

This plugin is a generalized, sanitized package of a real three-day Codex session that began on 2026-08-21. The source vault started empty except for Obsidian settings and evolved through repeated behavioral tests, user corrections and graph validation.

## The build sequence

### 1. Start with durable information, not a transcript

The first vault separated stable preferences, project context, decisions, completed work, reusable failures and next steps. It explicitly rejected credentials, small talk, raw logs and one-off debugging details.

### 2. Use GitHub as project identity

Repositories and branches came from GitHub facts rather than folder-name guesses. An early inventory incorrectly treated 23 publicly visible repositories as the account total. The user identified a total of 26; the difference was a private-repository authorization gap. The lasting rule is therefore:

> Current visibility is not proof of account completeness.

The public plugin never assumes an account total. It scopes by exact `OWNER/REPO`, explicit inclusions and exclusions.

### 3. Keep machine rules outside the vault

SSH, WSL and sandbox behavior were moved to user-level Codex guidance rather than duplicated in project memory. The reusable principle is that machine execution policy and project knowledge have different lifecycles and should not share a fact source.

### 4. Replace passive instructions with lifecycle hooks

A blind test asked a new session to inspect an unrelated empty directory. Text guidance alone did not reliably cause it to load Obsidian memory. Deterministic hooks were then installed for:

- `UserPromptSubmit`
- `SessionStart` after compaction
- `SubagentStart`
- `Stop`

The first three inject scoped context. The Stop hook requires a durable-memory review but permits no-op completion when nothing worth retaining changed.

### 5. Rebuild the graph around repositories

The initial flat index created too many management nodes. The graph was redesigned into two clusters:

```text
knowledge cluster                      project cluster

home ─ maintenance ─ template    home ─ project index ─ repository home ─ branch
  └──── global memory             └──────── one intentional bridge ────────┘
```

The model later received an important correction: multiple branches of one repository must not become separate project folders. The final identity rules became:

- one GitHub repository → one folder and one project home;
- one working branch → one same-folder `type: branch` page;
- repository-wide stable facts → project home;
- branch progress → only the exact `working_branch` page.

### 6. Replace substring routing with exact frontmatter

Substring matching caused plausible collisions such as `RAG` versus `Agent-RAG` and could mix branch descriptions. Project homes now require exact `github_repo` frontmatter, while branch pages require exact `working_branch` frontmatter.

### 7. Scope by origin, not only by the current index

An indexed-only gate excluded ordinary folders but also missed newly uploaded repositories. The corrected rule admits an exact configured GitHub owner or explicit repository even when no project page exists yet. A new eligible repository receives global memory and the template, then gets registered only if the task produces durable context.

Local-only repositories, other Git hosts, other owners and explicit exclusions stay silent. The vault itself is the sole maintenance exception.

### 8. Add non-destructive routines

The final system added a weekly kickoff brief and monthly knowledge audit. Daily scheduler triggers provide catch-up behavior, while successful ISO week or calendar month keys prevent duplicate runs. Failures never advance the key. Monthly audits may recommend archival, but never delete, move or archive files automatically.

## Verified snapshot

At the end of the source build on 2026-08-22, the vault reported:

| Invariant | Result |
|---|---:|
| Tracked repository folders | 25 |
| Project homes | 25 |
| Exact branch pages | 26 |
| Visible graph nodes | 60 |
| Lifecycle hook handlers | 4 |
| Broken Wiki links | 0 |
| Orphan nodes | 0 |
| Cross-cluster edges | 1 |

The scheduled-task actions also completed empty-period checks successfully, and the non-interactive Codex path was exercised end to end.

These are case-study results, not promises about another user's vault. The public validator measures each installation independently.

## Failed approaches that shaped the plugin

| Failure | Cause | Public design response |
|---|---|---|
| A simple task skipped memory loading | Instructions were advisory | Use lifecycle hooks for deterministic injection |
| Public repository count was called the total | Authorization coverage was incomplete | Never infer totals from current visibility |
| Branches became duplicate projects | Folder identity followed branch identity | One repository folder; separate branch pages |
| `RAG` could collide with `Agent-RAG` | Body substring matching | Exact frontmatter identity |
| New uploaded repositories were ignored | Scope depended on an existing index | Gate on GitHub origin plus exclusions |
| Graph validation failed on old PowerShell/.NET | `Path.GetRelativePath` was unavailable | Use a dependency-free Python validator |
| A scheduler flag combination was incompatible | CLI flags were not tested together | Exercise the actual non-interactive command path |

## What was deliberately not packaged

- private repository names or contents;
- SSH keys, tokens, cookies or API credentials;
- machine-specific WSL, proxy or sandbox rules;
- the user's personal vault pages;
- fabricated report results for periods that had not run.

The public repository contains a fresh template, configurable paths, deterministic scripts and the reusable decisions behind them.

---

## 中文

本插件是一次真实三天 Codex 会话的通用化、脱敏包装。该会话始于 2026-08-21：源知识库最初除 Obsidian 配置外为空，随后通过行为测试、用户纠错和图谱验证逐步形成完整系统。

### 构建过程

#### 1. 从持久信息开始，而不是保存对话流水账

第一版知识库区分稳定偏好、项目上下文、决策、已完成工作、可复用失败经验和下一步；同时明确拒绝凭据、寒暄、原始日志和一次性调试细节。

#### 2. 使用 GitHub 作为项目身份

仓库和分支身份来自 GitHub 事实，而不是文件夹名称猜测。早期清单错误地把当前可见的 23 个公开仓库当作账号总数；用户指出总数为 26，差额来自 private 仓库授权缺口。因此形成了长期规则：

> 当前可见范围不能证明账号完整范围。

公开插件不会假设账号仓库总数，只按精确 `OWNER/REPO`、显式包含和显式排除决定范围。

#### 3. 将本机规则留在知识库之外

SSH、WSL 和沙箱行为被移到用户级 Codex 指引中，不再复制到项目记忆。可复用原则是：机器执行策略和项目知识具有不同生命周期，不应共享同一事实来源。

#### 4. 用生命周期 Hook 替代被动文字指令

一次盲测要求新会话检查无关空目录，结果证明文字指引不能稳定触发 Obsidian 记忆加载。随后安装四类确定性 Hook：

- `UserPromptSubmit`
- 上下文压缩后的 `SessionStart`
- `SubagentStart`
- `Stop`

前三类注入精确范围的上下文；Stop Hook 要求执行持久记忆检查，但当任务没有值得保留的变化时允许不写入。

#### 5. 围绕仓库重建图谱

最初的扁平索引产生了过多管理节点。图谱随后重构为两个簇：

```text
知识簇                                 项目簇

首页 ─ 维护 ─ 模板              首页 ─ 项目总览 ─ 仓库主页 ─ 分支
  └──── 全局记忆                  └──────── 唯一跨簇桥 ────────┘
```

之后又纠正了一项重要结构问题：同一仓库的多个分支不能成为多个项目文件夹。最终身份规则为：

- 一个 GitHub 仓库对应一个文件夹和一个项目主页；
- 一个 working branch 对应一个同文件夹 `type: branch` 页面；
- 仓库级稳定事实写项目主页；
- 分支进度只写精确 `working_branch` 页面。

#### 6. 用精确 frontmatter 替代正文子串路由

正文子串匹配会产生 `RAG` 与 `Agent-RAG` 等合理碰撞，也可能混入其他分支说明。项目主页现在要求精确 `github_repo` frontmatter，分支页要求精确 `working_branch` frontmatter。

#### 7. 按 origin 准入，而不仅按现有索引准入

“仅已登记仓库”能够排除普通文件夹，却会漏掉刚上传的新仓库。修正后的规则允许配置 GitHub owner 下的精确 origin 或显式仓库，即使项目页尚不存在。新的合格仓库会获得全局记忆和模板，并仅在任务产生持久上下文时登记。

本地仓库、其他 Git 平台、其他 owner 和显式排除项保持静默；知识库自身是唯一维护例外。

#### 8. 增加非破坏性周期任务

最终系统增加每周开工简报和每月知识体检。每日调度触发提供错过后的补跑能力，成功的 ISO 周或日历月状态防止重复运行；失败永远不推进状态。月检只能建议归档，不能自动删除、移动或归档文件。

### 已验证快照

2026-08-22 源系统构建结束时，知识库结果为：

| 不变量 | 结果 |
|---|---:|
| 已跟踪仓库文件夹 | 25 |
| 项目主页 | 25 |
| 精确分支页 | 26 |
| 可见图谱节点 | 60 |
| 生命周期 Hook 处理器 | 4 |
| Wiki 断链 | 0 |
| 孤立节点 | 0 |
| 跨簇边 | 1 |

计划任务空周期检查成功完成，非交互 Codex 路径也完成端到端测试。

这些是案例结果，不是对其他用户知识库的承诺。公开验证器会独立测量每次安装。

### 塑造插件的失败方案

| 失败 | 原因 | 公开版设计响应 |
|---|---|---|
| 简单任务跳过记忆加载 | 文字指令只是建议 | 使用生命周期 Hook 确定性注入 |
| 把公开仓库数称为总数 | 授权覆盖不完整 | 不从当前可见范围推断总数 |
| 分支成为重复项目 | 文件夹身份跟随分支身份 | 一个仓库文件夹，分支使用独立页面 |
| `RAG` 与 `Agent-RAG` 可能碰撞 | 正文子串匹配 | 使用精确 frontmatter 身份 |
| 新上传仓库被忽略 | 范围依赖现有索引 | 使用 GitHub origin 与排除表准入 |
| 旧 PowerShell/.NET 图谱验证失败 | 缺少 `Path.GetRelativePath` | 使用无依赖 Python 验证器 |
| 计划任务参数组合不兼容 | CLI 参数没有一起实测 | 执行真实非交互命令路径 |

### 明确没有打包的内容

- private 仓库名称或内容；
- SSH 密钥、令牌、Cookie 或 API 凭据；
- 本机特有的 WSL、代理或沙箱规则；
- 用户个人知识库页面；
- 尚未运行周期的虚构报告结果。

公开仓库只包含新模板、可配置路径、确定性脚本，以及这些设计背后的可复用决策。
