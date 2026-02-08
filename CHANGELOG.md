# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### 模型配置管理系统

- **后端模块** (`src/one_dragon_agent/core/model/`)
  - `models.py` - Pydantic 数据模型定义
    - `ModelInfo` - 模型信息（ID、视觉能力、思考能力）
    - `ModelConfigCreate` - 创建配置请求
    - `ModelConfigUpdate` - 更新配置请求（支持乐观锁）
    - `ModelConfigResponse` - 配置响应（不包含 api_key）
    - `PaginatedModelConfigResponse` - 分页响应
    - `TestConnectionRequest/Response` - 测试连接

  - `repository.py` - 数据库访问层
    - 创建、查询、更新、删除配置
    - 分页查询（支持过滤）
    - 乐观锁机制（使用 `updated_at` 字段）

  - `service.py` - 业务逻辑层
    - 配置验证（名称唯一性、URL 格式、provider 验证）
    - 测试连接功能（通过 POST 请求验证 API 可用性）

  - `router.py` - FastAPI 路由
    - `POST /api/models/configs` - 创建配置
    - `GET /api/models/configs` - 获取配置列表（分页、过滤）
    - `GET /api/models/configs/{id}` - 获取单个配置
    - `PUT /api/models/configs/{id}` - 更新配置
    - `DELETE /api/models/configs/{id}` - 删除配置
    - `PATCH /api/models/configs/{id}/status` - 切换启用状态
    - `POST /api/models/configs/test-connection` - 测试连接

  - `migrations/` - 数据库迁移脚本
    - 创建 `model_configs` 表
    - 添加索引（idx_name, idx_provider, idx_is_active）

- **前端模块** (`frontend/src/`)
  - `services/modelApi.ts` - TypeScript API 服务
    - 完整的 CRUD 操作封装
    - 类型安全的接口定义
    - 统一错误处理

  - `views/model-management/ModelConfigList.vue` - 配置列表页
    - 表格展示（配置名称、Provider、Base URL、模型数量、启用状态）
    - 分页组件
    - 过滤器（启用状态、Provider）
    - 操作按钮（新建、编辑、删除、启用/禁用）

  - `views/model-management/components/ModelConfigDialog.vue` - 配置对话框
    - 创建/编辑表单
    - 模型列表管理（添加、编辑、删除模型）
    - 表单验证
    - 测试连接功能

  - `router/index.ts` - 添加 `/model-management` 路由

- **测试** (103 个测试用例全部通过)
  - `tests/one_dragon_agent/core/model/test_models.py` - 数据模型测试
  - `tests/one_dragon_agent/core/model/test_repository.py` - 仓库层测试
  - `tests/one_dragon_agent/core/model/test_service.py` - 服务层测试
  - `tests/one_dragon_agent/core/model/test_api.py` - API 集成测试
  - `tests/one_dragon_agent/core/model/test_integration.py` - 集成测试
  - `frontend/src/services/__tests__/modelApi.test.ts` - 前端 API 测试

### Changed

- 主应用注册模型配置路由

### Fixed

- 修复测试连接功能，改用 POST 请求到 `/v1/chat/completions` 端点
- 修复前端 API 调用路径（使用 `/api/models/configs` 前缀）

### Security

- API Key 在响应中被过滤，不返回给前端
- 数据库存储加密敏感信息

---

## [0.1.0] - 2025-01-XX

### Added

- 初始项目结构
- MySQL 连接服务
- 基础 Agent 框架
- Qwen 模型集成
