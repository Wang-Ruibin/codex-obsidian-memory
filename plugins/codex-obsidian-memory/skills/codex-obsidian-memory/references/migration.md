# Adopting an existing vault

[简体中文](zh-CN/migration.md)

1. Back up or version the vault.
2. If it matches default paths, run `init` without `--force-template`; only missing files are added.
3. For another language or layout, use `--no-template` and repeat `--path KEY=RELATIVE_PATH` as needed.
4. Keep one repository folder and do not merge unrelated project facts.
5. Add exact `type`, `github_repo`, and `working_branch` frontmatter.
6. Link every child page from its project home and every project home from the index.
7. Run `validate` and resolve duplicate identities before enabling normal work.

Path mappings must be relative and remain inside the vault. Prefer CLI mappings over hand-editing generated configuration.
