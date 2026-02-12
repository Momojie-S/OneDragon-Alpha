
## ADDED Requirements

### Requirement: 数据库表设计
系统 SHALL 创建数据库表用于存储 OpenAI 模型配置。

#### Scenario: 表结构包含所有必需字段
- **WHEN** 系统创建 model_configs 表
- **THEN** 表 SHALL 包含以下字段：
  - `id`: 主键（BIGINT，自增）
  - `name`: 配置名称（VARCHAR(255)，唯一，非空）
  - `provider`: 模型提供商（VARCHAR(50)，非空）
  - `base_url`: API baseUrl（TEXT，非空）
  - `api_key`: API密钥（TEXT，非空，明文存储）
  - `models`: 模型列表（JSON，存储模型对象数组）
    - 每个模型对象包含：model_id、support_vision、support_thinking
  - `is_active`: 是否启用（BOOLEAN，默认 true）
  - `created_at`: 创建时间（DATETIME）
  - `updated_at`: 更新时间（DATETIME）

#### Scenario: 创建索引
- **WHEN** 系统创建数据库表
- **THEN** 系统 SHALL 在 name 字段上创建唯一索引
- **AND** 系统 SHALL 在 provider 字段上创建索引
- **AND** 系统 SHALL 在 is_active 字段上创建索引以优化查询

### Requirement: 模型配置持久化
系统 SHALL 支持将模型配置保存到数据库。

#### Scenario: 保存新配置
- **WHEN** 用户创建新的模型配置
- **THEN** 系统 SHALL 将配置数据插入到 model_configs 表
- **AND** api_key SHALL 以明文形式存储到 api_key 字段
- **AND** created_at 和 updated_at SHALL 自动设置为当前时间

#### Scenario: 更新现有配置
- **WHEN** 用户更新现有模型配置
- **THEN** 系统 SHALL 更新 model_configs 表中的对应记录
- **AND** updated_at SHALL 自动更新为当前时间
- **AND** created_at SHALL 保持不变

#### Scenario: 物理删除配置
- **WHEN** 用户删除模型配置
- **THEN** 系统 SHALL 从数据库中移除该记录
- **AND** 该操作 SHALL 不可恢复（物理删除）

### Requirement: 模型配置查询
系统 SHALL 支持多种方式查询模型配置。

#### Scenario: 查询所有配置
- **WHEN** 用户请求获取所有模型配置
- **THEN** 系统 SHALL 从数据库中读取所有记录
- **AND** api_key SHALL 不在响应中返回
- **AND** 结果 SHALL 按 created_at 倒序排列

#### Scenario: 根据 ID 查询配置
- **WHEN** 用户请求获取特定 ID 的模型配置
- **THEN** 系统 SHALL 从数据库中查询该 ID 的记录
- **AND** 如果记录存在，返回配置信息（api_key 不在响应中返回）
- **AND** 如果记录不存在，返回 404 错误

#### Scenario: 查询启用的配置
- **WHEN** 用户请求获取所有启用的模型配置
- **THEN** 系统 SHALL 仅返回 is_active = true 的记录
- **AND** 结果 SHALL 按 created_at 倒序排列

#### Scenario: 根据名称查询配置
- **WHEN** 用户请求获取特定名称的模型配置
- **THEN** 系统 SHALL 从数据库中查询该名称的记录
- **AND** 如果记录存在，返回配置信息
- **AND** 如果记录不存在，返回 404 错误

### Requirement: 数据库连接管理
系统 SHALL 使用现有的 MySQL 连接服务进行数据库操作。

#### Scenario: 使用现有连接池
- **WHEN** 系统执行数据库操作
- **THEN** 系统 SHALL 使用已有的 MySQL 连接服务
- **AND** 不需要创建新的数据库连接

#### Scenario: 连接失败处理
- **WHEN** 数据库连接失败
- **THEN** 系统 SHALL 返回明确的错误信息
- **AND** 错误信息 SHALL 包含数据库连接问题的提示

### Requirement: 事务处理
系统 SHALL 在需要时使用数据库事务确保数据一致性。

#### Scenario: 创建配置的事务处理
- **WHEN** 创建模型配置过程中发生错误
- **THEN** 系统 SHALL 回滚所有已执行的数据库操作
- **AND** 数据库 SHALL 保持操作前的状态

#### Scenario: 更新配置的事务处理
- **WHEN** 更新模型配置过程中发生错误
- **THEN** 系统 SHALL 回滚所有已执行的数据库操作
- **AND** 原有配置数据 SHALL 保持不变

### Requirement: 数据安全
系统 SHALL 保护敏感信息的安全。

**注意**: 当前版本中，API key 以明文形式存储在数据库中。安全措施包括:
- 数据库访问控制
- 网络隔离
- API 响应中不返回 api_key 字段
- 仅在内部调用时使用 api_key

#### Scenario: API key 存储
- **WHEN** 存储 API key 到数据库
- **THEN** 系统 SHALL 以明文形式存储在 api_key 字段中
- **AND** 数据库 SHALL 通过访问控制限制访问

#### Scenario: API key 使用
- **WHEN** 从数据库读取 API key 用于实际调用
- **THEN** 系统 SHALL 读取 api_key 字段的数据
- **AND** 明文 SHALL 仅用于内部调用，不返回给前端
