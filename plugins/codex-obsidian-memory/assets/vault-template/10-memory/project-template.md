---
type: system-template
status: active
tags:
  - graph/knowledge
---

# Project memory template / 项目记忆模板

← [[10-memory/maintenance|Memory maintenance / 记忆维护]]

## Project home / 项目主页

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

# Repository name / 仓库名称

← [[20-projects/project-index|Project index / 项目总览]]

## Goal and constraints / 目标与约束
## Stable context / 稳定背景
## Development branches / 开发分支
## Repository-level decisions / 仓库级决策
## Open questions / 开放问题
```

Use `source_kind: owned` or `fork`. / `source_kind` 使用 `owned` 或 `fork`。

## Branch page / 分支页

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

# Repository / branch / 仓库 / 分支

Project / 项目: [[20-projects/repository/repository|Project home / 项目主页]]

## Goal and constraints / 目标与约束
## Current state / 当前状态
## Decisions / 决策
## Completed / 已完成
## Reusable failure lessons / 可复用失败经验
## Next steps / 下一步
## Open questions / 开放问题
```

Sanitize filename-invalid characters, but preserve the full Git branch in `working_branch`.

文件名中替换非法字符，但 `working_branch` 必须保留完整 Git 分支名。
