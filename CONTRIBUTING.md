# Contributing / 贡献指南

## English

Thanks for improving Codex Obsidian Memory.

## Development setup

The runtime uses Python 3.11+ and the standard library only.

```bash
git clone git@github.com:Wang-Ruibin/codex-obsidian-memory.git
cd codex-obsidian-memory
python -m unittest discover -s tests -v
```

## Change rules

- Keep vault operations additive unless a user explicitly asks to replace a reviewed template file.
- Never add code that reads credentials, private keys, cookies or unrelated personal files.
- Preserve exact `github_repo` and `working_branch` routing.
- Add a behavioral test for every routing, lifecycle, migration or uninstall fix.
- Update the bundled Skill and README when the CLI changes.

Open an issue before a large schema migration. Pull requests should explain the user-visible outcome, tests run and any compatibility impact.

## 中文

感谢你帮助改进 Codex Obsidian Memory。

### 开发环境

运行时使用 Python 3.11+，且只依赖标准库。

```bash
git clone git@github.com:Wang-Ruibin/codex-obsidian-memory.git
cd codex-obsidian-memory
python -m unittest discover -s tests -v
```

### 修改规则

- 除非用户明确要求替换已审阅的模板文件，否则知识库操作必须保持增量式。
- 禁止增加读取凭据、私钥、Cookie 或无关个人文件的代码。
- 保持 `github_repo` 与 `working_branch` 精确路由。
- 每个路由、生命周期、迁移或卸载修复都要增加行为测试。
- CLI 变化时同步更新捆绑的 Skill 和 README。
- 所有面向人的 Markdown 文档必须同步维护英文与中文版本。

大型结构迁移前请先创建 Issue。Pull Request 应说明用户可见结果、执行过的测试以及兼容性影响。
