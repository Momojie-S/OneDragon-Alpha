# OpenAI 模型 API 规范

## ADDED Requirements

### Requirement: 创建模型配置 API
系统 SHALL 提供 POST /api/models/configs 接口用于创建新的模型配置。

#### Scenario: 成功创建配置
- **WHEN** 用户发送 POST 请求到 /api/models/configs
- **AND** 请求体包含有效的配置数据
- **THEN** 系统 SHALL 返回 201 Created 状态码
- **AND** 响应体包含完整的配置信息（api_key 不在响应中返回）
- **AND** 响应体包含新创建配置的 ID

#### Scenario: 创建配置失败 - 名称重复
- **WHEN** 用户发送 POST 请求到 /api/models/configs
- **AND** 请求体中的 name 已存在
- **THEN** 系统 SHALL 返回 400 Bad Request 状态码
- **AND** 响应体包含错误信息，提示配置名称已存在

#### Scenario: 创建配置失败 - 验证错误
- **WHEN** 用户发送 POST 请求到 /api/models/configs
- **AND** 请求体缺少必需字段或格式不正确
- **THEN** 系统 SHALL 返回 422 Unprocessable Entity 状态码
- **AND** 响应体包含详细的验证错误信息

### Requirement: 测试 API 连接
系统 SHALL 提供 POST /api/models/configs/test-connection 接口用于测试配置的 API 连接。

#### Scenario: 连接测试成功
- **WHEN** 用户发送 POST 请求到 /api/models/configs/test-connection
- **AND** 请求体包含有效的 base_url 和 api_key
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 响应体包含 success: true 和连接测试结果

#### Scenario: 连接测试失败
- **WHEN** 用户发送 POST 请求到 /api/models/configs/test-connection
- **AND** 无法连接到指定的 API 端点
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 响应体包含 success: false 和错误详情

### Requirement: 获取模型配置列表 API
系统 SHALL 提供 GET /api/models/configs 接口用于获取所有模型配置。

#### Scenario: 成功获取列表
- **WHEN** 用户发送 GET 请求到 /api/models/configs
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 响应体为分页对象，包含 total、page、page_size、items 字段
- **AND** items 为模型配置数组，api_key 不在响应中返回
- **AND** items SHALL 按 created_at 倒序排列

#### Scenario: 过滤启用的配置
- **WHEN** 用户发送 GET 请求到 /api/models/configs?is_active=true
- **THEN** 系统 SHALL 仅返回 is_active = true 的配置
- **AND** 响应体状态码为 200 OK

#### Scenario: 空列表
- **WHEN** 数据库中没有任何模型配置
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 响应体包含空数组

#### Scenario: 无效的分页参数
- **WHEN** 用户发送 GET 请求到 /api/models/configs?page_size=200
- **AND** page_size 超过最大值 100
- **THEN** 系统 SHALL 返回 400 Bad Request 状态码
- **AND** 响应体包含错误信息，提示 page_size 超出范围

#### Scenario: 负数分页参数
- **WHEN** 用户发送 GET 请求到 /api/models/configs?page=-1
- **THEN** 系统 SHALL 返回 400 Bad Request 状态码

#### Scenario: 无效的过滤参数
- **WHEN** 用户发送 GET 请求到 /api/models/configs?is_active=invalid
- **THEN** 系统 SHALL 返回 400 Bad Request 状态码
- **AND** 响应体包含错误信息，提示 is_active 参数无效


### Requirement: 获取单个模型配置 API
系统 SHALL 提供 GET /api/models/configs/{id} 接口用于获取特定模型配置。

#### Scenario: 成功获取配置
- **WHEN** 用户发送 GET 请求到 /api/models/configs/{id}
- **AND** 该 ID 的配置存在
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 响应体包含配置信息（api_key 不在响应中返回）

#### Scenario: 配置不存在
- **WHEN** 用户发送 GET 请求到 /api/models/configs/{id}
- **AND** 该 ID 的配置不存在
- **THEN** 系统 SHALL 返回 404 Not Found 状态码
- **AND** 响应体包含错误信息，提示配置未找到

#### Scenario: 无效的 ID 格式
- **WHEN** 用户发送 GET 请求到 /api/models/configs/{id}
- **AND** {id} 不是有效的数字
- **THEN** 系统 SHALL 返回 400 Bad Request 状态码
- **AND** 响应体包含错误信息，提示 ID 格式不正确


### Requirement: 认证和授权
系统 SHALL 对所有 API 端点进行身份认证和授权验证。

#### Scenario: 缺少认证凭据
- **WHEN** 用户发送请求但未提供有效的认证凭据
- **THEN** 系统 SHALL 返回 401 Unauthorized 状态码
- **AND** 响应体包含错误信息，提示需要认证

#### Scenario: 认证凭据无效
- **WHEN** 用户发送请求但提供的认证凭据已过期或无效
- **THEN** 系统 SHALL 返回 401 Unauthorized 状态码
- **AND** 响应体包含错误信息，提示凭据无效

#### Scenario: 权限不足
- **WHEN** 用户已认证但没有管理模型配置的权限
- **THEN** 系统 SHALL 返回 403 Forbidden 状态码
- **AND** 响应体包含错误信息，提示权限不足

### Requirement: 更新模型配置 API
系统 SHALL 提供 PUT /api/models/configs/{id} 接口用于更新模型配置。

