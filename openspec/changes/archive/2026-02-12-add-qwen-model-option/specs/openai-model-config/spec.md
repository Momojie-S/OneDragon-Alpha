# OpenAI 模型配置规范 - 多 Provider 支持

## MODIFIED Requirements

### Requirement: 模型配置数据结构
系统 SHALL 定义模型配置的数据结构，包含以下字段：
- `name`: 配置名称（用户自定义，如 "DeepSeek 官方"）
- `provider`: 模型提供商（支持 "openai" 或 "qwen"）
- `base_url`: API baseUrl（如 "https://api.deepseek.com"，qwen provider 时可为空）
- `api_key`: API 密钥（需加密存储，qwen provider 时可为空）
- `models`: 模型列表（JSON 数组，每个模型包含以下字段）：
  - `model_id`: 模型 ID（如 "deepseek-chat"）
  - `support_vision`: 该模型是否支持视觉能力（布尔值）
  - `support_thinking`: 该模型是否支持思考能力（布尔值）
- `is_active`: 是否启用（布尔值）
- `oauth_access_token`: OAuth 访问令牌（加密存储，仅 qwen provider）
- `oauth_token_type`: OAuth 令牌类型（如 "Bearer"，仅 qwen provider）
- `oauth_refresh_token`: OAuth 刷新令牌（加密存储，仅 qwen provider）
- `oauth_expires_at`: OAuth 过期时间戳（毫秒，仅 qwen provider）
- `oauth_scope`: OAuth 授权范围（可选，仅 qwen provider）
- `oauth_metadata`: OAuth 额外元数据（JSON，可选，仅 qwen provider）

#### Scenario: 创建 OpenAI 类型的模型配置
- **WHEN** 用户提供了所有必需字段（name、provider="openai"、base_url、api_key、models）
- **AND** models 数组包含至少一个模型对象
- **THEN** 系统 SHALL 创建有效的模型配置对象
- **AND** api_key 字段 SHALL 被标记为敏感信息
- **AND** oauth 相关字段 SHALL 为 NULL

#### Scenario: 创建 Qwen 类型的模型配置
- **WHEN** 用户提供了所有必需字段（name、provider="qwen"、models、oauth_access_token）
- **AND** 用户已完成 OAuth 认证
- **AND** models 数组包含至少一个模型对象
- **THEN** 系统 SHALL 创建有效的模型配置对象
- **AND** base_url 和 api_key 字段 SHALL 为空字符串
- **AND** oauth_access_token SHALL 被加密存储
- **AND** oauth_refresh_token SHALL 被加密存储

#### Scenario: 模型列表为空
- **WHEN** 用户创建配置时未提供任何模型
- **THEN** 系统 SHALL 返回验证错误
- **AND** 错误信息 SHALL 提示至少需要添加一个模型

#### Scenario: 模型对象结构验证
- **WHEN** 用户添加模型时提供了完整的模型对象
- **AND** 模型对象包含 model_id、support_vision、support_thinking 字段
- **THEN** 系统 SHALL 接受该模型对象
- **AND** 保存该模型的能力标识

#### Scenario: 不同模型的能力差异
- **WHEN** 同一个配置下包含多个模型
- **THEN** 每个模型 SHALL 有独立的能力标识
- **AND** 某个模型 support_vision 为 true 时，不影响其他模型
- **AND** 系统 SHALL 能够根据模型 ID 筛选具有特定能力的模型

### Requirement: 模型配置验证
系统 SHALL 在创建或更新模型配置时根据 provider 类型验证字段的有效性。

#### Scenario: OpenAI Provider 验证 baseUrl 格式
- **WHEN** provider 为 "openai"
- **AND** 用户提供的 base_url 不是有效的 URL 格式
- **THEN** 系统 SHALL 返回验证错误
- **AND** 错误信息 SHALL 提示 baseUrl 格式不正确

#### Scenario: OpenAI Provider 验证 API key 非空
- **WHEN** provider 为 "openai"
- **AND** 用户提供的 api_key 为空字符串
- **THEN** 系统 SHALL 返回验证错误
- **AND** 错误信息 SHALL 提示 API key 不能为空

