# 项目文档

本文档目录包含 OneDragon-Alpha 项目的各类设计文档和开发指南。

## 文档索引

### 顶层文档

- **[project-overview.md](project-overview.md)** - 项目概览
  - 项目概述和技术栈
  - 目录结构说明
  - 环境配置说明

- **[development-environment.md](development-environment.md)** - 开发环境搭建
  - OpenSpec 工作流工具安装
  - Pyright 语言服务器安装

- **[development-guide.md](development-guide.md)** - 开发规范
  - 后端开发规范（编码风格、类型提示、导入约定等）
  - 前端开发规范
  - 测试策略（单元测试、E2E 测试、测试数据清理）
  - 开发流程（需求开发流程、opsx 使用）

- **[documentation-guide.md](documentation-guide.md)** - 文档规范
  - 文档编写原则（简洁优先、设计导向、无代码示例）
  - 文档组织原则
  - 文档应包含和不应包含的内容

### 架构设计

**[architecture/](architecture/)** - 系统架构和技术选型文档

- **[alpha-architecture.md](architecture/alpha-architecture.md)** - OneDragon-Alpha 架构设计
  - 系统整体架构
  - 技术栈选型理由
  - 模块划分和职责

### 模块文档

**[modules/](modules/)** - 功能模块的设计和接口定义文档

- **[model-config/](modules/model-config/)** - 模型配置模块
  - [model-config.md](modules/model-config/model-config.md) - 模块总览
  - [model-config-api.md](modules/model-config/model-config-api.md) - API 设计
  - [model-config-database.md](modules/model-config/model-config-database.md) - 数据库设计
  - [qwen-model.md](modules/model-config/qwen-model.md) - Qwen 模型集成
  - [model-config-user-guide.md](modules/model-config/model-config-user-guide.md) - 用户使用指南

### 功能文档

**[features/](features/)** - 具体功能的设计思路和实现说明文档

#### 后端功能
**[backend/](features/backend/)** - 后端功能设计
- [chat.md](features/backend/chat.md) - 聊天功能设计
- [mysql_connection_service.md](features/backend/mysql_connection_service.md) - MySQL 连接服务

#### 前端功能
**[frontend/](features/frontend/)** - 前端功能设计
- [chat.md](features/frontend/chat.md) - 聊天界面设计

### 产品手册

**[manual/](manual/)** - 产品使用手册和操作指南（待完善）

### 数据库文档

**[database/](database/)** - 数据库设计和安全要求
- [security-requirements.md](database/security-requirements.md) - 数据库安全需求

## 文档导航

- **开发者**：从 [project-overview.md](project-overview.md) 开始，配置 [development-environment.md](development-environment.md)，然后阅读 [development-guide.md](development-guide.md)
- **架构理解**：查看 [architecture/](architecture/) 目录下的文档
- **功能开发**：在 [features/](features/) 和 [modules/](modules/) 目录下查找对应功能的设计文档
- **文档编写**：参考 [documentation-guide.md](documentation-guide.md) 的规范编写文档
