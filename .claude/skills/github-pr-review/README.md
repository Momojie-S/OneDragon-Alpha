# GitHub PR Review Skill

GitHub Pull Request Review 处理指南。

## 🎯 功能

快速查看 PR 的未解决评论。

## 🚀 使用方法

### 使用脚本

```bash
./.claude/skills/github-pr-review/list-unresolved.sh <pr_number>
```

**示例**:
```bash
./.claude/skills/github-pr-review/list-unresolved.sh 2
```

### 使用 Skill

在 Claude Code 中：

```bash
/github-pr-review
```

## 📋 输出内容

- 未解决评论总数
- 每个评论的详细信息：
  - 文件路径和行号
  - 作者
  - 问题描述
  - 建议修复
  - 评论链接

## 🔄 完整工作流

1. 查看未解决评论
2. 修复代码
3. 运行测试
4. 提交代码
5. 等待 re-review
6. 验证已解决

循环直到所有评论解决。

## 📚 相关资源

- **项目编码规范**: `CLAUDE.md`
- **GitHub CLI**: https://cli.github.com/manual/
- **CodeRabbit**: https://docs.coderabbit.ai/

## 📂 文件结构

```text
.claude/skills/github-pr-review/
├── SKILL.md              # 完整工作流指南
├── README.md             # 本文件
└── list-unresolved.sh    # 列出未解决评论
```

## 👤 作者

Momojie-S

## 📄 许可证

MIT License
