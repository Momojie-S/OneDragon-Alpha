# Qwen OAuth 2.0 设备码认证规范

## ADDED Requirements

### Requirement: 设备码授权流程启动

系统必须支持 OAuth 2.0 设备码授权流程（RFC 8628），允许用户在浏览器中完成认证。系统应向 Qwen OAuth 端点请求设备码和用户码，并持续轮询直到用户完成授权或超时。该流程适用于无浏览器环境或需要分离设备交互的场景。

#### Scenario: 成功获取设备码
- **WHEN** 应用程序调用 `get_device_code()` 方法
- **THEN** 系统向 Qwen OAuth 端点发送 POST 请求
- **AND** 系统返回设备码（device_code）、用户码（user_code）和验证 URI（verification_uri）
- **AND** 系统返回过期时间（expires_in）和轮询间隔（interval）
- **AND** 用户码为 8 位字符，易于用户手动输入

#### Scenario: 设备码请求失败
- **WHEN** Qwen OAuth 服务不可用或返回错误
- **THEN** 系统抛出 `QwenOAuthError` 异常
- **AND** 异常信息包含错误描述

### Requirement: PKCE 流程实现

系统必须使用 PKCE（Proof Key for Code Exchange）增强安全性。PKCE 通过在客户端生成 code_verifier 和 code_challenge，防止授权码拦截攻击。系统应使用 SHA256 哈希算法生成 challenge，确保只有原始客户端能够完成授权。

#### Scenario: 生成 code_challenge 和 code_verifier
- **WHEN** 应用程序初始化 OAuth 流程
- **THEN** 系统生成 32 字节随机码作为 code_verifier
- **AND** 系统使用 SHA256 哈希算法计算 code_challenge
- **AND** code_challenge 和 code_verifier 使用 base64url 编码

#### Scenario: 设备码请求包含 PKCE 参数
- **WHEN** 应用程序请求设备码
- **THEN** 请求包含 code_challenge 参数
- **AND** 请求包含 code_challenge_method 参数，值为 "S256"

### Requirement: 用户授权轮询

系统必须轮询 Qwen OAuth 端点，等待用户完成授权。轮询应按照服务器返回的 interval 进行，避免过于频繁的请求。当收到 "slow_down" 错误时，系统应增加轮询间隔。如果用户在 expires_in 时间内未完成授权，系统应停止轮询并报告超时。

#### Scenario: 等待用户授权
- **WHEN** 用户在浏览器中完成授权
- **THEN** 系统按照 interval 指定的时间间隔轮询 token 端点
- **AND** 轮询请求包含 device_code、client_id、grant_type 和 code_verifier
- **AND** 当用户完成授权后，系统收到 access_token、refresh_token 和 expires_in

#### Scenario: 用户未完成授权
- **WHEN** 用户尚未完成授权
- **THEN** 系统收到 "authorization_pending" 错误
- **AND** 系统继续轮询，不超过 expires_in 时间

#### Scenario: 轮询过于频繁
- **WHEN** 应用程序轮询频率过高
- **THEN** 系统收到 "slow_down" 错误
- **AND** 系统增加轮询间隔（乘以 1.5 倍，最大 10 秒）

#### Scenario: 授权超时
- **WHEN** 用户在 expires_in 时间内未完成授权
- **THEN** 系统停止轮询
- **AND** 系统抛出 `QwenOAuthTimeoutError` 异常

### Requirement: 访问令牌响应解析

系统必须解析 Qwen OAuth 返回的令牌响应，提取访问令牌、刷新令牌和过期时间。系统应将 expires_in（秒）转换为绝对时间戳（毫秒），便于后续判断 token 是否过期。如果响应包含 resource_url，系统也应保存该信息。

#### Scenario: 成功获取访问令牌
- **WHEN** 用户完成授权
- **THEN** 系统解析响应获取 access_token、refresh_token、expires_in 和 resource_url
- **AND** 系统计算 token 的过期时间戳（当前时间 + expires_in）
- **AND** 系统返回 `QwenOAuthToken` 对象

#### Scenario: 令牌响应不完整
- **WHEN** OAuth 响应缺少 access_token、refresh_token 或 expires_in
- **THEN** 系统抛出 `QwenOAuthError` 异常
- **AND** 异常信息说明响应不完整

### Requirement: Refresh Token 刷新

系统必须支持使用 refresh_token 获取新的 access_token，无需用户重新授权。Refresh token 端点使用相同的 token 端点，但 grant_type 参数不同。系统应处理 refresh_token 过期的情况，提示用户重新认证。

#### Scenario: 成功刷新 access_token
- **WHEN** 系统使用有效的 refresh_token 调用刷新端点
- **THEN** 系统向 `/api/v1/oauth2/token` 发送 POST 请求
- **AND** 请求包含 grant_type="refresh_token"、refresh_token 和 client_id
- **AND** 系统收到新的 access_token 和 expires_in
- **AND** 如果响应包含新的 refresh_token，系统使用新的；否则复用旧的
- **AND** 系统返回更新后的 `QwenOAuthToken` 对象

#### Scenario: Refresh token 过期或无效
- **WHEN** refresh_token 过期或无效
- **THEN** 系统收到 400 错误
- **AND** 系统抛出 `QwenRefreshTokenInvalidError` 异常
- **AND** 异常信息提示用户重新进行设备码认证

#### Scenario: Refresh token 请求失败
- **WHEN** refresh_token 请求失败（网络错误、服务器错误等）
- **THEN** 系统抛出 `QwenOAuthError` 异常
- **AND** 异常信息包含原始错误详情

### Requirement: OAuth 客户端配置

系统必须支持配置 Qwen OAuth 客户端参数。默认配置应适用于大多数场景，但系统也应允许通过构造函数参数自定义 client_id 和 scope。OAuth 服务器的 URL 和 API base URL 固定为官方地址，不支持自定义。

#### Scenario: 使用默认配置
- **WHEN** 应用程序未指定 OAuth 配置
- **THEN** 系统使用固定的 OAuth 基础 URL（https://chat.qwen.ai）
- **AND** 系统使用固定的 API base URL（https://portal.qwen.ai/v1）
- **AND** 系统使用默认的 client_id（f0304373b74a44d2b584a3fb70ca9e56）
- **AND** 系统使用默认的 scope（openid profile email model.completion）

#### Scenario: 自定义 OAuth 配置
- **WHEN** 应用程序通过构造函数指定了自定义的 client_id
- **THEN** 系统使用自定义的 client_id
- **AND** OAuth 和 API URL 保持固定
