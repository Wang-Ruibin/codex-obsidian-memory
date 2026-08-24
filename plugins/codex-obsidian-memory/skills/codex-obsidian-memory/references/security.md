# Security model

[简体中文](zh-CN/security.md)

- Memory stays in the user-selected local vault.
- Hooks use read-only Git commands to identify `origin` and the current branch.
- Resolved note paths outside the vault are rejected.
- Repository eligibility comes from configured owners, inclusions and exclusions.
- Start hooks redact common token and private-key patterns before injection.
- The Stop hook requests a durable-memory review but never stores credentials.
- Plugin hooks require explicit review in `/hooks`; changed definitions require trust again.
- Setup backs up `config.toml` before a narrow writable-root edit.
- Uninstall removes a root only when setup recorded that this plugin added it. It never deletes the vault.

No scanner is complete. Keep secrets out of Markdown notes and repositories.
