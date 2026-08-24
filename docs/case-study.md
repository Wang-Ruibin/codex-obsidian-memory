# Case study: deterministic project memory in Obsidian

[简体中文](zh-CN/case-study.md)

This plugin generalizes and sanitizes a real three-day Codex session that began on 2026-08-21. The source vault started empty except for Obsidian settings and evolved through behavioral tests, user corrections and graph validation.

## Build sequence

1. **Store durable information, not transcripts.** Keep stable preferences, context, decisions, verified outcomes, reusable failures and next steps; reject credentials and raw logs.
2. **Use GitHub as project identity.** An early inventory mistook 23 visible public repositories for the account total. The authorization gap established the rule that current visibility is not proof of completeness.
3. **Keep machine rules outside project memory.** SSH, WSL and sandbox behavior belong to user-level execution guidance.
4. **Replace passive instructions with hooks.** A blind task skipped memory loading, so deterministic handlers were added for `UserPromptSubmit`, post-compaction `SessionStart`, `SubagentStart` and `Stop`.
5. **Organize the graph around repositories.** One GitHub repository owns one folder and one project home; branch progress belongs only to an exact `working_branch` page.
6. **Use exact frontmatter.** Body substring matching caused plausible collisions such as `RAG` and `Agent-RAG`.
7. **Gate by origin, not only the index.** New eligible repositories receive global memory and a template even before registration.
8. **Make routines non-destructive.** Weekly and monthly state advances only after success; audits may recommend archival but never perform it.

## Verified source snapshot

| Invariant | Result |
|---|---:|
| Repository folders / project homes | 25 / 25 |
| Exact branch pages | 26 |
| Visible graph nodes | 60 |
| Lifecycle handlers | 4 |
| Broken links / orphan nodes | 0 / 0 |
| Cross-cluster edges | 1 |

These are case-study results, not promises about another user's vault. Each installation is validated independently.

## Reusable failures

| Failure | Public design response |
|---|---|
| Simple tasks skipped advisory memory instructions | Deterministic lifecycle hooks |
| Visible repositories were called the total | Never infer totals from current authorization coverage |
| Branches became duplicate projects | One repository folder with separate branch pages |
| Body text caused identity collisions | Exact frontmatter fields |
| Indexed-only scope missed new repositories | GitHub origin plus explicit exclusions |
| Old PowerShell lacked `Path.GetRelativePath` | Dependency-free Python validator |

## Deliberately excluded

Private repository contents, credentials, machine-specific execution rules, personal vault pages and fabricated routine results are not packaged. The public project contains fresh templates, configurable paths, deterministic scripts and reusable decisions.
