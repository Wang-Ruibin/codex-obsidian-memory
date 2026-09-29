# Security policy

[简体中文](docs/zh-CN/SECURITY.md)

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/Wang-Ruibin/codex-obsidian-memory/security/advisories/new). During the initial development stage, security fixes are applied to the latest release on `main`.

Never include real tokens, private keys, cookies, private vault pages or other credentials in reports, issues, pull requests, fixtures or logs.

## Trust boundary

- The plugin runs local lifecycle hooks and reads a user-selected Markdown vault. Review hook definitions in `/hooks` before trusting them.
- Explicit runtime preparation can download a checksum-pinned uv bootstrap and a private Python distribution. It does not upload notes, install pip packages, change system PATH or register system Python. Ordinary Hooks never download. Setup removes bootstrap downloads and temporary extraction files; the selected private interpreter is retained while in use.
- Repository identity comes from read-only Git commands. Every note is resolved inside the configured vault, and common secret patterns are redacted before injection. No command deletes or moves the vault.
- Local projects use explicitly registered canonical roots and stable IDs; unregistered folders stay silent. Registration does not edit project files or Git settings. Its pending-review receipt contains only changed note paths, requiring a visible current-task disclosure even without a pre-registration prompt snapshot. Other changes still need the normal snapshot. Stopping a local registration preserves notes and withholds their reference retrieval.
- At prompt start, the plugin stores a temporary map of relative Markdown paths and SHA-256 hashes — never note bodies. At Stop, it requires a visible review covering every created, modified or deleted file in this task's scoped notes with a concrete description, followed by disclosure and review markers. Comments, code fences, quoted text and filename-only or generic “updated” entries do not satisfy this check. An incomplete review remains blocked on retries and keeps the snapshot. Successful completion removes it.
- In a project conversation, the review covers its own project folder and shared notes explicitly claimed for that turn. Other projects' note changes are excluded. The `claim-shared` operation reserves a global-memory or shared-lesson file until that turn's review is accepted; a second conversation must wait before editing it. Vault maintenance intentionally reviews the whole vault. Direct concurrent writes to the same project note still require coordination.
- This is a file-coverage and minimum-description check, not proof that the described facts are accurate or exhaustive. Review the notes before relying on them. Missing turn identifiers or an unavailable snapshot prevent change detection; the review instruction still applies, but per-file enforcement needs the prompt-start snapshot.
- Branch routing and duplicate-identity validation compare the full `working_branch` value case-sensitively and the GitHub repository identity case-insensitively. Use distinct note filenames on filesystems that ignore filename case.
- Hook context uses a 16,000-token threshold. Oversized context may be delivered as a head-and-tail preview with the full output stored separately by Codex.
- Redaction is defense in depth, not a complete secret scanner. Keep credentials out of Markdown memory files.
