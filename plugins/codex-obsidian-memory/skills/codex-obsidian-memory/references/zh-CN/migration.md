# 接管现有知识库

[English](../migration.md)

1. 备份知识库或将其纳入版本控制。
2. 如果布局符合默认路径，运行不带 `--force-template` 的 `init`；只增加缺失文件。
3. 其他语言或布局使用 `--no-template`，并按需重复 `--path KEY=RELATIVE_PATH`。
4. 每个仓库只使用一个文件夹，不合并无关项目事实。
5. 增加精确 `type`、`github_repo` 和 `working_branch` frontmatter。
6. 每个子页从项目主页链接，每个项目主页从总览链接。
7. 启用普通工作前运行 `validate` 并解决重复身份。

路径映射必须是相对路径并保持在知识库内部。优先使用 CLI 映射，不要手工修改生成配置。
