# 接管现有知识库

[English](../migration.md)

已经有自己的 Obsidian 知识库？你不需要手工重新整理。告诉 Codex 知识库在哪里，以及哪些内容必须保留：

```text
使用 $codex-obsidian-memory 接管我位于 /absolute/path/to/vault 的现有知识库。保留当前文件夹和笔记，不要覆盖任何内容；修改全局 Codex 配置前先询问我，并在完成后验证结果。
```

继续前，请先备份知识库或将它纳入版本控制。Codex 应先检查现有布局，向你展示准备采用的映射，并在修改前等待确认。

## Codex 应该保留什么

- 已有笔记保持不变。如果知识库本来就是默认布局，设置过程只补充缺失的模板文件。
- 自定义布局会被映射，而不是被替换；所有映射路径都留在知识库内部。
- 每个 GitHub 仓库保留一个项目文件夹和一个项目主页，分支进度只进入匹配的分支页。
- 每个项目主页继续由项目总览链接，分支页和其他子页继续由对应项目主页链接。
- 只有验证结果不存在必需笔记缺失、重复身份、Wiki 断链和孤立节点时，才开始正常使用自动记忆。

## 手工路径参考

大多数用户到这里就可以交给 Codex 完成。如果你需要亲自审阅或输入映射，可以使用以下路径键：

| 键 | 用途 | 默认值 |
|---|---|---|
| `home` | 记忆首页 | `00-memory-home.md` |
| `global_memory` | 跨项目偏好 | `10-memory/global-memory.md` |
| `maintenance` | 维护中心 | `10-memory/maintenance.md` |
| `template` | 项目与分支模板 | `10-memory/project-template.md` |
| `project_index` | 仓库总览 | `20-projects/project-index.md` |
| `projects_dir` | 仓库文件夹 | `20-projects` |
| `weekly_brief` | 每周报告 | `10-memory/weekly-brief.md` |
| `monthly_audit` | 每月报告 | `10-memory/monthly-audit.md` |

## 手工示例

在 Skill 目录中执行下面的命令，可以在不复制默认模板的情况下接管自定义布局。请先替换知识库路径和 owner，再按实际布局调整笔记路径：

```text
python ../../scripts/memoryctl.py init --vault /absolute/path/to/vault --github-owner my-account --no-template --path home=Home.md --path global_memory=Knowledge/Global.md --path maintenance=Knowledge/Maintenance.md --path template=Knowledge/Project-template.md --path project_index=Projects/Index.md --path projects_dir=Projects --path weekly_brief=Knowledge/Weekly.md --path monthly_audit=Knowledge/Monthly.md
```

Windows 上没有 `python` 时使用 `py.exe`。接管后立即运行 `status` 和 `validate`。如果任一检查发现问题，请保持自动记忆暂停，并让 Codex 解释需要处理的内容。

## 验证第一条已保存的记忆

让 Codex 检查当前打开的项目是否在适用范围内；知识库健康并不能证明这一点。然后保存一条真实项目偏好，查看它指出的笔记，在同一项目、同一分支新开对话，询问这条偏好及来源。如果没有读取到，先检查 Hook 信任和项目范围，不要重复初始化。

回写审查被拦截时，每个修改笔记单独列一条，包含相对知识库的路径和具体说明。不同项目文件夹有同名文件时，需要带目录路径。Windows 上为 `Release` 和 `release` 等分支使用不同笔记文件名，同时保留精确的 `working_branch` 值。
