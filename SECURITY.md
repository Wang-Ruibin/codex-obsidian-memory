# Security policy

[简体中文](docs/zh-CN/SECURITY.md)

## Report a vulnerability

Use [GitHub private vulnerability reporting](https://github.com/Wang-Ruibin/codex-obsidian-memory/security/advisories/new). During the initial development stage, security fixes are applied to the latest release on `main`.

Never include real tokens, private keys, cookies, private vault pages or other credentials in reports, issues, pull requests, fixtures or logs.

## Trust boundary

- The plugin runs local lifecycle hooks and reads a user-selected Markdown vault. Review hook definitions in `/hooks` before trusting them.
- Repository identity comes from read-only Git commands. Every note is resolved inside the configured vault, and common secret patterns are redacted before injection. No command deletes or moves the vault.
- At prompt start, the plugin stores a temporary map of relative Markdown paths and SHA-256 hashes — never note bodies. At Stop, it compares hashes and requires a visible writeback-review heading plus disclosure and review markers. Codex is told to explain every changed file, but version 0.4.0 cannot judge whether that explanation is complete or accurate. Review it before relying on the new memory. Successful completion removes the turn snapshot.
- Branch pages preserve the full `working_branch` value, but version 0.4.0 compares it case-insensitively. Avoid branch names that differ only by letter case until this limitation is removed.
- Hook context uses a 16,000-token threshold. Oversized context may be delivered as a head-and-tail preview with the full output stored separately by Codex.
- Redaction is defense in depth, not a complete secret scanner. Keep credentials out of Markdown memory files.
