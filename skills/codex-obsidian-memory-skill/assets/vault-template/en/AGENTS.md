# Long-term memory protocol — Skill edition

This vault is a durable local memory source, not a chat transcript. Use the standalone `codex-obsidian-memory-skill`; it has no lifecycle hooks or background workers.

## Start of a task

Run the Skill's `skillctl start --cwd <workspace>`, consume its context and keep its task ID. Resume unfinished work with the same task ID after compaction or interruption. Use exact GitHub origin identity or an explicitly registered local project ID. Load only the current branch page and directly linked non-branch children. Unregistered ordinary chats remain off unless the user explicitly enables the actual session ID.

## During a task

Search shared experience before substantial implementation, after failure or before changing strategy; retry projects when shared candidates do not apply. Read bounded evidence and verify conditions and sources. Historical branches are references. Reserve each shared/global note with `claim-shared` and this task ID before editing; defer on foreign claims. Coordinate edits to the same project file.

## End of a task

Keep durable goals, constraints, context, decisions, verified results, transferable failures and next steps. Branch progress belongs on the exact branch page; stable repository context belongs on its home. Shared verified methods retain applicability, limitations, source identity/branch/note and verification date. Never save transcripts, credentials, raw logs or guesses as facts.

Run `changes` and `validate`, then show one concrete per-file entry in a visible Knowledge-base writeback review and invite corrections. Pass that UTF-8 review draft to `finish`; omit the section and review file when no Markdown changed. The command validates coverage and releases only this task's claims; there is no host Stop enforcement or hidden marker requirement. Remove the temporary draft afterwards.

## Ordinary conversations

Explicit per-chat consent uses `conversation-enable/disable` and the actual session ID. Existing local/GitHub project routing takes precedence. Load only the corresponding chat note. Filename synchronization happens on `start` or explicit `conversation-sync`, including after content memory is disabled, unless title sync is frozen. Nothing runs while the Skill is idle. Never delete or move the vault.
