---
name: codex-obsidian-memory
description: Set up, validate, troubleshoot, enable, disable, or remove Codex-to-Obsidian memory. Use when a user asks to remember or enable long-term memory for this local project without GitHub, immediately in the current conversation, or to manage GitHub scope, vault routing, hooks and routines; ordinary registered-project work is automatic.
---

# Codex Obsidian Memory

Simplified Chinese translation: [SKILL.zh-CN.md](SKILL.zh-CN.md).

Manage the local-first memory integration packaged with this plugin. Lifecycle hooks handle ordinary project tasks without explicit Skill invocation.

## Choose the operation

- First-time setup: run `python ../../scripts/memoryctl.py init --vault <absolute-path> --github-owner <owner> [--locale en|zh-CN]` from this Skill directory.
- Without GitHub: use `init --vault <absolute-path> --local-only [--locale en|zh-CN]`. Existing installations do not need reinitialization to add local projects.
- Explicitly enable the current local project: read [local-projects.md](references/local-projects.md), then use `local-register --path <confirmed-root>`. Immediately consume the returned memory context in this task and perform the current task's writeback review. Do not defer activation to a new conversation. Mentioning memory without asking to enable it does not authorize registration.
- Local controls: use `local-list`, `local-disable <id>`, `local-enable <id>` and `local-move <id> --path <new-root>`; preserve the generated ID and notes. `context --cwd <workspace>` reloads memory in the same conversation.
- Current state: run `python ../../scripts/memoryctl.py status`.
- Structural check: run `python ../../scripts/memoryctl.py validate`.
- Reversible control: use `enable` or `disable`.
- Active integration removal: uninstall optional automation first, then run `uninstall`. Never remove the vault. Explain that routine history, logs or interrupted-turn snapshots may remain under `$CODEX_HOME/obsidian-memory`.
- Repository scope: use `exclude OWNER/REPO` or `include OWNER/REPO`.
- Recurring briefs or audits: read [automation.md](references/automation.md) before installing an OS scheduler.
- Existing vault adoption: read [migration.md](references/migration.md) before changing files.

On Windows, prefer `py.exe` when `python` is unavailable.

## Cross-project experience reuse

Before substantial implementation, after failure or before changing strategy, search shared lessons first, falling back to eligible project notes; explicitly search projects when shared candidates do not apply. Use `search` and `read` on demand, check conditions and provenance, and treat historical branches as references only. Read [reuse.md](references/reuse.md) when retrieving or distilling verified lessons, adapting older vaults or handling conflicts.

## Safety invariants

- Obtain approval immediately before changing global Codex configuration, creating scheduler entries, or removing integration state.
- Never read, copy, print or store passwords, private keys, tokens, cookies or other credentials.
- Never delete or move a vault. Template installation is additive unless the user explicitly approves `--force-template` after reviewing conflicts.
- For a non-default existing layout, use `--no-template` plus repeatable `--path KEY=RELATIVE_PATH` mappings, then validate.
- Keep one folder and one project home per GitHub repository. Create a branch page only for durable branch-specific progress. Match `working_branch` case-sensitively and `github_repo` case-insensitively. Use distinct filenames for branches such as `Release` and `release` on case-insensitive filesystems.
- Treat unresolved claims as open questions; do not retain guesses, transcripts or one-off output.
- Hooks must stay silent outside configured GitHub scope and explicitly enabled local roots. Local projects use a stable `project_id`, not a fabricated `github_repo`. No named Git branch means progress belongs on the project home. The vault itself is the maintenance exception; explicit GitHub exclusions still apply.
- After any vault Markdown write, the final reply must contain a visible **Knowledge-base writeback review** section. Use one bullet per changed file with its vault-relative path and the concrete facts or sections added, changed or removed. A basename is accepted only when unique across the vault and changed files. Invite corrections, then append the disclosure marker followed by the review marker. The Stop hook checks file coverage and minimum descriptions, including on retries; it cannot verify factual accuracy or exhaustive semantics. Do not hide entries in quotes, comments or code fences. Do not show the section when nothing was written.

## Setup outcome

After `init`:

1. Review configuration, locale and vault paths with `status`.
2. Open `/hooks`, review the commands, and trust them.
3. Open an eligible GitHub repository or explicitly register a local project. Registration loads memory in the current conversation; use a later new conversation to verify persistence.
4. Verify that global memory, the matching repository home and any existing matching branch page load.
5. Run `validate` and keep broken links, duplicate project homes and duplicate branch identities at zero.

Read [structure.md](references/structure.md) for graph or schema changes and [security.md](references/security.md) for trust, writable-root or credential reviews.
