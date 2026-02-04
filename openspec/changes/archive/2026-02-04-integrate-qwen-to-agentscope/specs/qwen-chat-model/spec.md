# Qwen 聊天模型规范

## ADDED Requirements

### Requirement: 继承 OpenAIChatModel

`QwenChatModel` 必须继承 AgentScope 的 `OpenAIChatModel`，复用其核心功能。由于 Qwen API 完全兼容 OpenAI API 格式，继承关系可以实现最大化的代码复用。该类应能够在任何使用 `OpenAIChatModel` 的场景下无缝替换。

#### Scenario: 类继承关系
- **WHEN** 应用程序创建 `QwenChatModel` 实例
- **THEN** 该实例是 `OpenAIChatModel` 的子类
- **AND** 该实例支持 `OpenAIChatModel` 的所有公共方法
- **AND** 该实例可以替换 `OpenAIChatModel` 使用

### Requirement: 使用 OAuth Token 作为 API Key

系统必须使用从 `QwenTokenManager` 获取的 OAuth token 作为 API key。`QwenChatModel` 在初始化时应从 `QwenTokenManager` 获取 token，并将其传递给父类的 `api_key` 参数。API base URL 固定为 "https://portal.qwen.ai/v1"，不支持自定义。

#### Scenario: 初始化时获取 token
- **WHEN** 应用程序创建 `QwenChatModel` 实例
- **THEN** 系统调用 `QwenTokenManager.get_access_token()` 获取 token
- **AND** 系统将 token 传递给父类 `OpenAIChatModel` 的 `api_key` 参数
- **AND** 系统使用固定的 API base URL "https://portal.qwen.ai/v1"

#### Scenario: Token 在初始化后不可用
- **WHEN** `QwenTokenManager` 无法提供有效的 token（如未认证）
- **THEN** 系统抛出 `QwenTokenNotAvailableError` 异常
- **AND** 异常信息提示用户先完成 OAuth 认证

### Requirement: 模型调用前 token 验证

系统必须在每次模型调用前验证 token 有效性，必要时触发刷新。由于 OpenAI client 在初始化后无法动态更新 API key，系统需要在检测到 token 过期时重新创建 client。该过程对调用者透明，不应影响正常使用。

#### Scenario: Token 有效时直接调用
- **WHEN** 应用程序调用模型的 `__call__` 或 `_call` 方法
- **AND** 当前 token 未过期
- **THEN** 系统直接使用现有的 OpenAI client 进行调用
- **AND** 系统不触发 token 刷新

#### Scenario: Token 过期时刷新
- **WHEN** 应用程序调用模型的 `__call__` 或 `_call` 方法
- **AND** 当前 token 已过期
- **THEN** 系统调用 `QwenTokenManager.refresh_token()` 刷新 token
- **AND** 系统重新创建 OpenAI client，使用新的 token
- **AND** 系统继续执行模型调用

#### Scenario: Token 刷新失败
- **WHEN** token 刷新失败（如 refresh_token 无效）
- **THEN** 系统抛出 `QwenTokenRefreshError` 异常
- **AND** 异常信息包含原始错误原因
- **AND** 异常信息提示用户重新进行 OAuth 认证

### Requirement: 支持多模型类型

系统必须支持配置不同的 Qwen 模型类型。Qwen 提供多种模型，如 Coder 模型专注于代码生成，Vision 模型支持图像输入。系统应支持通过 model_name 参数指定模型类型，并自动添加正确的 ID 前缀。

#### Scenario: Coder 模型
- **WHEN** 应用程序指定 `model_name="coder-model"`
- **THEN** 系统使用完整模型 ID "qwen-portal/coder-model"
- **AND** 该模型支持文本输入和输出

#### Scenario: Vision 模型
- **WHEN** 应用程序指定 `model_name="vision-model"`
- **THEN** 系统使用完整模型 ID "qwen-portal/vision-model"
- **AND** 该模型支持文本和图像输入

#### Scenario: 自定义模型名称
- **WHEN** 应用程序指定自定义的 `model_name`
- **THEN** 系统使用指定的模型 ID（需添加 "qwen-portal/" 前缀，如果未包含）

### Requirement: 模型配置管理

系统必须支持通过配置文件或环境变量配置模型参数。配置应包括模型名称、OAuth 客户端 ID 和 API 基础 URL 等。系统应支持多种配置来源，并按照明确的优先级合并配置。

#### Scenario: 通过配置文件配置
- **WHEN** 配置文件定义了 Qwen 模型配置
- **THEN** 系统从配置文件读取 model_name、client_id 等参数
- **AND** 系统使用读取的参数创建 `QwenChatModel` 实例

#### Scenario: 通过环境变量配置
- **WHEN** 环境变量设置了 `QWEN_MODEL_NAME` 和 `QWEN_CLIENT_ID`
- **THEN** 系统从环境变量读取配置参数
- **AND** 系统使用读取的参数创建 `QwenChatModel` 实例

#### Scenario: 配置优先级
- **WHEN** 同时存在配置文件和环境变量
- **THEN** 构造函数参数优先级最高
- **AND** 环境变量优先级次之
- **AND** 配置文件优先级最低

### Requirement: 兼容 AgentScope 模型接口

系统必须完全兼容 AgentScope 的模型接口规范。`QwenChatModel` 应能与 AgentScope 的消息格式化器、流式输出和工具调用等功能配合使用，无需额外适配。

#### Scenario: 格式化器兼容
- **WHEN** 应用程序使用 `OpenAIChatFormatter` 与 `QwenChatModel` 配合
- **THEN** 系统正常工作，无需额外配置
- **AND** 消息格式与 OpenAI 格式一致

#### Scenario: 流式输出支持
- **WHEN** 应用程序启用流式输出（stream=True）
- **THEN** 系统支持流式返回模型响应
- **AND** 流式输出格式与 `OpenAIChatModel` 一致

#### Scenario: 工具调用支持
- **WHEN** 应用程序使用 AgentScope 的工具调用功能
- **THEN** 系统支持函数调用（function calling）
- **AND** 工具调用格式与 OpenAI 兼容

### Requirement: 错误处理

系统必须正确处理 Qwen API 返回的错误，并将其转换为适当的异常。错误应包括认证错误、限流错误和服务器错误等类型。异常信息应清晰明确，帮助用户快速定位问题。

#### Scenario: API 认证错误
- **WHEN** Qwen API 返回 401 未授权错误
- **THEN** 系统抛出 `QwenAuthenticationError` 异常
- **AND** 异常信息提示 token 可能已过期

#### Scenario: API 限流错误
- **WHEN** Qwen API 返回 429 限流错误
- **THEN** 系统抛出 `QwenRateLimitError` 异常
- **AND** 异常信息包含重试时间（如果 API 返回）

#### Scenario: API 服务器错误
- **WHEN** Qwen API 返回 5xx 服务器错误
- **THEN** 系统抛出 `QwenServerError` 异常
- **AND** 异常信息包含 HTTP 状态码和错误详情
