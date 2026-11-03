---
name: codex-obsidian-memory
description: Set up, validate, troubleshoot or manage Codex-to-Obsidian memory; explicitly enable or disable memory for one ordinary conversation, register a local project, reorganize vault areas, or manage GitHub scope and hooks. Registered project memory is automatic; ordinary conversation memory defaults off.
---

# Codex Obsidian Memory

Simplified Chinese translation: [SKILL.zh-CN.md](SKILL.zh-CN.md).

Manage the local-first memory integration packaged with this plugin. Lifecycle hooks handle ordinary project tasks without explicit Skill invocation.

This is the Hook edition. Users who want a standalone Skill can choose the separate `skills/codex-obsidian-memory-skill` distribution described in the repository README. It uses explicit task start/finish calls and its own profile. Do not install it over an existing Hook setup unless the user requests that switch.

## Choose the operation

- Before setup, automatically run `sh ../../scripts/memoryctl.sh prepare-runtime` on macOS/Linux, or `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action prepare-runtime` on Windows. Reuse a compatible Python or prepare the plugin's private runtime. Do not ask the user to install Python/pip or configure PATH. See [runtime.md](references/runtime.md) for supported platforms and troubleshooting.
- Run commands through `sh ../../scripts/memoryctl.sh <command> <args>` or Windows `powershell.exe -NoProfile -ExecutionPolicy Bypass -File ../../scripts/memoryctl.ps1 -Action <command> <args>`. First-time setup uses `init --vault <absolute-path> --github-owner <owner> [--locale en|zh-CN]`.
- Without GitHub: use `init --vault <absolute-path> --local-only [--locale en|zh-CN]`. Existing installations do not need reinitialization to add local projects.
- Explicitly enable the current local project: read [local-projects.md](references/local-projects.md), then use `local-register --path <confirmed-root>`. Immediately consume the returned memory context in this task and perform the current task's writeback review. Do not defer activation to a new conversation. Mentioning memory without asking to enable it does not authorize registration.
- Local controls: use `local-list`, `local-disable <id>`, `local-enable <id>` and `local-move <id> --path <new-root>`; preserve the generated ID and notes. `context --cwd <workspace>` reloads memory in the same conversation.
- Current state: run the launcher with `status`.
- Structural check: run the launcher with `validate`.
- Reversible control: use `enable` or `disable`.
- Active integration removal: uninstall optional automation first, then run `uninstall`. Never remove the vault. Explain that routine history, logs or interrupted-turn snapshots may remain under `$CODEX_HOME/obsidian-memory`.
- Repository scope: use `exclude OWNER/REPO` or `include OWNER/REPO`.
- For a newly eligible GitHub repository, use `register-github --cwd <workspace> --review-token <current-turn-token>` to create its home and project-index link under the shared vault lock. Its initial turn reviews the returned note paths. Avoid editing the index by hand when registering a repository during concurrent work.
- Recurring briefs or audits: read [automation.md](references/automation.md) before installing an OS scheduler.
- Existing vault adoption: read [migration.md](references/migration.md) before changing files.

Source-level Python examples in references are developer equivalents. For users, use the platform launcher above, including for local registration, search, read and context. Hooks use the same prepared runtime and never download it. After a Hook definition update, review its new launcher command through the host's normal Hook trust flow; do not copy or fabricate trust hashes.

## Ordinary conversations and root layout

Read [conversations.md](references/conversations.md) when the user explicitly asks to remember or stop remembering this ordinary chat. Use its actual session ID with conversation-enable/disable; consume the returned context immediately. Preserve existing local project registrations. Do not enable chats by scanning prompt keywords. Read [migration.md](references/migration.md) for an authorized root-layout move; show the dry-run plan, preserve affected notes, then apply with the current review token and validate. New defaults are 30-reusable and 40-conversations, separate from knowledge and projects.

## Cross-project experience reuse

Before substantial implementation, after failure or before changing strategy, search shared lessons first, falling back to eligible project notes; explicitly search projects when shared candidates do not apply. Use `search` and `read` on demand, check conditions and provenance, and treat historical branches as references only. Read [reuse.md](references/reuse.md) when retrieving or distilling verified lessons, adapting older vaults or handling conflicts.

## Safety invariants

- Obtain approval immediately before changing global Codex configuration, creating scheduler entries, or removing integration state.
- Never read, copy, print or store passwords, private keys, tokens, cookies or other credentials.
- Never delete or move a vault. Template installation is additive unless the user explicitly approves `--force-template` after reviewing conflicts.
- For a non-default existing layout, use `--no-template` plus repeatable `--path KEY=RELATIVE_PATH` mappings, then validate.
- Keep one folder and one project home per GitHub repository. Create a branch page only for durable branch-specific progress. Match `working_branch` case-sensitively and `github_repo` case-insensitively. Use distinct filenames for branches such as `Release` and `release` on case-insensitive filesystems.
- Treat unresolved claims as open questions; do not retain guesses, transcripts or one-off output.
- Hooks must stay silent outside configured GitHub scope, explicitly enabled local roots and opted-in conversation IDs. Local projects use a stable `project_id`, not a fabricated `github_repo`. No named Git branch means progress belongs on the project home. The vault itself is the maintenance exception; explicit GitHub exclusions still apply.
- Concurrent project conversations review only their own project folder. Before editing global memory or a shared lesson from a project conversation, run `claim-shared <vault-relative-path> --review-token <token-from-current-hook> --cwd <workspace>` through the launcher. If another conversation owns the note, defer that shared write. Do not edit unclaimed shared pages from a project conversation. If two conversations need to edit the same project note, coordinate their writes; file hashes do not merge text.
- After any vault Markdown write, the final reply must contain a visible **Knowledge-base writeback review** section. Use one bullet per changed file with its vault-relative path and the concrete facts or sections added, changed or removed. A basename is accepted only when unique across the vault and changed files. Invite corrections, then append the disclosure marker followed by the review marker. The Stop hook checks file coverage and minimum descriptions, including on retries; it cannot verify factual accuracy or exhaustive semantics. Do not hide entries in quotes, comments or code fences. Do not show the section when nothing was written.

## Setup outcome

After `init`:

1. Review configuration, locale and vault paths with `status`.
2. Open `/hooks`, review the commands, and trust them.
3. Open an eligible GitHub repository or explicitly register a local project. Registration loads memory in the current conversation; use a later new conversation to verify persistence.
4. Verify that global memory, the matching repository home and any existing matching branch page load.
5. Run `validate` and keep broken links, duplicate project homes and duplicate branch identities at zero.

Read [structure.md](references/structure.md) for graph or schema changes and [security.md](references/security.md) for trust, writable-root or credential reviews.
