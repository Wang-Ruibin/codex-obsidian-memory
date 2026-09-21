# Security policy

[简体中文](docs/zh-CN/SECURITY.md)

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/Wang-Ruibin/codex-obsidian-memory/security/advisories/new). During the initial development stage, security fixes are applied to the latest release on `main`.

Never include real tokens, private keys, cookies, private vault pages or other credentials in reports, issues, pull requests, fixtures or logs.

## Trust boundary

- The plugin runs local lifecycle hooks and reads a user-selected Markdown vault. Review hook definitions in `/hooks` before trusting them.
- Repository identity comes from read-only Git commands. Every note is resolved inside the configured vault, and common secret patterns are redacted before injection. No command deletes or moves the vault.
- At prompt start, the plugin stores a temporary map of relative Markdown paths and SHA-256 hashes — never note bodies. At Stop, it requires a visible review covering every created, modified or deleted file with a concrete description, followed by disclosure and review markers. Comments, code fences, quoted text and filename-only or generic “updated” entries do not satisfy this check. An incomplete review remains blocked on retries and keeps the snapshot. Successful completion removes it.
- This is a file-coverage and minimum-description check, not proof that the described facts are accurate or exhaustive. Review the notes before relying on them. Missing turn identifiers or an unavailable snapshot prevent change detection; the review instruction still applies, but per-file enforcement needs the prompt-start snapshot.
- Branch routing and duplicate-identity validation compare the full `working_branch` value case-sensitively and the GitHub repository identity case-insensitively. Use distinct note filenames on filesystems that ignore filename case.
- Hook context uses a 16,000-token threshold. Oversized context may be delivered as a head-and-tail preview with the full output stored separately by Codex.
- Redaction is defense in depth, not a complete secret scanner. Keep credentials out of Markdown memory files.
