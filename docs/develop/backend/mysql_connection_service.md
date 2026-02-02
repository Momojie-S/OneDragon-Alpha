# MySQL 连接服务

## 概述

`MySQLConnectionService` 是一个统一的 MySQL 数据库连接管理服务，提供连接池管理、会话获取和生命周期管理功能。

## 功能特性

- **连接池管理**: 使用 SQLAlchemy 异步引擎，支持连接池配置
- **异步支持**: 完全基于 asyncio，支持高性能异步操作
- **灵活配置**: 支持环境变量和代码配置两种方式
- **自动清理**: 支持异步上下文管理器，自动释放资源
- **健康检查**: 提供连接健康状态检查功能
- **线程安全**: 支持并发访问

## 快速开始

### 1. 环境变量配置

在 `.env` 文件中设置数据库连接信息：

```bash
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=your_database
MYSQL_POOL_SIZE=5
MYSQL_MAX_OVERFLOW=10
MYSQL_POOL_RECYCLE=3600
MYSQL_ECHO=false
```

### 2. 基本使用

```python
from one_dragon_alpha.services.mysql.connection_service import MySQLConnectionService

# 自动从环境变量加载配置
service = MySQLConnectionService()

try:
    # 获取数据库会话
    session = await service.get_session()

    # 执行数据库操作
    result = await session.execute(select(User).where(User.id == 1))
    user = result.scalar_one()

finally:
    # 关闭服务
    await service.close()
```

### 3. 使用上下文管理器（推荐）

```python
async with MySQLConnectionService() as service:
    session = await service.get_session()
    # 执行数据库操作
# 自动关闭服务
```

### 4. 使用自定义配置

```python
from one_dragon_alpha.services.mysql.config import MySQLConfig

config = MySQLConfig(
    host="localhost",
    port=3306,
    user="myuser",
    password="mypassword",
    database="mydb",
    pool_size=10,
)

async with MySQLConnectionService(config) as service:
    session = await service.get_session()
    # 执行数据库操作
```

## API 参考

### MySQLConfig

数据库配置类。

#### 参数

- `host` (str): 数据库主机地址
- `port` (int): 数据库端口，默认 3306
- `user` (str): 数据库用户名
- `password` (str): 数据库密码
- `database` (str): 数据库名称
- `pool_size` (int): 连接池大小，默认 5
- `max_overflow` (int): 最大溢出连接数，默认 10
- `pool_recycle` (int): 连接回收时间（秒），默认 3600
- `echo` (bool): 是否打印 SQL 语句，默认 False

#### 方法

##### from_env()

从环境变量创建配置对象。

```python
config = MySQLConfig.from_env()
```

##### validate()

验证配置参数。

```python
config.validate()
```

##### to_connection_url()

转换为 SQLAlchemy 连接 URL。

```python
url = config.to_connection_url()
```

### MySQLConnectionService

MySQL 连接服务类。

#### 方法

##### __init__(config: MySQLConfig | None = None)

初始化服务。

- `config`: 配置对象，如果为 None 则从环境变量加载

##### async get_session() -> AsyncSession

获取数据库会话。

返回: SQLAlchemy 异步会话对象

抛出: RuntimeError - 服务已关闭时

##### get_engine() -> AsyncEngine

获取底层引擎。

返回: SQLAlchemy 异步引擎对象

抛出: RuntimeError - 服务已关闭时

##### async close() -> None

关闭所有连接并释放资源。

该方法是幂等的，多次调用不会产生错误。

##### async health_check() -> HealthStatus

检查数据库连接健康状态。

返回: 健康状态对象，包含连接池统计信息

##### async __aenter__() -> Self

异步上下文管理器入口。

##### async __aexit__(*args) -> None

异步上下文管理器出口，自动调用 close()。

## 配置说明

### 连接池配置

- **pool_size**: 常驻连接数，默认 5
- **max_overflow**: 额外连接数上限，默认 10
- **pool_recycle**: 连接回收时间（秒），默认 3600（1小时）
- **pool_pre_ping**: 连接前验证可用性，默认启用

建议配置：

- **开发环境**: pool_size=5, max_overflow=10
- **生产环境**: 根据并发量调整，通常 pool_size=10-20, max_overflow=20-50

### 连接回收

MySQL 默认 8 小时断开空闲连接。为避免连接丢失错误：

- 设置 `pool_recycle=3600`（1小时）
- 启用 `pool_pre_ping=True`（默认启用）

## 健康检查

使用健康检查功能验证数据库连接：

```python
service = MySQLConnectionService()
health = await service.health_check()

if health.is_healthy:
    print(f"Pool size: {health.pool_size}")
    print(f"Checked out: {health.checked_out}")
else:
    print(f"Error: {health.error}")
```

## 最佳实践

### 1. 使用上下文管理器

确保资源正确释放：

```python
async with MySQLConnectionService() as service:
    session = await service.get_session()
    # 操作数据库
```

### 2. 配置优先级

配置优先级：构造参数 > 环境变量 > 默认值

### 3. 错误处理

```python
from sqlalchemy.exc import SQLAlchemyError

async with MySQLConnectionService() as service:
    try:
        session = await service.get_session()
        # 执行数据库操作
        await session.commit()
    except SQLAlchemyError as e:
        await session.rollback()
        logger.error(f"Database error: {e}")
```

### 4. 会话管理

```python
async with MySQLConnectionService() as service:
    async with service.get_session() as session:
        # 执行查询
        result = await session.execute(select(User))
        users = result.scalars().all()
```

## 故障排查

### 连接失败

检查：
1. MySQL 服务是否运行
2. 连接参数是否正确（host、port、user、password）
3. 数据库是否存在
4. 网络连接是否正常

### 连接池耗尽

症状：请求等待或超时

解决：
- 增加 `pool_size` 和 `max_overflow`
- 确保会话正确关闭
- 检查是否有连接泄漏

### 连接超时断开

症状：MySQL has gone away 错误

解决：
- 设置 `pool_recycle=3600` 或更小
- 确保启用了 `pool_pre_ping=True`

## 示例代码

完整示例请参考：`examples/mysql_connection_service_example.py`
