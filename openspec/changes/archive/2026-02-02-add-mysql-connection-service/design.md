## Context

当前系统使用 SQLAlchemy 2.0 和 PyMySQL 作为数据库访问层，但缺乏统一的连接管理机制。各组件如需访问 MySQL 数据库，需要独立创建和管理连接，这导致：

- 代码重复：每个组件都需要编写相似的连接创建逻辑
- 资源浪费：无法复用连接池，每次查询可能创建新连接
- 维护困难：连接参数散落在各处，难以统一管理
- 潜在泄漏：缺乏统一的资源清理机制

项目已有 `SessionService` 类管理会话，提供了服务模式参考。现有的技术栈包括：
- Python 3.11+
- SQLAlchemy 2.0.46（支持异步操作）
- PyMySQL 1.1.2（MySQL 驱动）
- AgentScope（Agent 框架）

## Goals / Non-Goals

**Goals:**

- 创建统一的 `MySQLConnectionService` 类，管理 MySQL 连接池
- 支持异步操作，使用 SQLAlchemy 异步引擎
- 提供灵活的配置方式（环境变量或直接配置）
- 实现资源自动管理（异步上下文管理器）
- 确保线程安全和并发访问
- 提供健康检查功能

**Non-Goals:**

- 不在 Agent 上下文中集成（保持服务独立性）
- 不引入新的依赖（使用现有的 SQLAlchemy 和 PyMySQL）
- 不实现复杂的多数据源管理（仅支持单 MySQL 实例）
- 不提供 ORM 模型定义（仅提供连接管理）
- 不实现连接池监控 metrics（仅在健康检查中提供基础统计）

## Decisions

### 1. 使用 SQLAlchemy 异步引擎 + aiomysql 驱动

**决策**: 采用 SQLAlchemy 2.0 的 `AsyncEngine` 和 `AsyncSession`，使用 `aiomysql` 作为异步驱动

**理由**:
- 项目已依赖 SQLAlchemy 2.0.46，具备完整的异步支持
- 提供高级 ORM 功能，便于后续开发
- 内置连接池管理（QueuePool），无需自行实现
- 支持声明式模型，与现有代码风格一致
- **aiomysql 提供完整的异步 I/O 支持**，是 asyncio 生态中推荐的 MySQL 异步驱动
- aiomysql 基于 PyMySQL 开发，保持兼容性的同时提供原生 async/await 接口
- URL 格式：`mysql+aiomysql://user:pass@host:port/db`

**替代方案**:
- **pymysql (同步)**: 不支持异步操作，阻塞事件循环
- **asyncmy**: 性能更好但生态系统不如 aiomysql 成熟

### 2. 独立服务类而非单例模式

**决策**: `MySQLConnectionService` 作为普通类，由使用者实例化和管理

**理由**:
- 保持灵活性，支持多数据库实例（如读写分离）
- 避免全局状态，便于测试和模拟
- 符合项目现有的服务模式（如 `SessionService`）
- 生命周期由使用者控制，更加透明

**替代方案**:
- **单例模式**: 全局唯一实例，但限制灵活性，不利于测试

### 3. 配置优先级：构造参数 > 环境变量 > 默认值

**决策**: 支持多种配置方式，按优先级选择

**理由**:
- 构造参数提供最大灵活性
- 环境变量作为默认配置源，符合 12-Factor App 原则
- 默认值确保开发环境的易用性

**配置项**:
```python
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=password
MYSQL_DATABASE=onedragon
MYSQL_POOL_SIZE=5
MYSQL_MAX_OVERFLOW=10
MYSQL_POOL_RECYCLE=3600
```

### 4. 连接池策略：QueuePool with 回收机制

**决策**: 使用 SQLAlchemy 默认的 `QueuePool`，配置连接回收

**理由**:
- `QueuePool` 是 SQLAlchemy 的默认连接池，稳定性高
- 连接回收（`pool_recycle`）防止 MySQL 8 小时超时断开
- 支持并发访问（`pool_size` + `max_overflow`）

**默认配置**:
- `pool_size=5`: 常驻连接数
- `max_overflow=10`: 额外连接数上限
- `pool_recycle=3600`: 1 小时回收连接
- `pool_pre_ping=True`: 连接前验证可用性

### 5. 异步上下文管理器支持

**决策**: 实现 `__aenter__` 和 `__aexit__` 方法

**理由**:
- Python 异步编程的标准模式
- 自动资源清理，防止连接泄漏
- 代码更简洁（`async with` 语法）

**示例**:
```python
async with MySQLConnectionService(config) as db:
    session = db.get_session()
    # 使用 session
# 自动调用 close()
```

### 6. 健康检查基于简单连接测试

**决策**: 使用 `text("SELECT 1")` 执行简单查询

**理由**:
- 轻量级，不消耗资源
- 快速验证连接可用性
- 可选地返回连接池统计信息（`pool.status()`）

**替代方案**:
- **完整查询验证**: 成本高，可能影响性能

## 架构设计

