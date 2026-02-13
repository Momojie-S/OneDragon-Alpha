# 项目概述

## 项目概述

OneDragon-Alpha 是一个前后端分离的 AI 应用项目。

## 技术栈

### 前端
- **包管理**: pnpm
- **框架**: Vue3
- **UI 组件库**: element-plus + element-plus-x
  - element-plus-x 是基于 element-plus 的 AI 应用组件库

### 后端
- **包管理**: uv
- **框架**: FastAPI
- **服务器**: Uvicorn
- **Agent 框架**: AgentScope
- **数据源**: AKShare

## 目录结构

```
OneDragon-Alpha/
├── src/                # Python 后端代码主入口
├── frontend/           # Vue 前端代码
├── docs/              # 项目文档
└── .env              # 环境变量配置（包含数据库密码等）
```

## 环境说明

### 数据库环境
- 当前项目没有区分开发和生产数据库，所有环境共用同一个数据库实例
- 测试数据清理尤为重要，必须确保测试后正确清理，避免影响开发和使用体验

### 临时文件
- 无论是使用工具还是测试代码，需要创建临时文件时，都在项目根目录下的 `.temp` 文件夹下创建

### 环境变量设置
- 项目所需的环境变量都能在 `.env` 文件中找到
- 使用 `uv run` 命令时，必须使用 `--env-file .env` 参数来加载环境变量
- 不要手动设置 `PYTHONPATH`，使用 `.env` 来加载
