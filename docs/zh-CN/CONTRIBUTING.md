# 贡献指南

[English](../../CONTRIBUTING.md)

感谢你帮助改进 Codex Obsidian Memory。下面的整个流程都可以交给你的 agent 完成，也可以自己输入命令。

## 准备与测试

```bash
git clone git@github.com:Wang-Ruibin/codex-obsidian-memory.git
cd codex-obsidian-memory
python -m unittest discover -s tests -v
```

运行时使用 Python 3.11+，只依赖标准库，无需安装任何依赖。更喜欢对话方式？把仓库交给你的 agent：

```text
在本地准备好 codex-obsidian-memory 仓库并运行它的测试套件。
告诉我结果，以及是否有失败项。
```

## 基本规则

- 除非用户明确批准替换已审阅模板，否则知识库操作保持增量式。
- 禁止读取凭据、私钥、Cookie 或无关个人文件。
- 保持 `github_repo` 和 `working_branch` 精确路由。
- 为路由、生命周期、迁移和卸载修复增加行为测试。
- 同一次修改中同步更新英文源文档和对应 `zh-CN` 翻译，保持标题、代码块、警告和本地链接结构一致。

大型结构迁移前请先创建 Issue。Pull Request 应说明用户可见结果、执行过的测试及兼容性影响。
