---
name: codex-obsidian-memory
description: Set up, configure, validate, troubleshoot, enable, disable, or remove the local Codex-to-Obsidian long-term memory integration. Use for lifecycle hooks, GitHub repository scope, vault structure, project and branch routing, and optional weekly or monthly memory routines; ordinary project work is handled automatically by the installed hooks.
---

# Codex Obsidian Memory

Manage the local-first memory integration packaged with this plugin. The lifecycle Hook handles ordinary project tasks without requiring this Skill.

## Choose the operation

- First-time setup: run `python ../../scripts/memoryctl.py init --vault <absolute-vault-path> --github-owner <owner>` from this Skill directory.
- Current state: run `python ../../scripts/memoryctl.py status`.
- Structural check: run `python ../../scripts/memoryctl.py validate`.
- Reversible control: use `enable` or `disable`.
- Complete integration-state removal: uninstall optional automation first, then run `uninstall`. Never remove the vault.
- Repository scope: use `exclude OWNER/REPO` or `include OWNER/REPO`.
- Recurring briefs or audits: read [automation.md](references/automation.md) before installing an OS scheduler.
- Existing vault adoption: read [migration.md](references/migration.md) before changing files.

On Windows, prefer `py.exe` when `python` is unavailable.

## Safety invariants

- Obtain user approval immediately before changing global Codex configuration, creating scheduler entries, or removing integration state.
- Never read, copy, print, or store passwords, private keys, tokens, cookies, or other credentials. Store only paths, GitHub repository names, and memory policy.
- Do not delete or move an existing vault during setup, disable, or plugin removal. Template installation is additive unless the user explicitly requests `--force-template` after reviewing conflicts.
- For an existing non-default layout, use `--no-template` plus repeatable `--path KEY=RELATIVE_PATH` mappings. Validate before enabling ordinary work.
- Keep one repository folder and one project home per GitHub repository. Put branch-specific progress only in a same-folder page whose `working_branch` exactly matches the current Git branch.
- Treat unresolved claims as open questions. Do not convert guesses, raw chat logs, or one-off debugging output into durable memory.
- The Hook must be silent outside configured GitHub scope. The vault itself is the only maintenance exception.

## Setup outcome

After `init`:

1. Review configuration and vault paths with `status`.
2. Open `/hooks`, review the plugin commands, and trust them.
3. Start a new thread inside one configured GitHub repository.
4. Verify that global memory plus the exact repository and branch pages load.
5. Run `validate` and keep zero broken links, duplicate repository homes, and duplicate branch identities.

Read [structure.md](references/structure.md) when changing the graph model or note schema. Read [security.md](references/security.md) when reviewing trust, writable roots, or credential boundaries.
