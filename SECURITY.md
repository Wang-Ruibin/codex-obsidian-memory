# Security policy

## Supported versions

Security fixes are applied to the latest release on `main` while the project is in its initial development stage.

## Reporting a vulnerability

Please use GitHub private vulnerability reporting for this repository. Do not include real tokens, private keys, cookies, private vault pages or other credentials in an issue, pull request, test fixture or log.

## Trust boundary

This plugin runs local lifecycle hooks and reads a user-selected Markdown vault. Review hook definitions in `/hooks` before trusting them. The plugin should use only read-only Git identity commands, resolve every note path within the configured vault, redact common secret patterns before injection and never delete the vault.

Secret-pattern redaction is defense in depth, not a complete secret scanner. Keep credentials out of Markdown memory files.