#### Scenario: Qwen Provider 允许空 base_url 和 api_key
- **WHEN** provider 为 "qwen"
- **AND** 用户未提供 base_url 或 api_key
- **THEN** 系统 SHALL 允许这些字段为空
- **AND** 系统 SHALL 验证 oauth_access_token 不为空

#### Scenario: Qwen Provider 验证 OAuth 认证
- **WHEN** provider 为 "qwen"
- **AND** oauth_access_token 为空或 NULL
- **THEN** 系统 SHALL 返回验证错误
- **AND** 错误信息 SHALL 提示请先完成 Qwen 账号认证

#### Scenario: 验证配置名称唯一性
- **WHEN** 用户创建配置时使用了已存在的配置名称
- **THEN** 系统 SHALL 返回验证错误
- **AND** 错误信息 SHALL 提示配置名称已存在

### Requirement: 模型配置激活状态管理
系统 SHALL 支持启用或禁用模型配置，无论 provider 类型。

#### Scenario: 启用 OpenAI 模型配置
- **WHEN** 用户将某个 OpenAI 配置的 is_active 设置为 true
- **THEN** 系统 SHALL 标记该配置为启用状态
- **AND** 该配置 SHALL 可用于模型调用

#### Scenario: 启用 Qwen 模型配置
- **WHEN** 用户将某个 Qwen 配置的 is_active 设置为 true
- **AND** oauth_token 未过期
- **THEN** 系统 SHALL 标记该配置为启用状态
- **AND** 该配置 SHALL 可用于模型调用

#### Scenario: 禁用模型配置
- **WHEN** 用户将某个配置的 is_active 设置为 false
- **THEN** 系统 SHALL 标记该配置为禁用状态
- **AND** 该配置 SHALL 不可用于模型调用

#### Scenario: 多个配置同时启用
- **WHEN** 用户启用了多个模型配置（包括 OpenAI 和 Qwen）
- **THEN** 系统 SHALL 允许所有启用的配置同时可用
- **AND** 用户可选择使用任意一个启用的配置

### Requirement: 敏感信息处理
系统 SHALL 对 API key 和 OAuth token 等敏感信息进行加密存储和脱敏展示。

#### Scenario: 加密存储 API key
- **WHEN** 用户保存 OpenAI 模型配置
- **THEN** 系统 SHALL 对 api_key 进行加密后存储到数据库
- **AND** 明文 api_key SHALL 不出现在日志中

#### Scenario: 加密存储 OAuth access_token
- **WHEN** 用户保存 Qwen 模型配置
- **THEN** 系统 SHALL 对 oauth_access_token 进行加密后存储到数据库
- **AND** 明文 oauth_access_token SHALL 不出现在日志中

#### Scenario: 加密存储 OAuth refresh_token
- **WHEN** 用户保存 Qwen 模型配置
- **THEN** 系统 SHALL 对 oauth_refresh_token 进行加密后存储到数据库
- **AND** 明文 oauth_refresh_token SHALL 不出现在日志中

#### Scenario: 脱敏展示 API key
- **WHEN** 用户查询模型配置列表
- **AND** 配置类型为 OpenAI
- **THEN** 系统 SHALL 返回脱敏后的 api_key（仅显示前 4 位和后 4 位）
- **AND** 完整的 api_key SHALL 不被暴露

#### Scenario: 不暴露 OAuth token
- **WHEN** 用户查询模型配置列表
- **AND** 配置类型为 Qwen
- **THEN** 系统 SHALL 不返回 oauth_access_token
- **AND** 系统 SHALL 不返回 oauth_refresh_token
- **AND** 系统 MAY 返回认证状态（已认证/已过期）

#### Scenario: 更新 OpenAI 配置时保留原 API key
- **WHEN** 用户更新 OpenAI 配置时未提供新的 api_key
- **THEN** 系统 SHALL 保留原有的加密 api_key
- **AND** 不需要用户重新输入完整的 API key

#### Scenario: 更新 Qwen 配置时保留原 OAuth token
- **WHEN** 用户更新 Qwen 配置时未提供新的 oauth_access_token
- **THEN** 系统 SHALL 保留原有的加密 oauth_access_token
- **AND** 系统 SHALL 保留原有的加密 oauth_refresh_token
