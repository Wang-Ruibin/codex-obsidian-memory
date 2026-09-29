# Local project memory

[简体中文](zh-CN/local-projects.md)

Use when the user explicitly asks to enable memory for a local project, including a folder with no Git or GitHub account. Merely mentioning memory, quoting an example or asking how it works is not consent to register a project. Commands below run from the Skill directory; use the installed interpreter for the current environment.

## Enable in the current conversation

Check `status` first. If memory is already configured, preserve it; do not re-run `init`. Otherwise ask where the vault belongs and whether the user wants local-only or GitHub plus explicitly registered local projects. Local-only setup does not need an owner or a Git installation:

```bash
python ../../scripts/memoryctl.py init --vault /absolute/path/to/memory --local-only --locale en
python ../../scripts/memoryctl.py local-register --path /absolute/path/to/project --name "My project"
```

Confirm the intended project root from the workspace. A subdirectory inside an already registered project does not require another registration. Registration is an explicit action performed by the agent; the Hook never enables memory by scanning prompt keywords. An explicit user request to enable this project authorizes this registration; do not ask for the same approval again. Separate setup changes such as global writable-root configuration still follow the setup policy.

Registration returns the stable project ID, root, changed notes and the complete eligible memory context. Read that returned context and use it immediately in this same task. Do not tell the user to restart or open a new conversation to activate a registered local project. The current Stop event resolves the new registration and requests memory review. A receipt of registration-created/updated note paths requires a visible per-file writeback review even if no prompt-start snapshot existed before registration. Other note edits still rely on the usual prompt-start snapshot when available.

To reload memory later in the same conversation:

```bash
python ../../scripts/memoryctl.py context --cwd /absolute/path/to/project
```

Future prompts, compaction and subagents use the registration automatically. First installing the plugin itself may still require the host to reload skills and trust Hook definitions; project registration does not bypass that installation requirement. If Hooks have not been loaded/trusted yet, use the returned context and perform the current task's review explicitly, then explain the remaining host setup step.

## Identity and directory routing

The integration configuration holds `local_projects` entries with a generated `project_id: local:<32 lowercase hex digits>`, resolved absolute `root`, display `name`, `enabled` flag and vault-relative `project_home`. Local absolute paths are not embedded into shared notes. Each ID has one home, typically `20-projects/local-<id>/project.md`, using `type: project`, `source_kind: local` and `project_id` instead of `github_repo`. Same-named folders get distinct IDs. Repeat registration of the same root reuses its ID and notes.

Normal child folders inherit their nearest registered root. A separately registered nested project overrides its parent; a disabled nested registration blocks parent fallback. An independent nested Git repository does not inherit a parent local registration. Canonical paths resolve symbolic links, avoiding a second identity for the same physical root. Drive roots, the user's home directory, the vault and directories containing the vault cannot be registered.

For a Git repository registered at its root, branch pages use its exact case-sensitive `working_branch` and the same `project_id`, with no `github_repo`. Create them only for durable branch-specific progress. Plain folders and detached HEAD have no named current branch: retain progress on the project home and do not invent `main` or `detached-head` pages.

Local registrations take precedence over automatic GitHub scope, so adding a GitHub origin later does not silently replace the local identity. Explicit GitHub exclusions take precedence over both routes. Registration refuses to create a second memory home for an already indexed GitHub project. Existing GitHub identities remain unchanged. Local-only mode disables automatic GitHub routing; mixed use can keep the existing GitHub configuration and register selected local roots.

## Stop, resume and relocate

Obtain the actual ID from `local-list`. The example ID below must be replaced with that returned value; do not invent it.

```bash
python ../../scripts/memoryctl.py local-list
python ../../scripts/memoryctl.py local-disable local:0123456789abcdef0123456789abcdef
python ../../scripts/memoryctl.py local-enable local:0123456789abcdef0123456789abcdef
python ../../scripts/memoryctl.py local-move local:0123456789abcdef0123456789abcdef --path /absolute/path/to/new-location
```

Disabling a local registration retains its notes and identity but stops automatic loading, Stop review and reference retrieval for it, including shared lessons derived from that source. Resume returns memory context for immediate use. `local-move` only changes the registered path after the user has moved the project; it never moves project files or vault notes. A different directory cannot claim an already registered root. All registration updates are serialized by a short-lived lock next to the integration configuration; if an interrupted command leaves the lock behind, inspect the owning operation before removing that specific stale lock.

Windows and WSL configurations are separate. To use the same local project identity from another environment sharing this vault, explicitly attach its existing ID using that environment's path:

```bash
python ../../scripts/memoryctl.py local-register --path /absolute/path/visible/here --project-id local:0123456789abcdef0123456789abcdef
```

This requires one existing project home with the requested ID. Never guess that matching folder names mean the same project. Do not copy credentials or entire configurations across environments.

## Shared experience and verification

Enabled local project homes and linked children participate in `search` and `read`. Their results carry `project_id`; `repository` is empty. A shared lesson from a local project uses `source_project_id` instead of `source_repo`, with the same exact `source_note`, `source_branch` and `verified_on` rules. A lesson must use exactly one of these source identity fields. Disabling a source makes its active derived lessons unavailable; validation reports those provenance problems until they are reviewed or retired.

Check that registration immediately returns global/project context, current-task Stop requests a per-file review, and a later prompt recalls a saved fact. Verify exact branches for local Git, plain-folder operation without GitHub, duplicate names, nested boundaries, relocation and disabling. Run `validate`, report every changed vault file and invite correction. Keep uncertain claims in Open questions rather than inventing remembered facts.
