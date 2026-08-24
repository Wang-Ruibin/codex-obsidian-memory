# Repository guidance

This repository publishes a Codex plugin whose distributable root is `plugins/codex-obsidian-memory`.

- Preserve local-first behavior and never add credential collection or remote telemetry.
- No command may delete or move a user's vault.
- Repository and branch routing must use exact identity fields, never body substring matching.
- Keep plugin runtime code dependency-free on Python 3.11+ unless a dependency is justified and documented.
- Public-facing explanatory documents use English canonical files plus separate Simplified Chinese `.zh-CN` files or `zh-CN/` directories.
- Keep paired explanatory-document headings, commands, warnings and links structurally aligned.
- Update tests, README behavior and Skill references together when commands or layouts change.
- Run the unit suite, localization parity checks, plugin validator and Skill validator before release.
