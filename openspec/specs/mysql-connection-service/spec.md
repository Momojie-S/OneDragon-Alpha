## ADDED Requirements

### Requirement: 连接服务初始化

系统必须提供一个 `MySQLConnectionService` 类，能够通过配置参数初始化 MySQL 数据库连接池。该类应支持异步操作，使用 SQLAlchemy 异步引擎和 pymysql 驱动。

#### Scenario: 成功初始化连接服务

- **WHEN** 提供有效的 MySQL 连接配置（host、port、user、password、database）
- **THEN** 系统创建 `MySQLConnectionService` 实例
- **AND** 底层 SQLAlchemy 异步引擎成功建立连接池
- **AND** 连接池使用默认或指定的连接池配置

#### Scenario: 使用环境变量配置

- **WHEN** 环境变量中定义了 MySQL 连接参数
- **THEN** `MySQLConnectionService` 自动从环境变量读取配置
- **AND** 支持配置项包括：MYSQL_HOST、MYSQL_PORT、MYSQL_USER、MYSQL_PASSWORD、MYSQL_DATABASE

#### Scenario: 配置无效时抛出异常

- **WHEN** 提供的连接配置无效（如错误的 host、port 或认证信息）
- **THEN** 初始化过程中抛出异常
- **AND** 异常信息包含详细的错误原因

### Requirement: 获取数据库会话

系统必须提供 `get_session()` 方法，用于获取 SQLAlchemy 异步会话对象。该方法返回的会话可用于执行数据库查询和事务操作。

#### Scenario: 成功获取会话

- **WHEN** 调用 `get_session()` 方法
- **THEN** 返回一个有效的 `AsyncSession` 对象
- **AND** 该会话可用于执行 ORM 查询操作

#### Scenario: 多次调用获取独立会话

- **WHEN** 多次调用 `get_session()` 方法
- **THEN** 每次调用返回新的会话对象
- **AND** 不同会话之间的操作互不影响

#### Scenario: 服务未初始化时获取会话

- **WHEN** 在服务未正确初始化的情况下调用 `get_session()`
- **THEN** 抛出适当的异常
- **AND** 异常信息表明服务未初始化

### Requirement: 获取底层引擎

系统必须提供 `get_engine()` 方法，用于获取底层的 SQLAlchemy 异步引擎对象。该方法允许高级用户直接访问引擎以执行特殊操作。

#### Scenario: 成功获取引擎

- **WHEN** 调用 `get_engine()` 方法
- **THEN** 返回底层 `AsyncEngine` 对象
- **AND** 该引擎对象可用于直接执行 SQL 语句或管理连接

#### Scenario: 引擎对象复用

- **WHEN** 多次调用 `get_engine()` 方法
- **THEN** 返回同一个引擎实例
- **AND** 引擎的连接池状态在多次调用间保持一致

### Requirement: 连接池配置

系统必须支持自定义连接池配置，包括最小连接数、最大连接数、连接回收时间等参数。连接池配置应在初始化时指定。

#### Scenario: 使用自定义连接池配置

- **WHEN** 初始化时提供自定义连接池参数（pool_size、max_overflow、pool_recycle 等）
- **THEN** 连接池按照指定参数创建
- **AND** 连接池行为符合配置要求

#### Scenario: 使用默认连接池配置

- **WHEN** 初始化时未提供连接池参数
- **THEN** 使用 SQLAlchemy 默认连接池配置
- **AND** 默认配置适用于一般应用场景

### Requirement: 生命周期管理

系统必须提供 `close()` 方法，用于显式关闭所有数据库连接并释放资源。该类还应支持异步上下文管理器协议，确保资源自动清理。

#### Scenario: 显式关闭连接

- **WHEN** 调用 `close()` 方法
- **THEN** 所有数据库连接被关闭
- **AND** 连接池资源被释放
- **AND** 后续调用 `get_session()` 将抛出异常

#### Scenario: 使用异步上下文管理器

- **WHEN** 使用 `async with` 语句管理 `MySQLConnectionService` 实例
- **THEN** 进入上下文时服务正常工作
- **AND** 退出上下文时自动调用 `close()` 方法
- **AND** 所有资源被正确释放

#### Scenario: 重复关闭不报错

- **WHEN** 多次调用 `close()` 方法
- **THEN** 第一次调用关闭所有连接
- **AND** 后续调用不产生错误（幂等操作）

### Requirement: 连接健康检查

系统应提供连接健康检查功能，用于验证数据库连接是否正常工作。

#### Scenario: 成功的健康检查

- **WHEN** 数据库连接正常时调用健康检查方法
- **THEN** 返回成功状态
- **AND** 可选地返回连接池统计信息

#### Scenario: 数据库不可达时的健康检查

- **WHEN** 数据库服务不可用或网络中断时调用健康检查方法
- **THEN** 返回失败状态
- **AND** 包含错误详情

### Requirement: 线程安全

`MySQLConnectionService` 必须是线程安全的，能够在多线程或异步环境中安全使用。

#### Scenario: 并发获取会话

- **WHEN** 多个协程同时调用 `get_session()` 方法
- **THEN** 每个协程都获得有效的会话对象
- **AND** 不会产生竞态条件或数据竞争

#### Scenario: 并发关闭服务

- **WHEN** 多个协程同时调用 `close()` 方法
- **THEN** 只执行一次实际的关闭操作
- **AND** 不会抛出异常或导致程序崩溃
