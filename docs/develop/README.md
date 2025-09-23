# 开发指南

## 目录结构

```text
OneDragon-Alpha/
├── src/               # Python后端代码主入口
├── frontend/          # Vue前端代码
├── docs/             # 项目文档
```

## Vibe Coding

你可以通过建立硬链接的方式放置到你的AI助手读取位置

- Gemini - `New-Item -ItemType HardLink -Path "GEMINI.md" -Target "docs/develop/spec/agent_guidelines.md"`
- Qwen - `New-Item -ItemType HardLink -Path "QWEN.md" -Target "docs/develop/spec/agent_guidelines.md"`
- Claude Code - `New-Item -ItemType HardLink -Path "CLAUDE.md" -Target "docs/develop/spec/agent_guidelines.md"`
- Roo Code - `New-Item -ItemType HardLink -Path " .roo/rules-code/project.md" -Target "docs/develop/spec/agent_guidelines.md"`