## Why

当前系统缺乏统一的数据库连接管理机制。各个 Agent 和组件如果需要访问 MySQL 数据库，都需要独立创建和管理连接，导致代码重复、资源浪费和潜在的连接泄漏问题。需要建立一个集中式的 MySQL 连接服务，在 Agent 上下文初始化时创建连接池，供所有需要数据库访问的 ORM 查询类复用。

## What Changes

- **新增 MySQL 连接服务类** (`MySQLConnectionService`): 提供统一的数据库连接管理和连接池功能，基于 SQLAlchemy 异步引擎
- **独立的连接管理**: 作为独立的服务模块，不依赖 Agent 上下文，可按需初始化
- **连接池管理**: 使用 SQLAlchemy 的连接池功能，支持连接池配置（最小连接数、最大连接数、超时设置等）
- **连接获取接口**: 提供 `get_session()` 和 `get_engine()` 方法，供后续 ORM 查询类使用
- **配置管理**: 支持从环境变量或配置文件读取数据库连接参数
- **生命周期管理**: 提供 `close()` 方法用于显式关闭连接，支持异步上下文管理器

## Capabilities

### New Capabilities
- `mysql-connection-service`: 提供统一的 MySQL 数据库连接管理服务，包括连接池创建、连接获取、连接释放和生命周期管理功能

### Modified Capabilities
（无现有能力的需求变更）

## Impact

**受影响的代码模块**:
- `src/one_dragon_alpha/services/mysql/`: 新增 MySQL 连接服务模块

**新增依赖**:
- `aiomysql>=0.3.2`: 异步 MySQL 驱动，提供完整的异步 I/O 支持
- 使用现有的 `sqlalchemy>=2.0.46`

**API 变更**:
- 新增 `MySQLConnectionService` 类，提供：
  - `get_session()`: 获取数据库会话
  - `get_engine()`: 获取底层引擎
  - `close()`: 关闭所有连接
  - `__aenter__()` / `__aexit__()`: 支持异步上下文管理器

**配置变更**:
- 需要在 `.env` 或配置文件中添加 MySQL 连接配置项（host, port, user, password, database 等）
