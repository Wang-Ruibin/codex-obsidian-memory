# Security policy / 安全策略

## English

## Supported versions

Security fixes are applied to the latest release on `main` while the project is in its initial development stage.

## Reporting a vulnerability

Please use GitHub private vulnerability reporting for this repository. Do not include real tokens, private keys, cookies, private vault pages or other credentials in an issue, pull request, test fixture or log.

## Trust boundary

This plugin runs local lifecycle hooks and reads a user-selected Markdown vault. Review hook definitions in `/hooks` before trusting them. The plugin should use only read-only Git identity commands, resolve every note path within the configured vault, redact common secret patterns before injection and never delete the vault.

Secret-pattern redaction is defense in depth, not a complete secret scanner. Keep credentials out of Markdown memory files.

## 中文

### 支持版本

项目处于早期开发阶段时，安全修复应用于 `main` 上的最新版本。

### 报告安全漏洞

请使用本仓库的 GitHub 私密漏洞报告功能。Issue、Pull Request、测试夹具和日志中不得包含真实令牌、私钥、Cookie、私人知识库页面或其他凭据。

### 信任边界

本插件运行本地生命周期 Hook，并读取用户选择的 Markdown 知识库。信任前请在 `/hooks` 中审阅 Hook 定义。插件只能运行只读 Git 身份命令；所有笔记路径必须解析在配置的知识库内；注入前遮蔽常见秘密模式；永远不得删除知识库。

秘密模式遮蔽只是纵深防御，并非完整的秘密扫描器。请勿在 Markdown 记忆文件中保存凭据。
