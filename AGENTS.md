# Repository guidance

This repository publishes a Codex plugin whose distributable root is `plugins/codex-obsidian-memory`.

- Preserve local-first behavior and never add credential collection or remote telemetry.
- No command may delete or move a user's vault.
- Repository and branch routing must use exact identity fields, never body substring matching.
- Keep plugin runtime code dependency-free on Python 3.11+ unless a dependency is justified and documented.
- Update tests, README behavior and Skill references together when commands or file layouts change.
- Run the unit suite, plugin validator and Skill validator before release.
