---
type: system-template
status: active
---

# 可复用经验模板

← [[10-memory/reusable/index|可复用经验索引]]

## 何时创建经验

只保留经过验证且能够迁移的方法。未验证想法留在项目“开放问题”中。先搜索已有经验。项目事件留在项目笔记，通用方法保存在此处。不复制聊天记录或秘密。

## 主题页面

```markdown
---
type: reusable-memory
status: verified
summary: 用一句话描述问题与结果
keywords: 问题 技术 环境
source_repo: OWNER/REPOSITORY
source_branch: exact-branch
source_note: 20-projects/repository/branch-page.md
verified_on: YYYY-MM-DD
---

# 主题

← [[10-memory/reusable/index|可复用经验索引]]

## 适用条件
说明问题、环境、版本和前提。

## 方法与理由
说明什么方法有效及其原因，不复制项目特有进度。

## 限制与失败方式
说明不适用场景和已知失败方案。

## 验证依据
说明实际验证了什么，以及在哪里找到支持结果。
```

使用单行 frontmatter 字段。`source_note` 是来源项目主页或其直接链接子页相对知识库的精确路径。保留来源的精确分支；仓库级笔记的 `source_branch` 留空。自定义布局需适配链接与路径。来源字段是普通溯源信息，不使用 Wiki 链接，因此不改变原有图谱桥接关系。

## 维护方式

来源是本地项目时，用 `source_project_id` 替换 `source_repo`，填写已有登记 ID；来源身份字段必须且只能填一种。普通文件夹的项目主页来源将 `source_branch` 留空，本地 Git 分支笔记则保留真实精确分支名。停用的本地来源不参与检索。

在索引中添加摘要与链接，并从记忆首页链接索引。只有实际验证后才更新 `verified_on`，单纯文字编辑不更新时间。保留冲突的适用条件，使用前重新核对。过时经验设为 `status: retired`，保留文件并标记索引条目；不得悄悄覆盖相反证据，也不自动移动或删除笔记。
