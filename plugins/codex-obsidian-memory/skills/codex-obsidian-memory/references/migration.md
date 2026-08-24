# Adopting an existing vault / 接管现有知识库

## English

1. Back up or version the vault.
2. If the vault already matches the default paths, run `memoryctl.py init` without `--force-template`; setup adds only missing default files.
3. If it uses another language or layout, use `--no-template` and repeat `--path KEY=RELATIVE_PATH` for `home`, `global_memory`, `maintenance`, `template`, `project_index`, `projects_dir`, `weekly_brief`, and `monthly_audit` as needed.
4. Move project facts under one repository folder without merging unrelated repositories.
5. Add exact `type`, `github_repo`, and `working_branch` frontmatter.
6. Link every child page from its project home and every project home from the project index.
7. Run `memoryctl.py validate` and resolve duplicate repository homes before enabling the Hook.

All path mappings must be relative and remain inside the configured vault. Do not hand-edit generated configuration when the CLI mapping can represent the layout.

## 中文

1. 备份知识库或将其纳入版本控制。
2. 如果知识库已使用默认路径，运行不带 `--force-template` 的 `memoryctl.py init`；Setup 只增加缺失的默认文件。
3. 如果使用其他语言或布局，使用 `--no-template`，并按需重复 `--path KEY=RELATIVE_PATH` 映射 `home`、`global_memory`、`maintenance`、`template`、`project_index`、`projects_dir`、`weekly_brief` 和 `monthly_audit`。
4. 将项目事实放入唯一仓库文件夹，不合并无关仓库。
5. 增加精确 `type`、`github_repo` 和 `working_branch` frontmatter。
6. 每个子页都从项目主页链接，每个项目主页都从项目总览链接。
7. 启用 Hook 前运行 `memoryctl.py validate` 并解决重复项目主页。

所有路径映射必须是相对路径并保持在已配置知识库内部。当 CLI 映射能够表达布局时，不要手工修改生成配置。
