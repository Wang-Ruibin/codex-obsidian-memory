# Ordinary conversation memory

[简体中文](zh-CN/conversations.md)

## Natural-language control

Ordinary conversations are chats without a GitHub repository and without an
existing local project registration. Their memory is off by default. Requests
such as "Remember this conversation" or "Stop remembering this conversation but
keep its notes" authorize the matching action for this conversation only. Do
not treat examples, quoted requests or a general question about memory as consent.
Existing registered local projects retain their project memory. If the user also wants filename synchronization paused, pass `--freeze-title` when disabling.

Resolve the current ID from `CODEX_THREAD_ID` or the host's thread metadata. Never
use a title or workspace folder as the ID. Use the normal platform launcher; these
source-level commands show the arguments:

```bash
python ../../scripts/memoryctl.py conversation-enable --session-id <actual-session-id> --cwd /absolute/workspace
python ../../scripts/memoryctl.py conversation-disable --session-id <actual-session-id>
python ../../scripts/memoryctl.py conversation-list
```

Enable returns the note path and immediate context. Consume it in the current
conversation and disclose the created note/index. Disable retains the note and
stops loading and factual writeback. Filename synchronization continues for the retained note; add `--freeze-title` to pause it too. Re-enable the same
ID to reuse its facts. Never register a plain workspace merely to enable one chat.

## Titles and filenames

Notes live directly in `40-conversations/` by default. Each has `type: conversation`
and an exact `conversation_id: codex:<session-id>`. Its filename follows the displayed
title, preserving Unicode. Filesystem-invalid characters and reserved names are
sanitized; long names are shortened. A stable ID suffix resolves duplicate titles,
including case-only collisions on Windows. Existing files are never overwritten
to claim a title. The note body is retained when the filename changes.

The read-only metadata adapter uses the current Codex home's SQLite `threads.name`
or its `session_index.jsonl` title record. SQLite's old `title` field can contain the
first prompt and is not used. No transcripts, authentication or unrelated message
content are read. Metadata layouts are host implementation details; if unavailable,
obtain the actual displayed title through the host and pass `--title` on enable.
An unavailable title does not erase or rename an existing note.

## Automatic rename synchronization

Only while registered notes need title synchronization, a detached local worker checks
registered title metadata about every two seconds. Windows runs it without a window;
there is no scheduler, network service or telemetry. A process lock prevents duplicate
workers. Hooks also synchronize the current title. Disabling the integration or
title synchronization for all registered notes stops the worker. Closing or archiving a chat does
not delete its note.

```bash
python ../../scripts/memoryctl.py conversation-sync
```

This command retries local title synchronization. After an idle rename, changed
note/index paths remain pending for the next visible writeback review. Do not
manually edit the managed conversation-index block.

## Isolation and writeback

An enabled chat loads global preferences and its own note. It never loads peer
conversation notes, a project index, or a fabricated branch page. Its search/read
commands are restricted to its own note. GitHub and existing local project routes
take precedence, and explicit repository exclusions cannot be bypassed.

Save durable goals, constraints, verified facts, decisions and next steps rather
than transcripts. Keep uncertain claims labeled. The first enable and later note
changes require the same visible per-file review and ordered markers as projects.
Concurrent chats review only their own notes and their managed-index receipts.

## Existing vaults and verification

Use [migration.md](migration.md) to move experience to a root sibling and add the
conversation index. Do not reinitialize an existing vault. New vaults use separate
`10-memory`, `20-projects`, `30-reusable` and `40-conversations` areas.

Verify default-off silence, immediate enable, disable/resume, duplicate titles,
Unicode and reserved names, body preservation, idle worker renames, metadata
unavailability, independent chat reviews, and rollback on publication failure.
