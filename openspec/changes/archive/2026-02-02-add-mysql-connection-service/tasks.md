# Implementation Tasks

## 1. 基础配置和数据结构

- [x] 1.1 创建 `src/one_dragon_alpha/services/` 目录结构
- [x] 1.2 实现 `MySQLConfig` 数据类（包含所有配置字段）
- [x] 1.3 实现 `MySQLConfig.from_env()` 类方法从环境变量加载配置
- [x] 1.4 实现 `HealthStatus` 数据类用于健康检查结果
- [x] 1.5 添加 UTF-8 编码声明到所有 Python 文件

## 2. 核心 MySQLConnectionService 实现

- [x] 2.1 实现 `MySQLConnectionService.__init__()` 方法
  - 支持传入配置对象或从环境变量加载
  - 创建 SQLAlchemy 异步引擎和连接池
  - 初始化时验证连接可用性
- [x] 2.2 实现 `get_session()` 方法返回 AsyncSession
- [x] 2.3 实现 `get_engine()` 方法返回底层引擎
- [x] 2.4 实现 `close()` 方法关闭所有连接（幂等操作）
- [x] 2.5 实现 `__aenter__()` 和 `__aexit__()` 支持异步上下文管理器
- [x] 2.6 实现 `health_check()` 方法验证连接健康状态

## 3. 错误处理和验证

- [x] 3.1 添加配置验证逻辑（检查必需字段）
- [x] 3.2 实现服务关闭状态检查（get_session 在关闭后抛出 RuntimeError）
- [x] 3.3 添加详细的错误信息和日志记录
- [x] 3.4 确保线程安全（使用 asyncio.Lock 保护关闭操作）

## 4. 文档和类型提示

- [x] 4.1 为所有类和方法添加 Google 风格的 docstring
- [x] 4.2 为所有函数签名添加完整的类型提示
- [x] 4.3 使用内置泛型类型（list、dict）而非 typing 模块
- [x] 4.4 正确使用 TYPE_CHECKING 导入类型注解

## 5. 单元测试

- [x] 5.1 创建测试目录结构 `tests/one_dragon_alpha/services/mysql/`
- [x] 5.2 编写 `MySQLConfig` 类的单元测试
- [x] 5.3 编写 `MySQLConnectionService` 初始化测试
  - 测试成功初始化场景
  - 测试使用环境变量配置
  - 测试配置无效时抛出异常
- [x] 5.4 编写 `get_session()` 方法测试
  - 测试成功获取会话
  - 测试多次调用获取独立会话
  - 测试服务关闭后获取会话抛出异常
- [x] 5.5 编写 `get_engine()` 方法测试
  - 测试成功获取引擎
  - 测试引擎对象复用
- [x] 5.6 编写生命周期管理测试
  - 测试显式关闭连接
  - 测试异步上下文管理器
  - 测试重复关闭的幂等性
- [x] 5.7 编写健康检查测试
  - 测试成功场景
  - 测试数据库不可达场景
- [x] 5.8 编写线程安全测试
  - 测试并发获取会话
  - 测试并发关闭服务

## 6. 集成和示例

- [x] 6.1 创建使用示例代码（展示如何初始化和使用服务）
- [x] 6.2 更新项目文档，说明 MySQL 连接服务的使用方法
- [x] 6.3 在 `__init__.py` 中导出公共接口（MySQLConnectionService、MySQLConfig）

## 7. 代码质量检查

- [x] 7.1 运行 `ruff check` 进行代码检查
- [x] 7.2 运行 `ruff format` 进行代码格式化
- [x] 7.3 确保所有测试通过（`pytest tests/`）
- [x] 7.4 验证所有代码符合项目编码规范