### 类设计

```python
class MySQLConnectionService:
    """MySQL 连接服务管理类。

    该类封装了 SQLAlchemy 异步引擎和会话管理，
    提供统一的数据库连接接口。

    Attributes:
        _engine: SQLAlchemy 异步引擎实例
        _config: 数据库连接配置
        _is_closed: 服务是否已关闭
    """

    def __init__(self, config: MySQLConfig | None = None):
        """初始化 MySQL 连接服务。

        Args:
            config: 数据库配置，如果为 None 则从环境变量读取。

        Raises:
            ValueError: 配置无效时
            SQLAlchemyError: 连接失败时
        """

    async def get_session(self) -> AsyncSession:
        """获取数据库会话。

        Returns:
            AsyncSession: SQLAlchemy 异步会话对象。

        Raises:
            RuntimeError: 服务已关闭时
        """

    def get_engine(self) -> AsyncEngine:
        """获取底层引擎。

        Returns:
            AsyncEngine: SQLAlchemy 异步引擎对象。
        """

    async def close(self) -> None:
        """关闭所有连接并释放资源。

        该方法是幂等的，多次调用不会产生错误。
        """

    async def health_check(self) -> HealthStatus:
        """检查数据库连接健康状态。

        Returns:
            HealthStatus: 健康状态对象。
        """

    async def __aenter__(self) -> Self:
        """异步上下文管理器入口。"""

    async def __aexit__(self, *args) -> None:
        """异步上下文管理器出口。"""
```

### 配置类设计

```python
@dataclass
class MySQLConfig:
    """MySQL 数据库配置。

    Attributes:
        host: 数据库主机地址
        port: 数据库端口
        user: 用户名
        password: 密码
        database: 数据库名称
        pool_size: 连接池大小
        max_overflow: 最大溢出连接数
        pool_recycle: 连接回收时间（秒）
        echo: 是否打印 SQL 语句
    """

    @classmethod
    def from_env(cls) -> Self:
        """从环境变量创建配置对象。"""
```

### 目录结构

```text
src/one_dragon_alpha/services/
├── __init__.py
├── mysql/
│   ├── __init__.py
│   ├── connection_service.py  # MySQLConnectionService 类
│   ├── config.py              # MySQLConfig 类
│   └── health.py              # HealthStatus 类
```

## Risks / Trade-offs

### Risk 1: 连接池耗尽

**描述**: 高并发场景下，所有连接可能被占用，导致请求等待或超时。

**缓解措施**:
- 设置合理的 `pool_size` 和 `max_overflow` 参数
- 监控连接池使用情况（通过健康检查接口）
- 确保会话正确关闭（使用 `async with session`）
- 添加连接超时配置（`pool_timeout`）

### Risk 2: MySQL 连接超时断开

**描述**: MySQL 默认 8 小时断开空闲连接，可能导致"已丢失连接"错误。

**缓解措施**:
- 启用 `pool_recycle` 配置（默认 3600 秒）
- 启用 `pool_pre_ping` 自动检测并重建失效连接
- 健康检查定期验证连接可用性

### Risk 3: 配置错误导致的启动失败

**描述**: 数据库配置错误可能影响应用启动。

**缓解措施**:
- 初始化时立即测试连接（快速失败）
- 提供详细的错误信息（host、port、认证失败原因）
- 支持延迟初始化（lazy initialization）选项

### Trade-off 1: 灵活性 vs 复杂性

**选择**: 支持多配置方式，但增加了一些复杂度。

**权衡**:
- **优点**: 适应不同部署环境（开发、测试、生产）
- **缺点**: 配置优先级逻辑需要清晰文档说明

### Trade-off 2: 同步 API vs 异步 API

**选择**: 完全采用异步 API。

**权衡**:
- **优点**: 符合项目异步风格，性能更好
- **缺点**: 不支持同步代码直接使用（需使用 `asyncio.run`）

## Migration Plan

### 阶段 1: 实现核心功能

- [ ] 实现 `MySQLConfig` 类和 `from_env()` 方法
- [ ] 实现 `MySQLConnectionService` 基础功能
- [ ] 编写单元测试

### 阶段 2: 集成和使用

- [ ] 创建示例代码展示如何使用服务
- [ ] 更新项目文档

### 阶段 3: 优化和完善

- [ ] 添加健康检查功能
- [ ] 完善错误处理和日志
- [ ] 性能测试和优化

**回滚策略**:
由于是新功能且不影响现有代码，无需特殊回滚策略。如有问题，直接删除相关代码即可。

## Open Questions

1. **是否需要支持读写分离？**
   - 当前设计不支持，如需支持可扩展为多引擎管理

2. **是否需要支持事务装饰器？**
   - 当前仅提供会话管理，高级事务管理由使用者实现

3. **连接池参数是否需要运行时动态调整？**
   - 当前设计不支持，需要在初始化时指定

4. **是否需要提供连接池监控接口？**
   - 当前健康检查提供基础统计，详细监控可后续扩展
