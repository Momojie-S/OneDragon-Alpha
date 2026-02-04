# Token 持久化存储规范

## ADDED Requirements

### Requirement: Token 文件存储

系统必须将 OAuth token 持久化存储到本地文件系统，避免重复认证。Token 文件应包含访问令牌、刷新令牌和过期时间等信息。为保护用户隐私和安全，文件权限应设置为仅所有者可读写。

#### Scenario: Token 首次保存
- **WHEN** 用户完成 OAuth 认证，获取到 access_token
- **THEN** 系统将 token 数据保存到用户主目录的 `.qwen/token.json` 文件
- **AND** 文件包含 access_token、refresh_token、expires_at 和 resource_url 字段
- **AND** 文件使用 JSON 格式，UTF-8 编码

#### Scenario: Token 文件权限
- **WHEN** 系统创建 token 文件
- **THEN** 文件权限设置为 0600（仅所有者可读写）
- **AND** 确保其他用户无法读取 token

#### Scenario: 自定义 token 存储路径
- **WHEN** 应用程序指定了自定义的 token 存储路径
- **THEN** 系统将 token 保存到指定路径
- **AND** 系统在保存前确保目录存在

### Requirement: Token 文件读取

系统必须在启动时从文件读取已保存的 token。如果 token 已过期，系统应尝试使用 refresh_token 进行刷新。如果文件不存在或损坏，系统应返回 token 不可用状态，触发重新认证。

#### Scenario: Token 文件存在且有效
- **WHEN** 应用程序启动时 token 文件存在
- **AND** 文件中的 token 未过期
- **THEN** 系统从文件读取 token 数据
- **AND** 系统使用读取的 token，无需重新认证

#### Scenario: Token 文件存在但已过期
- **WHEN** 应用程序启动时 token 文件存在
- **AND** 文件中的 token 已过期
- **THEN** 系统从文件读取 token 数据
- **AND** 系统尝试使用 refresh_token 刷新
- **AND** 如果刷新成功，系统更新 token 文件

#### Scenario: Token 文件不存在
- **WHEN** 应用程序启动时 token 文件不存在
- **THEN** 系统返回 token 不可用状态
- **AND** 应用程序应触发 OAuth 认证流程

#### Scenario: Token 文件损坏
- **WHEN** token 文件存在但格式错误或损坏
- **THEN** 系统抛出 `QwenTokenCorruptedError` 异常
- **AND** 异常信息提示用户删除 token 文件并重新认证

### Requirement: Token 文件更新

系统必须在 token 刷新后更新存储文件。更新操作应保持文件权限不变，并确保数据完整性。如果刷新失败，系统应保留原 token 文件，避免丢失认证信息。

#### Scenario: Token 刷新成功后更新文件
- **WHEN** 系统使用 refresh_token 成功刷新了 access_token
- **THEN** 系统用新的 token 数据覆盖原 token 文件
- **AND** 文件权限保持为 0600

#### Scenario: Token 刷新失败时保持原文件
- **WHEN** token 刷新失败
- **THEN** 系统保持原 token 文件不变
- **AND** 系统抛出 `QwenTokenRefreshError` 异常

### Requirement: Token 文件删除

系统必须支持删除 token 文件，用于登出或重置认证状态。删除操作应同时清除内存中的 token 缓存，确保后续操作不会继续使用已删除的 token。

#### Scenario: 主动删除 token
- **WHEN** 应用程序调用 `delete_token()` 方法
- **THEN** 系统删除 token 文件
- **AND** 系统清除内存中的 token 缓存
- **AND** 后续模型调用将触发重新认证

#### Scenario: Token 文件删除失败
- **WHEN** token 文件删除操作失败（如权限不足）
- **THEN** 系统抛出 `QwenTokenFileError` 异常
- **AND** 异常信息包含失败原因

### Requirement: Token 数据结构

系统必须使用统一的数据结构存储 token 信息。数据结构应包含所有必要的认证信息，并支持向后兼容性。系统应在序列化时验证数据完整性，反序列化时处理缺失字段。

#### Scenario: Token 数据字段
- **WHEN** 系统序列化 token 数据
- **THEN** 数据包含以下字段：
  - `access_token`: 访问令牌（字符串）
  - `refresh_token`: 刷新令牌（字符串）
  - `expires_at`: 过期时间戳（整数，Unix 时间戳，毫秒）
  - `resource_url`: 资源 URL（可选，字符串）
  - `client_id`: OAuth 客户端 ID（字符串）

#### Scenario: 向后兼容
- **WHEN** 系统读取旧版本的 token 文件（缺少某些字段）
- **THEN** 系统使用默认值填充缺失字段
- **AND** 系统在下次刷新时更新为新格式

### Requirement: Token 安全性

系统必须确保 token 存储和传输的安全性。除了文件权限控制，系统还应避免在日志中暴露完整的 token。对于可选的高级场景，系统应支持 token 加密存储。

#### Scenario: Token 文件加密存储（可选）
- **WHEN** 系统配置了加密密钥
- **THEN** 系统在保存前加密 token 数据
- **AND** 系统在读取后解密 token 数据

#### Scenario: 内存中的 token 保护
- **WHEN** token 加载到内存
- **THEN** 系统应避免在日志中输出完整的 token
- **AND** 系统在异常信息中脱敏 token（仅显示前 8 位和后 4 位）
