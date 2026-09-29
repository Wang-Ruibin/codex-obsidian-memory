---
type: system-template
status: active
tags:
  - graph/knowledge
---

# 项目记忆模板

← [[10-memory/maintenance|记忆维护]]

## 项目主页

```markdown
---
type: project
status: tracked
updated: YYYY-MM-DD
github_repo: OWNER/REPOSITORY
source_kind: owned
default_branch: main
upstream_repo:
tags:
  - graph/project
---

# 仓库名称

← [[20-projects/project-index|项目总览]]

## 目标与约束
## 稳定背景
## 开发分支
## 仓库级决策
## 开放问题
```

`source_kind` 使用 `owned` 或 `fork`。

## 分支页

```markdown
---
type: branch
status: tracked
updated: YYYY-MM-DD
github_repo: OWNER/REPOSITORY
working_branch: feature/exact-name
tags:
  - graph/branch
---

# 仓库 / 分支

项目：[[20-projects/repository/repository|项目主页]]

## 目标与约束
## 当前状态
## 决策
## 已完成
## 可复用失败经验
## 下一步
## 开放问题
```

文件名中替换非法字符，但 `working_branch` 必须保留完整 Git 分支名。

## 明确登记的本地项目

`local-register` 创建项目主页，生成 `project_id: local:<32 lowercase hex digits>` 并设置 `source_kind: local`。保留该 ID；普通文件夹不填写 `github_repo`、`default_branch` 和 `upstream_repo`。没有具名 Git 分支时，进度写在项目主页。本地 Git 分支页将上述分支模板中的 `github_repo` 替换为登记的 `project_id`，保留真实 `working_branch`；不得虚构 ID 或 `main` 分支。从已有项目主页链接子页。登记返回的上下文应在当前会话立即使用。
