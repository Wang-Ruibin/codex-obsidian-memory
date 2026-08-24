# Security model

Use this reference when reviewing hook trust, writable roots, or sensitive data handling.

- All memory files stay in the user-selected local vault.
- The Hook runs read-only Git commands to identify `origin` and the current branch.
- The Hook reads only configured vault files and rejects resolved paths outside the vault.
- Repository eligibility is determined by configured GitHub owners, explicit inclusions, and exclusions.
- Start hooks redact common token and private-key patterns before injecting notes.
- The Stop hook asks the agent to review durable updates; it never receives or stores credentials.
- Plugin hooks require explicit review in `/hooks`; changed hook definitions require trust again.
- Cross-project writes require the vault to be an approved Codex writable root. Setup creates a backup before narrowly editing `config.toml`.
- Uninstall removes the writable root only when setup recorded that this plugin added it. It never deletes or moves the vault.

No secret-scanning rule is complete. Users remain responsible for keeping secrets out of Markdown notes and repositories.
