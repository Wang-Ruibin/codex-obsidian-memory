# Security policy

[简体中文](docs/zh-CN/SECURITY.md)

## Supported versions

Security fixes are applied to the latest release on `main` during the initial development stage.

## Reporting a vulnerability

Use GitHub private vulnerability reporting. Never include real tokens, private keys, cookies, private vault pages or other credentials in issues, pull requests, fixtures or logs.

## Trust boundary

This plugin runs local lifecycle hooks and reads a user-selected Markdown vault. Review hook definitions in `/hooks` before trusting them. The plugin uses read-only Git identity commands, resolves every note inside the configured vault, redacts common secret patterns before injection and never deletes the vault.

At prompt start, the plugin stores a temporary map of relative Markdown paths and SHA-256 hashes. It never copies note bodies into review state. At Stop, it compares hashes and requires visible disclosure of changed files and facts before accepting the final review markers; successful completion removes the turn snapshot.

Redaction is defense in depth, not a complete secret scanner. Keep credentials out of Markdown memory files.
