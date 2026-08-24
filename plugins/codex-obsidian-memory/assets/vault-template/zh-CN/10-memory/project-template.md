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
