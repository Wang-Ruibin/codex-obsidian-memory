# Repository guidance

This repository publishes a Hook-based Codex plugin at `plugins/codex-obsidian-memory` and a standalone, Hook-free Skill at `skills/codex-obsidian-memory-skill`.

- Preserve local-first behavior and never add credential collection or remote telemetry.
- No command may delete or move a user's vault.
- Repository and branch routing must use exact identity fields, never body substring matching.
- Keep plugin runtime code dependency-free on Python 3.11+ unless a dependency is justified and documented.
- Keep `README.md` and `README.zh-CN.md` at the repository root for visible language switching. Put other Simplified Chinese explanatory documents under `docs/zh-CN/`; keep their English canonical files at the conventional root or English documentation path.
- Keep paired explanatory-document headings, commands, warnings and links structurally aligned.
- Update tests, README behavior and Skill references together when commands or layouts change.
- Shared routing/retrieval libraries in the standalone Skill are generated from the plugin by `python scripts/build_skill.py`. Edit the canonical plugin modules, regenerate, and check with `--check`; do not maintain a divergent runtime copy.
- Keep the standalone Skill free of Hook definitions, schedulers, background workers and automatic global configuration changes. Its profile is separate from the Hook integration. Do not install or replace either edition on this machine unless the user requests it.
- Run the unit suite, localization parity checks, plugin validator and Skill validator before release.
