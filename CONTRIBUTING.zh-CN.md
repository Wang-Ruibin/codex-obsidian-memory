# 贡献指南

[English](CONTRIBUTING.md)

感谢你帮助改进 Codex Obsidian Memory。

## 开发环境

运行时使用 Python 3.11+，且只依赖标准库。

```bash
git clone git@github.com:Wang-Ruibin/codex-obsidian-memory.git
cd codex-obsidian-memory
python -m unittest discover -s tests -v
```

## 修改规则

- 除非用户明确批准替换已审阅模板，否则知识库操作保持增量式。
- 禁止读取凭据、私钥、Cookie 或无关个人文件。
- 保持 `github_repo` 和 `working_branch` 精确路由。
- 为路由、生命周期、迁移和卸载修复增加行为测试。
- 同一次修改中同步更新英文源文档和对应 `zh-CN` 翻译。
- 不同语言的标题、代码块、警告和本地链接结构保持一致。

大型结构迁移前请先创建 Issue。Pull Request 应说明用户可见结果、执行过的测试及兼容性影响。
