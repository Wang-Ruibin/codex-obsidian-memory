# Case study: building deterministic project memory in Obsidian

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
