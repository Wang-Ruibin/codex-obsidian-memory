# 安全模型

[English](../security.md)

- 记忆保留在用户选择的本地知识库中。
- Hook 只使用只读 Git 命令识别 `origin` 和当前分支。
- 拒绝解析后位于知识库之外的笔记路径。
- 仓库准入来自配置的 owner、包含项和排除项。
- 开始类 Hook 在注入前遮蔽常见令牌和私钥模式。
- Stop Hook 要求执行持久记忆检查，但永远不保存凭据。
- 本轮快照只包含 Markdown 相对路径和 SHA-256 哈希，不包含笔记正文。只要笔记变化，Hook 接受结束前必须在最终回复中可见披露回写。
- 插件 Hook 必须在 `/hooks` 中显式审阅；定义改变后需要重新信任。
- Setup 在窄范围修改 writable root 前备份 `config.toml`。
- Uninstall 只移除 Setup 记录为本插件添加的 root，永远不删除知识库。

任何扫描器都不完整。请勿在 Markdown 笔记和仓库中保存秘密。
