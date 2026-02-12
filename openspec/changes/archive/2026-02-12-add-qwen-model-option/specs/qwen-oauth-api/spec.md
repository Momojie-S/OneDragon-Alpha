# Qwen OAuth 认证 API 规范

## ADDED Requirements

### Requirement: 获取设备码 API

系统 MUST 提供 API 端点用于获取 Qwen OAuth 设备码。

#### Scenario: 成功获取设备码
- **WHEN** 客户端发送 POST 请求到 `/api/qwen/oauth/device-code`
- **THEN** 系统 MUST 返回 HTTP 200 状态码
- **AND** 响应 MUST 包含 `device_code` 字段（用于轮询）
- **AND** 响应 MUST 包含 `user_code` 字段（8位用户码，格式如 "ABCD-1234"）
- **AND** 响应 MUST 包含 `verification_uri` 字段（验证链接）
- **AND** 响应 MUST 包含 `verification_uri_complete` 字段（完整验证链接，包含用户码）
- **AND** 响应 MUST 包含 `expires_in` 字段（过期时间，秒）
- **AND** 响应 MUST 包含 `interval` 字段（轮询间隔，秒）

#### Scenario: 设备码请求失败
- **WHEN** Qwen OAuth 服务返回错误
- **THEN** 系统 MUST 返回 HTTP 500 状态码
- **AND** 响应 MUST 包含 `detail` 字段说明错误原因
- **AND** 错误信息 MUST 使用中文

### Requirement: 轮询认证状态 API

系统 MUST 提供 API 端点用于轮询 Qwen OAuth 认证状态。

#### Scenario: 轮询等待授权
- **WHEN** 客户端发送 GET 请求到 `/api/qwen/oauth/status`
- **AND** 请求参数包含 `device_code`
- **AND** 用户尚未完成授权
- **THEN** 系统 MUST 返回 HTTP 200 状态码
- **AND** 响应 MUST 包含 `status` 字段，值为 "pending"
- **AND** 响应 MAY 包含 `retry_after` 字段（建议重试间隔，毫秒）

#### Scenario: 轮询频率过高时返回 slow_down
- **WHEN** 客户端轮询频率过高
- **THEN** 系统 MUST 返回 HTTP 200 状态码
- **AND** 响应 MUST 包含 `status` 字段，值为 "pending"
- **AND** 响应 MUST 包含 `retry_after` 字段（建议重试间隔，毫秒）
- **AND** `retry_after` 值 MUST 大于当前间隔

#### Scenario: 认证成功
- **WHEN** 用户已完成授权
- **AND** 客户端发送 GET 请求到 `/api/qwen/oauth/status`
- **THEN** 系统 MUST 返回 HTTP 200 状态码
- **AND** 响应 MUST 包含 `status` 字段，值为 "success"
- **AND** 响应 MUST 包含 `token` 对象
- **AND** `token` 对象 MUST 包含 `access_token` 字段
- **AND** `token` 对象 MUST 包含 `refresh_token` 字段
- **AND** `token` 对象 MUST 包含 `expires_at` 字段（过期时间戳，毫秒）
- **AND** `token` 对象 MAY 包含 `resource_url` 字段

#### Scenario: 认证超时
- **WHEN** 设备码已过期
- **AND** 客户端发送 GET 请求到 `/api/qwen/oauth/status`
- **THEN** 系统 MUST 返回 HTTP 408 状态码
- **AND** 响应 MUST 包含 `detail` 字段，说明"认证超时"

#### Scenario: 设备码无效
- **WHEN** 请求参数中的 `device_code` 无效
- **THEN** 系统 MUST 返回 HTTP 400 状态码
- **AND** 响应 MUST 包含 `detail` 字段，说明"设备码无效"

### Requirement: Token 持久化方式

系统 MUST 支持 MySQL 和 JSON 文件两种 token 持久化方式。

#### Scenario: 系统使用 MySQL 持久化
- **WHEN** 系统 START 运行
- **THEN** 系统 MUST 使用 `MySQLTokenPersistence` 实现
- **AND** Token MUST 存储到 `model_configs` 表的 OAuth 字段
- **AND** Token MUST 与模型配置关联

#### Scenario: 保留 JSON 持久化方式
- **WHEN** 其他系统或脚本需要使用 Qwen OAuth
- **THEN** 系统 MUST 保留 `TokenPersistence`（JSON 文件）类
- **AND** JSON 文件路径 MUST 为 `~/.one_dragon_alpha/qwen_oauth_creds.json`
- **AND** JSON 方式 MAY 被 `QwenTokenManager` 单例使用

#### Scenario: MySQL 持久化优先
- **WHEN** 前端通过 API 创建 Qwen 模型配置
- **THEN** 系统 MUST 使用 MySQL 持久化
- **AND** 系统 MUST NOT 写入 JSON 文件
- **AND** JSON 文件 MAY 被 `QwenTokenManager` 用于 CLI 工具

### Requirement: Token 加密存储

系统 MUST 在存储 OAuth token 到数据库前进行加密。

#### Scenario: 存储前加密 access_token
- **WHEN** 系统 SUCCESSFULLY 获取到 OAuth token
- **THEN** 系统 MUST 使用 Fernet 对称加密加密 `access_token`
- **AND** 系统 MUST 使用配置中的 `TOKEN_ENCRYPTION_KEY` 环境变量
- **AND** 加密后的 token MUST 存储到 `model_configs.oauth_access_token` 字段

#### Scenario: 存储前加密 refresh_token
- **WHEN** 系统 SUCCESSFULLY 获取到 OAuth token
- **THEN** 系统 MUST 使用 Fernet 对称加密加密 `refresh_token`
- **AND** 系统 MUST 使用相同的 `TOKEN_ENCRYPTION_KEY`
- **AND** 加密后的 token MUST 存储到 `model_configs.oauth_refresh_token` 字段

