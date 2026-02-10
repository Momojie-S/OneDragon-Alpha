# Spec: 后端聊天接口模型选择

本文档定义后端聊天接口集成模型配置系统的需求规范。

## ADDED Requirements

### Requirement: 聊天请求必须指定模型配置 ID 和模型 ID

聊天接口必须要求客户端在每次请求时提供有效的模型配置 ID 和模型 ID。系统不得使用默认配置、默认模型或环境变量作为后备方案。

**Rationale**: 强制客户端明确指定模型配置和具体模型，确保模型选择的可预测性和可追踪性，避免因配置缺失导致的意外行为。

#### Scenario: 缺少 model_config_id 参数

- **WHEN** 客户端发送聊天请求时未提供 `model_config_id` 字段
- **THEN** 系统必须返回 HTTP 400 错误
- **AND** 错误消息必须明确指出缺少必填字段 `model_config_id`

#### Scenario: 缺少 model_id 参数

- **WHEN** 客户端发送聊天请求时未提供 `model_id` 字段
- **THEN** 系统必须返回 HTTP 400 错误
- **AND** 错误消息必须明确指出缺少必填字段 `model_id`

#### Scenario: 提供了有效的 model_config_id 和 model_id

- **WHEN** 客户端发送聊天请求时提供了有效的 `model_config_id` 和 `model_id`
- **THEN** 系统必须接受请求并处理该消息
- **AND** 系统必须使用该配置和模型 ID 指定的模型进行响应

---

### Requirement: 系统必须验证模型配置和模型 ID 的有效性

在处理聊天请求之前，系统必须验证提供的模型配置 ID 是否存在、是否启用，以及提供的模型 ID 是否在该配置的 `models` 数组中。

**Rationale**: 确保系统使用有效的配置和模型，避免在运行时因配置无效或模型不存在导致失败。

#### Scenario: 模型配置不存在

- **WHEN** 客户端提供的 `model_config_id` 在数据库中不存在
- **THEN** 系统必须返回 HTTP 404 错误
- **AND** 错误消息必须明确指出模型配置不存在

#### Scenario: 模型配置已禁用

- **WHEN** 客户端提供的 `model_config_id` 存在但 `is_active` 为 `false`
- **THEN** 系统必须返回 HTTP 400 错误
- **AND** 错误消息必须明确指出该模型配置已禁用

#### Scenario: 模型 ID 不在配置中

- **WHEN** 客户端提供的 `model_id` 不在该配置的 `models` 数组中
- **THEN** 系统必须返回 HTTP 400 错误
- **AND** 错误消息必须明确指出该模型 ID 不在此配置中
- **AND** 错误消息必须列出该配置中可用的模型 ID 列表

#### Scenario: 模型配置和模型 ID 都有效

- **WHEN** 客户端提供的 `model_config_id` 存在、已启用且 `model_id` 在 `models` 数组中
- **THEN** 系统必须继续处理请求
- **AND** 系统必须使用指定的模型 ID 创建 Agent

---

### Requirement: Session 必须根据模型配置 ID 和模型 ID 重建 Agent

当接收到新的 `model_config_id` 或 `model_id` 时，Session 必须重新创建主 Agent 和分析 Agent。如果两者都与上次请求相同，则复用现有 Agent。

**Rationale**: AgentScope 的 ReActAgent 不支持运行时更换模型，重建 Agent 是安全可靠的方式。复用机制可避免不必要的性能开销。

#### Scenario: 首次聊天请求

- **WHEN** Session 首次接收到聊天请求（无论 `model_config_id` 和 `model_id` 为何值）
- **THEN** 系统必须使用该配置和模型 ID 创建主 Agent
- **AND** 系统必须使用相同的配置和模型 ID 创建分析 Agent（用于 `analyse_by_code` 工具）
- **AND** 系统必须缓存当前的 `model_config_id`、`model_id` 和 Agent 实例

#### Scenario: 模型配置 ID 发生变化

- **WHEN** Session 接收到聊天请求，且 `model_config_id` 与缓存的值不同
- **THEN** 系统必须从数据库读取新配置
- **AND** 系统必须使用新配置和新 `model_id` 重新创建主 Agent
- **AND** 系统必须使用新配置和新 `model_id` 重新创建分析 Agent
- **AND** 系统必须更新缓存的 `model_config_id`、`model_id` 和 Agent 实例
- **AND** 旧的 Agent 实例必须被释放（允许垃圾回收）

#### Scenario: 模型 ID 发生变化（配置相同）

- **WHEN** Session 接收到聊天请求，且 `model_config_id` 相同但 `model_id` 不同
- **THEN** 系统必须使用缓存的配置和新的 `model_id` 重新创建主 Agent
- **AND** 系统必须使用缓存的配置和新的 `model_id` 重新创建分析 Agent
- **AND** 系统必须更新缓存的 `model_id` 和 Agent 实例
- **AND** 旧的 Agent 实例必须被释放（允许垃圾回收）

