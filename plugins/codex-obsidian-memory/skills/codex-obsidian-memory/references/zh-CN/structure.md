# 知识库结构

[English](../structure.md)

修改笔记路径、图谱路由、项目身份或分支行为时使用本参考。

```text
00-memory-home
├── 10-memory/global-memory
├── 10-memory/maintenance
│   └── 10-memory/project-template
└── 20-projects/project-index
    └── 20-projects/<repository>/<repository>
        ├── <branch-page>
        └── 可选决策、失败经验或里程碑页面
```

知识簇和项目簇只保留一条刻意建立的桥：记忆首页到项目总览。

## 身份规则

- 项目主页具有 `type: project` 和精确 `github_repo: OWNER/REPO`。
- 一个仓库对应一个文件夹和一个项目主页。
- 分支页具有 `type: branch`、相同 `github_repo` 和精确区分大小写的 `working_branch`。`Release` 和 `release` 属于不同身份；仓库和精确分支名都相同的两个页面仍是重复。在不区分文件名大小写的系统上，请使用 `release-upper.md` 和 `release-lower.md` 等不同文件名；分支身份不由文件名决定。
- 文件名可以替换路径分隔符，但 `working_branch` 保留原始 Git 名称。
- 只有存在持久分支背景时才创建分支页，不要求为每次 checkout 建立空页面。
- 项目主页直接链接每个分支页和仓库级子页。

只保留稳定目标、约束、背景、有理由的决策、已验证结果、可复用失败经验、阻塞和具体下一步。不要保存对话记录、原始输出、可直接从代码获得的事实或秘密。
