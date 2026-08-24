# Adopting an existing vault

1. Back up or version the vault.
2. If the vault already matches the default paths, run `memoryctl.py init` without `--force-template`; setup adds only missing default files.
3. If it uses another language or layout, use `--no-template` and repeat `--path KEY=RELATIVE_PATH` for `home`, `global_memory`, `maintenance`, `template`, `project_index`, `projects_dir`, `weekly_brief`, and `monthly_audit` as needed.
4. Move project facts under one repository folder without merging unrelated repositories.
5. Add exact `type`, `github_repo`, and `working_branch` frontmatter.
6. Link every child page from its project home and every project home from the project index.
7. Run `memoryctl.py validate` and resolve duplicate repository homes before enabling the Hook.

All path mappings must be relative and remain inside the configured vault. Do not hand-edit generated configuration when the CLI mapping can represent the layout.
