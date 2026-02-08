## Why

当前系统需要支持多种大语言模型（LLM）的接入和管理。为了支持 OpenAI 兼容的 API（如 DeepSeek、Moonshot、OpenAI 官方等），需要一个可配置的模型管理模块，使用户能够灵活添加和管理不同的模型提供商及其模型列表。

## What Changes

- **新增 OpenAI 模型配置管理模块**：提供 OpenAI 兼容模型的配置接口和管理能力
  - 支持配置多个不同的 API 提供商
  - 每个配置包含基础字段（baseUrl、apiKey 等）和模型能力标识（视觉、思考等）
  - 每个配置下可管理多个模型 ID
  - 支持添加、编辑、删除、启用/禁用配置
- **数据库持久化**：使用 MySQL 数据库存储所有模型配置
- **前端管理界面**：提供 Vue + Element-Plus 的模型配置管理页面
- **后端 API**：提供 FastAPI 接口用于模型的 CRUD 操作

## Capabilities

### New Capabilities
- `openai-model-config`: 管理 OpenAI 兼容模型的配置信息，支持多配置、多模型，包括 baseUrl、API token、模型列表等
- `openai-model-database-storage`: 使用 MySQL 数据库存储和查询 OpenAI 模型配置
- `openai-model-api`: 提供 RESTful API 用于 OpenAI 模型配置的增删改查操作
- `openai-model-frontend`: Vue 前端页面，提供 OpenAI 模型配置的可视化管理界面

## Impact

**后端代码**:
- 新增 OpenAI 模型配置管理模块（数据模型、数据库操作）
- 新增 FastAPI 路由（模型的 CRUD 接口）
- 数据库表设计（模型配置存储）

**前端代码**:
- 新增模型配置管理页面（Vue 组件）
- 新增 API 调用封装

**现有代码适配**:
- Agent 可能需要支持从数据库加载模型配置（可选）

**依赖项**:
- 后端：现有 MySQL 连接服务
- 前端：Element-Plus 组件库（已有）
- 可能需要新增加密库用于敏感信息存储

**测试**:
- 新增模块的单元测试
- API 集成测试
- 前端组件测试
