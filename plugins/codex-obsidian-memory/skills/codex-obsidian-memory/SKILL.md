---
name: codex-obsidian-memory
description: Set up, validate, troubleshoot, enable, disable, or remove local Codex-to-Obsidian memory, including lifecycle hooks, GitHub scope, vault routing, locale templates, and optional routines; ordinary project work is handled automatically by installed hooks.
---

# Codex Obsidian Memory

Simplified Chinese translation: [SKILL.zh-CN.md](SKILL.zh-CN.md).

Manage the local-first memory integration packaged with this plugin. Lifecycle hooks handle ordinary project tasks without explicit Skill invocation.

## Choose the operation

- First-time setup: run `python ../../scripts/memoryctl.py init --vault <absolute-path> --github-owner <owner> [--locale en|zh-CN]` from this Skill directory.
- Current state: run `python ../../scripts/memoryctl.py status`.
- Structural check: run `python ../../scripts/memoryctl.py validate`.
- Reversible control: use `enable` or `disable`.
- Active integration removal: uninstall optional automation first, then run `uninstall`. Never remove the vault. Explain that routine history, logs or interrupted-turn snapshots may remain under `$CODEX_HOME/obsidian-memory`.
- Repository scope: use `exclude OWNER/REPO` or `include OWNER/REPO`.
- Recurring briefs or audits: read [automation.md](references/automation.md) before installing an OS scheduler.
- Existing vault adoption: read [migration.md](references/migration.md) before changing files.

On Windows, prefer `py.exe` when `python` is unavailable.

## Safety invariants

- Obtain approval immediately before changing global Codex configuration, creating scheduler entries, or removing integration state.
- Never read, copy, print or store passwords, private keys, tokens, cookies or other credentials.
- Never delete or move a vault. Template installation is additive unless the user explicitly approves `--force-template` after reviewing conflicts.
- For a non-default existing layout, use `--no-template` plus repeatable `--path KEY=RELATIVE_PATH` mappings, then validate.
- Keep one folder and one project home per GitHub repository. Create a branch page only for durable branch-specific progress. Version 0.4.0 compares `working_branch` case-insensitively, so warn about branch names that differ only by case.
- Treat unresolved claims as open questions; do not retain guesses, transcripts or one-off output.
- Hooks must stay silent outside configured GitHub scope. The vault itself is the only maintenance exception.
- After any vault Markdown write, the final reply must contain a visible **Knowledge-base writeback review** section listing every changed file and the concrete facts or sections added, changed or removed. Invite corrections, then append the disclosure marker. The Stop hook verifies the heading and markers, not the semantic completeness of the list. Do not show the section when nothing was written.

## Setup outcome

After `init`:

1. Review configuration, locale and vault paths with `status`.
2. Open `/hooks`, review the commands, and trust them.
3. Start a new thread inside one configured GitHub repository.
4. Verify that global memory, the matching repository home and any existing matching branch page load.
5. Run `validate` and keep broken links, duplicate project homes and duplicate branch identities at zero.

Read [structure.md](references/structure.md) for graph or schema changes and [security.md](references/security.md) for trust, writable-root or credential reviews.
