# Repository guidance / 仓库指南

## English

This repository publishes a Codex plugin whose distributable root is `plugins/codex-obsidian-memory`.

- Preserve local-first behavior and never add credential collection or remote telemetry.
- No command may delete or move a user's vault.
- Repository and branch routing must use exact identity fields, never body substring matching.
- Keep plugin runtime code dependency-free on Python 3.11+ unless a dependency is justified and documented.
- Update tests, README behavior and Skill references together when commands or file layouts change.
- Keep every human-facing Markdown document complete in both English and Chinese.
- Run the unit suite, documentation check, plugin validator and Skill validator before release.

## 中文

本仓库发布一个 Codex 插件，可分发根目录为 `plugins/codex-obsidian-memory`。

- 保持本地优先，永远不得增加凭据收集或远程遥测。
- 任何命令都不得删除或移动用户的知识库。
- 仓库与分支路由必须使用精确身份字段，禁止匹配正文子串。
- 除非依赖有充分理由并完成文档说明，插件运行时代码只依赖 Python 3.11+ 标准库。
- 命令或文件结构变化时，同步更新测试、README 行为说明和 Skill 参考资料。
- 每一份面向人的 Markdown 文档都必须同时提供完整英文和中文内容。
- 发布前运行单元测试、文档检查、插件校验器和 Skill 校验器。
