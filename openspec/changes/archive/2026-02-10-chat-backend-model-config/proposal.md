# Proposal: 后端聊天接口集成模型配置

## Why

当前后端聊天接口（`/chat/stream`）使用硬编码的环境变量来配置 AI 模型，无法动态切换模型配置。虽然前端已经实现了模型选择器，且后端已有完整的模型配置管理系统（数据库表 `model_configs` 和完整的 CRUD API），但聊天接口尚未集成该系统。这导致用户在前端选择的模型配置无法实际应用到聊天会话中，需要在后端实现模型配置的动态加载和应用。

## What Changes

- **BREAKING**: 修改 `ChatRequest` API，添加两个必填字段：
  - `model_config_id: int` - 指定模型配置 ID
  - `model_id: str` - 指定配置中的具体模型 ID（必须是配置的 `models` 数组中的一个）
- 创建 `ModelFactory` 工厂类，根据模型配置和模型 ID 动态创建 AgentScope 模型实例（支持 OpenAI 和 Qwen 两种 provider）
- 修改 `TushareSession`，实现模型切换机制：
  - Session 级别缓存当前的 `model_config_id`、`model_id` 和 Agent 实例
  - 每次聊天请求时对比传入的 `model_config_id` 和 `model_id` 与缓存的值
  - 如果任一不同，则重新创建主 Agent 和分析 Agent（使用新的配置和模型）
  - 如果都相同，复用现有 Agent，避免不必要的重建开销
- 修改 `Session` 基类，在 `chat` 方法签名中添加 `model_config_id` 和 `model_id` 参数
- 修改聊天路由 `/chat/stream`，传递 `model_config_id` 和 `model_id` 参数并在调用 Session 前验证有效性
- 添加数据库会话依赖注入到聊天路由，支持访问模型配置服务以验证配置存在性、启用状态和模型 ID 有效性
- 实现运行时模型切换：同一会话的不同轮次可以使用不同的模型配置或不同的模型（通过 Agent 重建机制）
- **前端实现**：创建双层模型选择器组件，第一层选择模型配置，第二层选择该配置下的具体模型

## Capabilities

### New Capabilities

- **chat-backend-model-selection**: 后端聊天接口的模型选择能力。支持在每次聊天请求时通过 `model_config_id` 指定模型配置，通过 `model_id` 指定具体模型。后端根据配置和模型 ID 动态创建模型实例并应用到聊天会话中。

- **chat-frontend-model-selector**: 前端双层模型选择器。第一层选择模型配置（显示配置名称和模型数量），第二层选择该配置下的具体模型（显示模型 ID 和能力标签）。

### Modified Capabilities

无（现有能力的需求不变，只是实现从硬编码改为从数据库读取）

## Impact

**受影响的代码模块**:
- `src/one_dragon_alpha/server/chat/router.py` - 修改 `ChatRequest` 添加 `model_config_id` 和 `model_id` 字段，添加数据库会话依赖
- `src/one_dragon_alpha/session/session.py` - 修改 `chat` 方法签名，添加 `model_config_id` 和 `model_id` 参数
- `src/one_dragon_alpha/agent/tushare/tushare_session.py` - 修改 Agent 创建逻辑，根据 `model_config_id` 和 `model_id` 动态创建模型
- `src/one_dragon_agent/core/model/` - 新增 `model_factory.py` 工厂类

**前端代码模块**:
- `frontend/src/components/` - 新增双层模型选择器组件 `DualModelSelector.vue`
- `frontend/src/views/ChatAnalysis.vue` - 集成双层模型选择器，传递 `model_config_id` 和 `model_id`

**API 变更**:
- `POST /chat/stream` - 请求体新增必填字段 `model_config_id: int` 和 `model_id: str`

**数据库依赖**:
- 依赖现有的 `model_configs` 表和 `ModelConfigService`

**依赖项**:
- 无新增外部依赖，使用现有的 AgentScope 和 SQLAlchemy

**系统影响**:
- 每次聊天请求会查询数据库获取模型配置（不缓存，符合开发阶段需求）
- 前端需要传递 `model_config_id` 和 `model_id` 参数
- 前端需要替换现有的 ModelSelector 为双层选择器
