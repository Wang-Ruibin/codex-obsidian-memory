# Vault structure

[简体中文](zh-CN/structure.md)

Use this reference when changing note paths, graph routing, project identity or branch behavior.

```text
00-memory-home
├── 10-memory/global-memory
├── 10-memory/maintenance
│   └── 10-memory/project-template
└── 20-projects/project-index
    └── 20-projects/<repository>/<repository>
        ├── <branch-page>
        └── optional decision, failure or milestone pages
```

The knowledge and project clusters have one intentional bridge: memory home to project index.

## Identity rules

- A project home has `type: project` and exact `github_repo: OWNER/REPO`.
- One repository maps to one folder and one project home.
- A branch page has `type: branch`, the same `github_repo`, and an exact, case-sensitive `working_branch`. `Release` and `release` are different identities; two pages with the same repository and exact branch remain duplicates. Use distinct filenames such as `release-upper.md` and `release-lower.md` on case-insensitive filesystems; filenames do not determine branch identity.
- Filenames may sanitize path separators, but `working_branch` preserves the Git name.
- Create a branch page only when durable branch-specific context exists; empty pages are not required for every checkout.
- The project home directly links every branch and repository-level child page.

Keep stable goals, constraints, background, reasoned decisions, verified outcomes, reusable failures, blockers and concrete next steps. Do not keep transcripts, raw output, facts directly available from code, or secrets.
