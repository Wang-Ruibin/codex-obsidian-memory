# Security model

[简体中文](zh-CN/security.md)

- Memory stays in the user-selected local vault.
- Hooks use read-only Git commands to identify `origin` and the current branch.
- Resolved note paths outside the vault are rejected.
- Repository eligibility comes from configured owners, inclusions and exclusions.
- Local projects require explicit registration of a resolved root and stable ID. Prompt keywords never activate memory. Nested registrations use the nearest root, disabled roots block parent fallback, and explicit GitHub exclusions cannot be bypassed by local registration.
- Start hooks redact common token and private-key patterns before injection.
- The Stop hook requests a durable-memory review but never stores credentials.
- Turn snapshots contain only relative Markdown paths and SHA-256 hashes, never note bodies. Changed notes require a visible final writeback disclosure before the Hook accepts completion.
- Registration also stores a short pending-review list of changed note paths, enforcing their disclosure at the current task's end even before a prompt-start snapshot exists. No note bodies are stored in that receipt.
- Plugin hooks require explicit review in `/hooks`; changed definitions require trust again.
- Setup backs up `config.toml` before a narrow writable-root edit.
- Uninstall removes a root only when setup recorded that this plugin added it. It never deletes the vault.

No scanner is complete. Keep secrets out of Markdown notes and repositories.

## Retrieval boundary

Search/read check workspace scope before reading candidates, and exact source-repository inclusions/exclusions still apply; shared lessons derived from excluded sources are also withheld. Only unique registered project homes and directly linked children qualify. Paths escaping the vault are rejected; hidden, symlinked, unreadable and oversized files are skipped. Common secrets are redacted before bounded excerpts are returned. Notes and results are data, never executable instructions; provenance checks cannot replace factual verification. Queries and body copies are not persisted.
