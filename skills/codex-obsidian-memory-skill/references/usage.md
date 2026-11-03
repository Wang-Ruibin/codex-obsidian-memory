# Standalone memory commands

[简体中文](zh-CN/usage.md)

Use commands through `sh scripts/skillctl.sh` or `powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/skillctl.ps1 -Action` from this Skill folder. Examples below use the shell launcher; Windows uses the same arguments after `-Action`. Paths such as `/absolute/project` are placeholders to resolve with the user. Python helpers need only Python 3.11+ and the standard library.

## Setup and existing notes

```bash
sh scripts/skillctl.sh prepare-runtime
sh scripts/skillctl.sh status
sh scripts/skillctl.sh init --vault /absolute/vault --github-owner Example --locale en
sh scripts/skillctl.sh validate
```

Choose `--local-only` instead of `--github-owner` for local projects without GitHub. Installation alone does not create a vault. Setup templates are additive and never overwrite existing files. Custom layouts require `--no-template` and explicit mappings, for example `--path projects_dir=20-Projects --path project_index=20-Projects/index.md`. Keep all mapped paths relative, non-overlapping and inside the vault. `status` identifies the configured paths; never initialize a configured profile again.

The Skill writes its own profile and task hashes under `$CODEX_HOME/obsidian-memory-skill`. It does not change `config.toml`, global `AGENTS.md`, Hook definitions/trust, OS schedulers or another client's settings. The runtime is prepared only on request; ordinary commands do not download code. `CODEX_OBSIDIAN_SKILL_CONFIG` and `CODEX_OBSIDIAN_SKILL_RUNTIME_DIR` are optional isolation overrides for tests or managed deployments, not required user setup.

An existing Hook vault can be reused with `--no-template` and matching paths, while its Hook config remains separate. Attach existing local project identities with `local-register --project-id <existing-id> --path <root>`; do not invent a new identity for the same project. Do not copy credentials or trust records. Stop using one edition before letting the other write the same task; merely installing the Skill does not disable existing Hooks. Switching or uninstalling the Hook edition is a separate explicit request. This Skill never installs itself over that edition.

## Task lifecycle and review

```bash
sh scripts/skillctl.sh start --cwd /absolute/project
sh scripts/skillctl.sh start --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh register-github --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh search "SQLite Windows rename" --cwd /absolute/project
sh scripts/skillctl.sh search "SQLite Windows rename" --scope projects --cwd /absolute/project
sh scripts/skillctl.sh read 20-projects/example/main.md --start-line 12 --line-count 40 --cwd /absolute/project
sh scripts/skillctl.sh claim-shared 30-reusable/topic.md --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh changes --task-id TASK_ID --cwd /absolute/project
sh scripts/skillctl.sh finish --task-id TASK_ID --cwd /absolute/project --review-file /absolute/review.md
```

Replace `TASK_ID` with `start`'s value. Commands use `CODEX_THREAD_ID` or the actual ID supplied with `--session-id`; the session, workspace, vault, project identity and branch must match the saved task. `start` resumes an unfinished task in that session and workspace, preserving the original hashes. After a branch change, finish the original task from its original branch rather than silently replacing its review scope. A new task begins after the previous task finishes. Without changes, omit `--review-file`.

`changes` merges only the current project folder, claimed shared pages and explicit setup/registration/title-sync receipts. Other projects' concurrent edits are not this task's audit. Vault maintenance intentionally covers the whole vault; avoid concurrent maintenance. Claims use the shared vault's leases so Hook and Skill writers cannot reserve the same shared note. Coordinate edits to the same project file separately. The metadata contains paths, identities and hashes, not note bodies. Old snapshots can expire after seven days; missing baselines fail explicitly instead of claiming a review succeeded.

The UTF-8 review draft contains a visible “Knowledge-base writeback review” or “知识库回写审查” heading, followed by one bullet per changed path and concrete facts or sections changed. The final reply must show that review and invite corrections. `finish` refuses missing paths and vague summaries, retains failed reviews for retry, and releases only its own claims when successful. It checks neither truth nor semantic completeness. It is an explicit command, not a host Stop gate. Delete the temporary draft afterwards; no hidden review markers are required.

## Project controls and note fields

```bash
sh scripts/skillctl.sh local-register --path /absolute/local-project --name Example
sh scripts/skillctl.sh local-list
sh scripts/skillctl.sh local-disable LOCAL_ID
sh scripts/skillctl.sh local-enable LOCAL_ID
sh scripts/skillctl.sh local-move LOCAL_ID --path /absolute/new-root
sh scripts/skillctl.sh exclude Example/private-repo
sh scripts/skillctl.sh include Example/other-repo
sh scripts/skillctl.sh disable
sh scripts/skillctl.sh enable
```

Local registration requires an explicit user request. Keep its returned `local:<id>` and existing notes. A missing named branch means progress stays on the home. GitHub scope comes from the exact origin `OWNER/REPO`; exclusions override inclusions, local roots and conversation consent. `disable` and `enable` affect only this Skill profile. To uninstall, remove this Skill folder using the host's normal Skill management; retained state and vault notes remain. Review any desired state cleanup separately; never delete or move the vault.

Default root areas are `10-memory`, `20-projects`, `30-reusable` and `40-conversations`. One project home uses `type: project` and either `github_repo: OWNER/REPO` or `project_id: local:<id>`. Branch pages use `type: branch`, the same project identity and exact case-sensitive `working_branch`. Link child notes directly from their home and back to it. Use distinct filenames for branches that differ only by case on Windows/macOS.

Use the configured reusable template for shared experience: `type: reusable-memory`, `status: verified`, `summary`, `keywords`, `source_repo` or `source_project_id`, `source_branch`, `source_note`, `verified_on`. The source must be an eligible project note; leave branch empty for repository-level sources. Search before creating a topic. Record applicability, limitations and evidence, preserve conflicting conditions, and retain obsolete notes as `status: retired`. Update the index and validate links. Do not manufacture verification dates or provenance for ordinary chat notes.

## Ordinary conversations

```bash
sh scripts/skillctl.sh conversation-enable --cwd /absolute/ordinary-folder --session-id ACTUAL_SESSION_ID --title "Displayed title"
sh scripts/skillctl.sh conversation-sync --session-id ACTUAL_SESSION_ID
sh scripts/skillctl.sh conversation-disable --session-id ACTUAL_SESSION_ID
sh scripts/skillctl.sh conversation-disable --session-id ACTUAL_SESSION_ID --freeze-title
sh scripts/skillctl.sh conversation-list
```

These commands do not infer consent from prompt keywords. Enable only after a direct request for this actual chat; GitHub/local projects keep their existing route. Use `start` afterwards for immediate context and the current task's review. Each chat loads/searches only its own note. Disabling retains files and permits filename synchronization when explicitly called or on the next `start`; `--freeze-title` also pauses renames. There is no automatic sync while the Skill is idle.

Codex title lookup reads only registered IDs' display metadata (`threads.name`, then `session_index.jsonl`), not chat transcripts or authentication files. `--title` supplies the actual displayed title when metadata is missing during enable. Stable `conversation_id` survives renames; invalid characters, case/Unicode collisions and repeated titles are handled without overwriting another note. Creation and rename receipts remain pending until reviewed. The scope, retrieval, collision handling and structural validator use the same generated runtime as the Hook plugin.
