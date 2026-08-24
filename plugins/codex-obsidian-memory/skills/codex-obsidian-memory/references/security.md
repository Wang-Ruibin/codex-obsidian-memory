# Security model / 安全模型

## English

Use this reference when reviewing hook trust, writable roots, or sensitive data handling.

- All memory files stay in the user-selected local vault.
- The Hook runs read-only Git commands to identify `origin` and the current branch.
- The Hook reads only configured vault files and rejects resolved paths outside the vault.
- Repository eligibility is determined by configured GitHub owners, explicit inclusions, and exclusions.
- Start hooks redact common token and private-key patterns before injecting notes.
- The Stop hook asks the agent to review durable updates; it never receives or stores credentials.
- Plugin hooks require explicit review in `/hooks`; changed hook definitions require trust again.
- Cross-project writes require the vault to be an approved Codex writable root. Setup creates a backup before narrowly editing `config.toml`.
- Uninstall removes the writable root only when setup recorded that this plugin added it. It never deletes or moves the vault.

No secret-scanning rule is complete. Users remain responsible for keeping secrets out of Markdown notes and repositories.

## 中文

审阅 Hook 信任、writable root 或敏感数据处理时使用本参考。

- 所有记忆文件保留在用户选择的本地知识库中。
- Hook 只运行只读 Git 命令来识别 `origin` 和当前分支。
- Hook 只读取已配置知识库文件，并拒绝解析后位于知识库之外的路径。
- 仓库准入由配置的 GitHub owner、显式包含项和排除项决定。
- 开始类 Hook 在注入笔记前遮蔽常见令牌和私钥模式。
- Stop Hook 只要求 agent 审阅持久更新，不接收或保存凭据。
- 插件 Hook 必须在 `/hooks` 中显式审阅；Hook 定义改变后需要重新信任。
- 跨项目写入要求知识库成为已批准的 Codex writable root；Setup 在窄范围修改 `config.toml` 前创建备份。
- Uninstall 仅在 Setup 记录该 writable root 由本插件添加时移除它；永远不删除或移动知识库。

任何秘密扫描规则都不可能完整。用户仍有责任确保 Markdown 笔记和仓库中不保存秘密。
