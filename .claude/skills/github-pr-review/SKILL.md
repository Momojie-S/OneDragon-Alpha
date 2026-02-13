---
name: github-pr-review
description: 快速查看和处理 GitHub PR 的未解决审查评论。
license: MIT
compatibility: Requires gh CLI and GitHub repo.
metadata:
  author: Momojie-S
  version: "2.2"
  generatedBy: "1.1.1"
---

# GitHub PR Review 指南

快速查看和处理 GitHub PR 的未解决审查评论。

## 📍 脚本位置

所有脚本位于**项目根目录**下的 `.claude/skills/github-pr-review/` 目录：

```
项目根目录/
└── .claude/
    └── skills/
        └── github-pr-review/
            ├── list-unresolved.sh      # 查看未解决评论
            ├── reply-comment.sh        # 回复评论
            └── resolve-thread.sh       # 关闭评论线程
```

**重要**：所有命令都必须在**项目根目录**下执行。

## 🎯 功能

使用 GitHub GraphQL API 查询 PR 中未解决的审查评论，并提供清晰的汇总信息。

## 🚀 使用方法

> **前提**：以下命令需要在**项目根目录**下执行。

### 查看未解决的评论

```bash
./.claude/skills/github-pr-review/list-unresolved.sh <pr_number>
```

**示例**：
```bash
./.claude/skills/github-pr-review/list-unresolved.sh 2
```

## 💬 处理评论工作流

### 第一轮：回复评论

```bash
./.claude/skills/github-pr-review/reply-comment.sh <pr_number> <comment_id> "回复内容"
```

**注意**：
- `comment_id` 是评论的数字 ID（如 `2786061437`）
- 不是线程 ID（如 `PRRT_kwDOP1X2Vs5tpqvt`）
- 可以从 `list-unresolved.sh` 的输出或 `gh api` 查询结果中找到
- 回复后不要立即关闭，等待 reviewer 确认或继续讨论

### 第二轮：查看并决定是否关闭

1. 查看未解决评论：
   ```bash
   ./.claude/skills/github-pr-review/list-unresolved.sh <pr_number>
   ```

2. 判断是否可以关闭：

   **✅ 可以关闭的情况**：
   - 已修复问题，reviewer 没有新回复
   - 解释了不需要修改的原因，reviewer 认可（没有新回复）
   - Reviewer 最后一条评论表示认可或问题已解决

   **❌ 不应该关闭的情况**：
   - Reviewer 还有疑问或新问题
   - 还在讨论中
   - 修复后等待 reviewer 验证

3. 如果确定可以关闭，使用脚本关闭：
   ```bash
   ./.claude/skills/github-pr-review/resolve-thread.sh <pr_number> <comment_id>
   ```

   **重要**：`comment_id` 必须是数字 ID（如 `2786061437`），不是线程 ID

### 注意事项

- **礼貌且专业**：提供技术依据或项目规范支持
- **确实问题应修复**：不要拒绝合理的建议
- **等待确认**：给 reviewer 确认的机会

## 🔀 合并 PR

### 合并方式

本项目默认使用 **squash merge** 方式合并 PR：

```bash
gh pr merge <pr_number> --squash --subject "提交标题" --body "提交说明" --delete-branch
```

**示例**：
```bash
gh pr merge 2 --squash \
  --subject "feat: Add new feature" \
  --body "Implemented the new feature with tests" \
  --delete-branch
```

### 为什么使用 Squash Merge

- **保持历史清洁**：将多个提交合并为一个
- **避免合并提交**：不产生 "Merge branch 'xxx' into 'main'" 提交
- **便于回滚**：单个提交便于理解整个 PR 的改动
- **符合项目规范**：本项目推荐使用此方式


