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

For a newly eligible GitHub repository, use `memoryctl.py register-github --cwd <workspace> --review-token <current-turn-token>` through the platform launcher. It creates and links one home under the vault-wide registration lock, so another conversation cannot overwrite the same index at that moment. Review the returned changed notes in the current task.

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

## Explicit local projects

`local-register` creates the project home with a generated `project_id: local:<32 lowercase hex digits>` and `source_kind: local`. Keep that ID; omit `github_repo`, `default_branch` and `upstream_repo` for a plain folder. Store progress on its project home when there is no named Git branch. For a local Git branch page, replace `github_repo` in the branch template with the registered `project_id` and preserve the real `working_branch`. Never invent an ID or a `main` branch. Link child pages from the existing project home. Registration returns context for immediate use in the current conversation.
