# Vault structure / 知识库结构

## English

Use this reference when changing note paths, graph routing, project identity, or branch behavior.

```text
00-memory-home
├── 10-memory/global-memory
├── 10-memory/maintenance
│   └── 10-memory/project-template
└── 20-projects/project-index
    └── 20-projects/<repository>/<repository>
        ├── <branch-page>
        └── optional decision, failure, or milestone pages
```

The knowledge cluster and project cluster have one intentional bridge: memory home to project index. Project facts do not live in the knowledge cluster.

## Identity rules

- A project home has `type: project` and an exact `github_repo: OWNER/REPO` field.
- One repository maps to one folder and one project home.
- A branch page has `type: branch`, the same `github_repo`, and an exact `working_branch`.
- Branch filenames may sanitize path separators, but `working_branch` must preserve the original Git name.
- The project home directly links every branch and repository-level child page.

Keep stable goals, constraints, background, decisions with rationale, verified outcomes, reusable failure lessons, blockers, and concrete next steps. Do not keep chat transcripts, raw command output, facts available directly from code, or secrets.

## 中文

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

知识簇和项目簇只保留一条刻意建立的桥：记忆首页到项目总览。项目事实不得放入知识簇。

### 身份规则

- 项目主页具有 `type: project` 和精确 `github_repo: OWNER/REPO` 字段。
- 一个仓库对应一个文件夹和一个项目主页。
- 分支页具有 `type: branch`、相同 `github_repo` 和精确 `working_branch`。
- 分支文件名可以替换路径分隔符，但 `working_branch` 必须保留原始 Git 名称。
- 项目主页直接链接每个分支页和仓库级子页。

只保留稳定目标、约束、背景、有理由的决策、已验证结果、可复用失败经验、阻塞和具体下一步。不要保存聊天记录、原始命令输出、可直接从代码获得的事实或秘密。
