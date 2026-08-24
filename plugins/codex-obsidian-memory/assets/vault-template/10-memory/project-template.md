---
type: system-template
status: active
tags:
  - graph/knowledge
---

# Project memory template

← [[10-memory/maintenance|Memory maintenance]]

## Project home

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

# Repository name

← [[20-projects/project-index|Project index]]

## Goal and constraints
## Stable context
## Development branches
## Repository-level decisions
## Open questions
```

Use `source_kind: owned` or `fork`.

## Branch page

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

# Repository / branch

Project: [[20-projects/repository/repository|Project home]]

## Goal and constraints
## Current state
## Decisions
## Completed
## Reusable failure lessons
## Next steps
## Open questions
```

Sanitize filename-invalid characters, but preserve the full Git branch in `working_branch`.