#### Scenario: 模型配置 ID 和模型 ID 都未变化

- **WHEN** Session 接收到聊天请求，且 `model_config_id` 和 `model_id` 都与缓存的值相同
- **THEN** 系统必须复用现有的主 Agent 实例
- **AND** 系统不得重新创建 Agent
- **AND** 系统必须直接处理消息

---

### Requirement: 系统必须支持多种模型 Provider

系统必须根据模型配置的 `provider` 字段创建对应的模型实例。当前必须支持 `openai` 和 `qwen` 两种 provider。

**Rationale**: 支持多种模型提供商，允许用户根据需求选择不同的 AI 服务。

#### Scenario: 创建 OpenAI 兼容模型

- **WHEN** 模型配置的 `provider` 为 `openai`
- **THEN** 系统必须创建 `OpenAIChatModel` 实例
- **AND** 系统必须使用配置中的 `base_url`、`api_key` 和 `model_id` 初始化模型
- **AND** 模型必须能够正常调用 API

#### Scenario: 创建 Qwen 模型

- **WHEN** 模型配置的 `provider` 为 `qwen`
- **THEN** 系统必须创建 `QwenChatModel` 实例
- **AND** 系统必须使用 `QwenChatModel` 的 OAuth 认证机制（不需要 API Key）
- **AND** 系统必须使用配置中的 `model_id` 初始化模型
- **AND** 模型必须能够正常调用 API

#### Scenario: 不支持的 Provider

- **WHEN** 模型配置的 `provider` 既不是 `openai` 也不是 `qwen`
- **THEN** 系统必须返回 HTTP 500 错误
- **AND** 错误消息必须明确指出不支持的 provider 类型
- **AND** 系统必须记录错误日志

---

### Requirement: 分析 Agent 必须使用与主 Agent 相同的模型配置和模型 ID

### Requirement: 系统必须在每次请求时从数据库读取配置

系统不得缓存模型配置。每次处理聊天请求时，如果需要创建或重建 Agent，必须从数据库读取最新的配置信息。

**Rationale**: 确保使用最新的配置，允许管理员在运行时更新配置而无需重启服务。符合开发阶段的需求（性能优化可在后续阶段进行）。

#### Scenario: 配置在会话期间被更新

- **GIVEN** 一个活跃的 Session 正在使用配置 ID 为 `1` 的模型配置
- **AND** 管理员更新了配置 ID 为 `1` 的 `api_key`
- **WHEN** 客户端发送新的聊天请求并使用相同的 `model_config_id = 1`
- **THEN** 系统必须从数据库读取最新的配置
- **AND** 系统必须使用更新后的 `api_key` 重新创建 Agent
- **AND** 新的聊天请求必须使用更新后的配置

---

### Requirement: 分析 Agent 必须使用与主 Agent 相同的模型配置和模型 ID

当 `TushareSession` 创建分析 Agent（用于 `analyse_by_code` 工具）时，必须使用与主 Agent 相同的模型配置和模型 ID。

**Rationale**: 保持会话的一致性，确保主对话和代码分析使用相同的模型能力。

#### Scenario: 创建分析 Agent

- **WHEN** 主 Agent 调用 `analyse_by_code` 工具
- **THEN** 系统必须创建分析 Agent
- **AND** 分析 Agent 必须使用当前缓存的 `model_config_id` 对应的配置
- **AND** 分析 Agent 必须使用当前缓存的 `model_id`
- **AND** 如果主 Agent 尚未创建，系统必须返回错误

---

### Requirement: Session 必须维护模型配置和模型状态

Session 必须在实例级别维护当前的 `model_config_id`、`model_id` 和对应的 Agent 实例，以便在后续请求中进行比较和复用。

**Rationale**: 实现 Agent 复用机制，避免在 `model_config_id` 和 `model_id` 未变化时重建 Agent。

#### Scenario: Session 初始化

- **WHEN** 创建新的 `TushareSession` 实例
- **THEN** 系统必须初始化 `_current_model_config_id` 为 `None`
- **AND** 系统必须初始化 `_current_model_id` 为 `None`
- **AND** 系统必须初始化 `_current_agent` 为 `None`
- **AND** 系统必须初始化 `_analyse_by_code_agent_map` 为空字典

#### Scenario: Agent 创建后更新状态

- **WHEN** 系统使用 `model_config_id = X` 和 `model_id = Y` 创建了主 Agent
- **THEN** 系统必须设置 `_current_model_config_id = X`
- **AND** 系统必须设置 `_current_model_id = Y`
- **AND** 系统必须设置 `_current_agent` 为新创建的 Agent 实例