#### Scenario: 读取时解密 token
- **WHEN** 系统从数据库读取 OAuth token
- **THEN** 系统 MUST 使用 Fernet 解密 `oauth_access_token` 字段
- **AND** 系统 MUST 使用 Fernet 解密 `oauth_refresh_token` 字段
- **AND** 如果解密失败，MUST 返回错误

#### Scenario: TOKEN_ENCRYPTION_KEY 未配置时使用默认值
- **WHEN** 环境变量 `TOKEN_ENCRYPTION_KEY` 未设置
- **THEN** 系统 MUST 使用硬编码的默认密钥
- **AND** 系统 MUST 记录警告日志，提示应配置独立密钥

### Requirement: OAuth Token 数据库字段

系统 MUST 在 `model_configs` 表中添加 OAuth 相关字段。

#### Scenario: 存储 token 基本信息
- **WHEN** 系统 保存 OAuth token
- **THEN** 系统 MUST 存储加密后的 `access_token` 到 `oauth_access_token` 字段
- **AND** 系统 MUST 存储加密后的 `refresh_token` 到 `oauth_refresh_token` 字段
- **AND** 系统 MUST 存储过期时间戳到 `oauth_expires_at` 字段（毫秒）

#### Scenario: 存储 token 类型
- **WHEN** 系统 保存 OAuth token
- **THEN** 系统 MUST 存储 token 类型到 `oauth_token_type` 字段
- **AND** 对于 Qwen，值 MUST 为 "Bearer"
- **AND** 字段类型 MUST 为 VARCHAR(50)

#### Scenario: 存储 scope 信息
- **WHEN** 系统 保存 OAuth token
- **THEN** 系统 MAY 存储授权的 scope 到 `oauth_scope` 字段
- **AND** 对于 Qwen，值 MAY 为 "openid profile email model.completion"
- **AND** 字段类型 MUST 为 VARCHAR(500)
- **AND** 如果响应中没有 scope，字段 MAY 为 NULL

#### Scenario: 存储额外元数据
- **WHEN** OAuth token 响应包含额外字段
- **THEN** 系统 MUST 存储额外字段到 `oauth_metadata` JSON 字段
- **AND** 对于 Qwen，MUST 包含 `resource_url` 字段（如果存在）
- **AND** JSON 格式 MUST 有效

### Requirement: Token 刷新

系统 MUST 自动刷新即将过期的 OAuth token。

#### Scenario: 检测到 token 接近过期
- **WHEN** 系统 使用 Qwen 模型配置
- **AND** `oauth_expires_at` 时间戳小于当前时间 + 5分钟
- **THEN** 系统 MUST 使用 `oauth_refresh_token` 刷新 token
- **AND** 系统 MUST 更新 `oauth_access_token` 为新 token
- **AND** 系统 MUST 更新 `oauth_expires_at` 为新的过期时间
- **AND** 如果响应包含新的 `refresh_token`，MUST 同时更新

#### Scenario: Refresh token 过期
- **WHEN** `oauth_refresh_token` 已过期或无效
- **THEN** 系统 MUST 返回认证失败错误
- **AND** 错误信息 MUST 提示用户重新登录
- **AND** 系统 MUST 清除数据库中的 OAuth token 字段

### Requirement: 关联 Token 到模型配置

系统 MUST 将 OAuth token 关联到创建的模型配置。

#### Scenario: 创建 Qwen 配置时保存 token
- **WHEN** 用户完成 OAuth 认证后提交表单
- **AND** 表单 provider 字段为 "qwen"
- **THEN** 系统 MUST 将 OAuth token 保存到新创建的配置记录
- **AND** 系统 MUST 设置 `base_url` 为空字符串
- **AND** 系统 MUST 设置 `api_key` 为空字符串

#### Scenario: 删除配置时清除关联 token
- **WHEN** 用户删除 Qwen 模型配置
- **THEN** 系统 MUST 同时删除该配置的 OAuth token
- **AND** 数据库记录中的 OAuth 字段 MUST 被设置为 NULL

### Requirement: OAuth 会话管理

系统 MUST 在 OAuth 流程中维护会话状态。

#### Scenario: 生成唯一的会话 ID
- **WHEN** 客户端请求设备码
- **THEN** 系统 MUST 生成唯一的会话 ID
- **AND** 响应 MUST 包含 `session_id` 字段
- **AND** 会话 ID MUST 用于后续的状态轮询

#### Scenario: 会话超时后清理
- **WHEN** OAuth 会话超过 15 分钟未完成
- **THEN** 系统 MUST 标记会话为过期
- **AND** 后续轮询请求 MUST 返回超时错误
- **AND** 系统 MUST 清理会话相关的临时数据

### Requirement: API 安全

系统 MUST 保护 OAuth API 端点。

#### Scenario: 限制设备码请求频率
- **WHEN** 同一 IP 地址在 1 分钟内请求超过 10 次设备码
- **THEN** 系统 MUST 返回 HTTP 429 状态码
- **AND** 响应 MUST 包含 `Retry-After` 头部

#### Scenario: 验证状态轮询权限
- **WHEN** 客户端轮询认证状态
- **THEN** 系统 MUST 验证 `session_id` 或 `device_code` 的有效性
- **AND** 如果会话不存在，MUST 返回 HTTP 404 状态码

#### Scenario: 不在日志中记录敏感信息
- **WHEN** 系统 记录 OAuth 相关日志
- **THEN** 日志 MUST NOT 包含完整的 `access_token`
- **AND** 日志 MUST NOT 包含完整的 `refresh_token`
- **AND** 日志 MAY 包含脱敏后的 token（仅前 8 位和后 4 位）
