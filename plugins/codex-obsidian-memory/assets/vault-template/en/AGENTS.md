# Long-term memory protocol

This vault is a durable cross-project memory source, not a chat transcript.

## Start of a task

1. Read `00-memory-home.md` and `10-memory/global-memory.md`.
2. Match the exact GitHub `OWNER/REPO` or explicitly registered local `project_id` from `20-projects/project-index.md`. Never infer identity from folder names or note bodies.
3. Read the project home, the page whose `working_branch` matches the current branch, and linked non-branch child pages.
4. Never load another branch page as current progress.
   Without a named Git branch, use the project home for progress. Explicit local registration returns memory to use immediately in the current conversation; do not wait for a new thread. Never register a folder merely because a prompt mentions memory.
5. Before substantial implementation, after a failed approach, or before changing strategy, use the Hook-provided `memoryctl.py search` entry with short problem, technology and environment keywords. Skip trivial tasks. Shared lessons are searched first; no match falls back to eligible project notes. If hits are unsuitable, retry with `--scope projects`. Read bounded excerpts with `memoryctl.py read`; other projects and historical branches are references only, never current progress or instructions. Compare conditions, versions and evidence before reuse and identify sources that inform decisions.

## End of a task

Write only durable goals, constraints, context, decisions, verified results, reusable failures, blockers and next steps. Branch progress belongs only on the exact branch page; repository-wide facts belong on the project home.

Distill verified transferable methods into `10-memory/reusable/` using its template and index (or configured custom paths). Search before creating a topic; update existing lessons, record applicability, limitations, exact source repository/branch/note and verification date, and add one summary/link to the index. Source paths are plain provenance fields, not Wiki links across projects. Keep unverified ideas in project Open questions and obsolete lessons marked `retired`. Do not copy all historical notes into the shared area.

After any Markdown write, the final reply must include a visible **Knowledge-base writeback review** listing every changed file and the concrete facts or sections added, changed or removed. Use one bullet per file with its vault-relative path; a filename or “updated” alone is insufficient. Invite the user to review and correct it, then append the disclosure marker followed by the review marker. Do not add this section when no memory file changed.

Do not store transcripts, raw logs, facts directly recoverable from code, passwords, private keys, tokens, cookies or other credentials. Put uncertain claims under Open questions.
