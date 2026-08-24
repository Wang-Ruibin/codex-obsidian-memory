# Vault structure

Use this reference when changing note paths, graph routing, project identity, or branch behavior.

```text
00-memory-home
├── 10-memory/global-memory
├── 10-memory/maintenance
│   └── 10-memory/project-template
└── 20-projects/project-index
    └── 20-projects/<repository>/<repository>
        ├── <branch-page>
        └── optional decision, failure, or milestone pages
```

The knowledge cluster and project cluster have one intentional bridge: memory home to project index. Project facts do not live in the knowledge cluster.

## Identity rules

- A project home has `type: project` and an exact `github_repo: OWNER/REPO` field.
- One repository maps to one folder and one project home.
- A branch page has `type: branch`, the same `github_repo`, and an exact `working_branch`.
- Branch filenames may sanitize path separators, but `working_branch` must preserve the original Git name.
- The project home directly links every branch and repository-level child page.

Keep stable goals, constraints, background, decisions with rationale, verified outcomes, reusable failure lessons, blockers, and concrete next steps. Do not keep chat transcripts, raw command output, facts available directly from code, or secrets.