#### Scenario: 成功更新配置
- **WHEN** 用户发送 PUT 请求到 /api/models/configs/{id}
- **AND** 该 ID 的配置存在
- **AND** 请求体包含有效地更新数据
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 响应体包含更新后的配置信息（api_key 不在响应中返回）
- **AND** updated_at 字段 SHALL 被更新为当前时间

#### Scenario: 更新时不提供 API key
- **WHEN** 用户发送 PUT 请求到 /api/models/configs/{id}
- **AND** 请求体中不包含 api_key 字段
- **THEN** 系统 SHALL 保留原有的 API key
- **AND** 其他字段 SHALL 正常更新

#### Scenario: 配置不存在
- **WHEN** 用户发送 PUT 请求到 /api/models/configs/{id}
- **AND** 该 ID 的配置不存在
- **THEN** 系统 SHALL 返回 404 Not Found 状态码

#### Scenario: 名称冲突
- **WHEN** 用户发送 PUT 请求到 /api/models/configs/{id}
- **AND** 请求体中的 name 与其他配置重复
- **THEN** 系统 SHALL 返回 400 Bad Request 状态码
- **AND** 响应体包含错误信息，提示配置名称已存在

#### Scenario: 更新冲突 - 乐观锁
- **WHEN** 用户发送 PUT 请求到 /api/models/configs/{id}
- **AND** 请求中的 updated_at 与数据库中的不一致
- **THEN** 系统 SHALL 返回 409 Conflict 状态码
- **AND** 响应体包含错误信息，提示配置已被其他用户修改

#### Scenario: 更新失败 - 验证错误
- **WHEN** 用户发送 PUT 请求到 /api/models/configs/{id}
- **AND** 请求体包含无效数据
- **THEN** 系统 SHALL 返回 422 Unprocessable Entity 状态码
- **AND** 响应体包含详细的验证错误信息


### Requirement: 删除模型配置 API
系统 SHALL 提供 DELETE /api/models/configs/{id} 接口用于删除模型配置。

#### Scenario: 成功删除配置
- **WHEN** 用户发送 DELETE 请求到 /api/models/configs/{id}
- **AND** 该 ID 的配置存在
- **THEN** 系统 SHALL 返回 204 No Content 状态码
- **AND** 数据库中的记录 SHALL 被物理删除

#### Scenario: 配置不存在
- **WHEN** 用户发送 DELETE 请求到 /api/models/configs/{id}
- **AND** 该 ID 的配置不存在
- **THEN** 系统 SHALL 返回 404 Not Found 状态码

### Requirement: 启用/禁用模型配置 API
系统 SHALL 提供 PATCH /api/models/configs/{id}/status 接口用于切换配置的启用状态。

#### Scenario: 启用配置
- **WHEN** 用户发送 PATCH 请求到 /api/models/configs/{id}/status
- **AND** 请求体为 {"is_active": true}
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 该配置的 is_active 字段 SHALL 被设置为 true

#### Scenario: 禁用配置
- **WHEN** 用户发送 PATCH 请求到 /api/models/configs/{id}/status
- **AND** 请求体为 {"is_active": false}
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 该配置的 is_active 字段 SHALL 被设置为 false

#### Scenario: 配置不存在
- **WHEN** 用户发送 PATCH 请求到 /api/models/configs/{id}/status
- **AND** 该 ID 的配置不存在
- **THEN** 系统 SHALL 返回 404 Not Found 状态码

### Requirement: API 请求验证
系统 SHALL 对所有 API 请求进行验证和授权。

#### Scenario: 请求体格式验证
- **WHEN** 用户发送的请求体不是有效的 JSON
- **THEN** 系统 SHALL 返回 400 Bad Request 状态码
- **AND** 响应体包含错误信息，提示请求体格式不正确

#### Scenario: Content-Type 验证
- **WHEN** 用户发送 POST/PUT/PATCH 请求
- **AND** Content-Type 不是 application/json
- **THEN** 系统 SHALL 返回 415 Unsupported Media Type 状态码

#### Scenario: 响应格式一致性
- **WHEN** API 返回成功响应
- **THEN** 除 204 No Content 外，Content-Type SHALL 为 application/json
- **AND** 成功响应直接返回数据对象（无额外包装层）
- **AND** 错误响应 SHALL 包含 code、message、details 字段

### Requirement: API 错误处理
系统 SHALL 提供清晰和一致的错误响应。

#### Scenario: 数据库错误处理
- **WHEN** 数据库操作失败
- **THEN** 系统 SHALL 返回 500 Internal Server Error 状态码
- **AND** 响应体包含错误信息，提示服务器内部错误
- **AND** 详细错误信息 SHALL 记录在日志中，不返回给客户端

#### Scenario: 验证错误详情
- **WHEN** 请求验证失败
- **THEN** 系统 SHALL 返回 422 Unprocessable Entity 状态码
- **AND** 响应体包含详细的字段级错误信息
- **AND** 每个字段错误 SHALL 包含字段名和错误描述

### Requirement: 分页支持
系统 SHALL 支持模型配置列表的分页查询。

**默认值和限制**:
- 默认 page = 1
- 默认 page_size = 20
- 最大 page_size = 100

#### Scenario: 使用分页参数
- **WHEN** 用户发送 GET 请求到 /api/models/configs?page=1&page_size=10
- **THEN** 系统 SHALL 返回第 1 页的 10 条记录
- **AND** 响应体包含 total、page、page_size、items 字段

#### Scenario: 超出页码范围
- **WHEN** 用户请求的页码超出实际页数
- **THEN** 系统 SHALL 返回 200 OK 状态码
- **AND** 响应体的 items 为空数组
