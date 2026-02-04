# Token 自动刷新规范

## ADDED Requirements

### Requirement: 定时刷新任务启动

系统必须在首次获取 token 后启动后台定时刷新任务。定时任务应独立运行，不依赖外部调用。系统应使用 asyncio.Task 实现异步定时逻辑。

#### Scenario: 首次获取 token 后启动定时任务
- **WHEN** 应用程序首次调用 `get_access_token()`
- **AND** 本地无有效 token
- **THEN** 系统执行设备码认证获取 token
- **AND** 系统启动后台定时刷新任务
- **AND** 定时任务在独立的 asyncio.Task 中运行

#### Scenario: 从文件加载 token 后启动定时任务
- **WHEN** 应用程序调用 `get_access_token()`
- **AND** 本地存在有效的 token 文件
- **THEN** 系统从文件加载 token
- **AND** 系统启动后台定时刷新任务
- **AND** 定时任务计算首次刷新时间

#### Scenario: 定时任务已在运行
- **WHEN** 应用程序再次调用 `get_access_token()`
- **AND** 定时任务已在运行
- **THEN** 系统不重复启动定时任务
- **AND** 系统直接返回当前 token

### Requirement: 定时刷新循环

系统必须实现定时刷新循环，在 token 过期前自动刷新。刷新时间应设置为过期时间减去缓冲区（如 5 分钟）。循环应持续运行，直到收到停止信号或刷新失败。

#### Scenario: 计算刷新时间
- **WHEN** 定时任务计算下次刷新时间
- **THEN** 系统读取 token 的 expires_at 时间戳
- **AND** 系统计算刷新时间 = expires_at - 5 分钟（300000 毫秒）
- **AND** 如果刷新时间已过，系统等待 60 秒后刷新

#### Scenario: 定时刷新执行
- **WHEN** 等待时间到达
- **THEN** 系统调用 refresh_token() 方法
- **AND** 系统更新内存中的 token 数据
- **AND** 系统保存 token 到文件
- **AND** 系统计算下次刷新时间并继续循环

#### Scenario: 刷新失败后重试
- **WHEN** token 刷新失败，且错误为临时性错误（如网络超时）
- **THEN** 系统记录警告日志
- **AND** 系统等待 60 秒后重试
- **AND** 系统继续循环

#### Scenario: Refresh token 无效
- **WHEN** token 刷新失败，且 refresh_token 无效（400 错误）
- **THEN** 系统抛出 `QwenRefreshTokenInvalidError` 异常
- **AND** 系统停止定时刷新任务
- **AND** 系统提示用户重新认证

### Requirement: 定时任务生命周期管理

系统必须提供定时任务的启动和停止方法。启动方法应在获取 token 后自动调用，停止方法应由应用程序在关闭时显式调用。系统应使用 asyncio.Event 实现优雅停止。

#### Scenario: 启动定时任务
- **WHEN** 系统调用 `_start_refresh_timer()`
- **AND** 定时任务未运行
- **THEN** 系统创建 asyncio.Task
- **AND** 系统运行 `_refresh_loop()` 协程
- **AND** 系统保存 task 引用

#### Scenario: 停止定时任务
- **WHEN** 应用程序调用 `shutdown()`
- **THEN** 系统设置 stop_event
- **AND** 系统取消定时任务（如果正在运行）
- **AND** 系统等待任务完成清理
- **AND** 后续调用 `get_access_token()` 将重新启动定时任务

#### Scenario: 优雅停止
- **WHEN** stop_event 被设置
- **AND** 定时任务正在等待刷新时间
- **THEN** 系统立即退出等待
- **AND** 系统停止刷新循环
- **AND** 系统完成资源清理

### Requirement: 并发刷新控制

系统必须避免并发刷新操作。虽然定时任务会自动刷新，但在某些异常情况下（如手动调用 refresh_token），可能需要并发控制。系统应使用 asyncio.Lock 保护刷新操作。

#### Scenario: 单例 Token Manager
- **WHEN** 多个 `QwenChatModel` 实例同时运行
- **THEN** 系统使用单例模式的 `QwenTokenManager`
- **AND** 所有实例共享同一个定时任务

#### Scenario: 并发刷新保护
- **WHEN** 定时任务正在刷新 token
- **AND** 外部调用尝试刷新 token
- **THEN** 系统使用 asyncio.Lock 保护刷新操作
- **AND** 外部调用等待定时任务完成
- **AND** 外部调用使用刷新后的 token

### Requirement: Token 刷新事件通知

系统必须在 token 刷新成功或失败时通知订阅者。通过事件机制，应用程序可以监听 token 刷新状态，实现日志记录、监控告警或自定义逻辑。

#### Scenario: 刷新成功通知
- **WHEN** 定时任务成功刷新 token
- **THEN** 系统触发 `on_token_refreshed` 回调事件
- **AND** 事件包含新的 token 信息

#### Scenario: 刷新失败通知
- **WHEN** 定时任务刷新 token 失败
- **THEN** 系统触发 `on_token_refresh_failed` 回调事件
- **AND** 事件包含错误信息

### Requirement: Token Manager 单例实现

系统必须实现单例模式的 `QwenTokenManager`，确保全局只有一个 token 管理实例。单例模式可以避免重复认证、token 冲突和资源浪费。系统应提供线程安全的实例获取方法，并支持重置单例以进行测试。

#### Scenario: 获取 Token Manager 实例
- **WHEN** 应用程序调用 `QwenTokenManager.get_instance()`
- **THEN** 系统返回全局唯一的 `QwenTokenManager` 实例
- **AND** 多次调用返回同一个实例

#### Scenario: Token Manager 初始化
- **WHEN** 首次调用 `QwenTokenManager.get_instance()`
- **THEN** 系统创建新的 `QwenTokenManager` 实例
- **AND** 系统初始化 stop_event（asyncio.Event）
- **AND** 系统初始化并发控制锁（asyncio.Lock）

#### Scenario: 重置 Token Manager
- **WHEN** 应用程序调用 `QwenTokenManager.reset()`
- **THEN** 系统调用现有实例的 `shutdown()` 方法
- **AND** 系统清除单例实例
- **AND** 下次调用 `get_instance()` 将创建新实例

### Requirement: Token 获取接口

系统必须提供简洁的 token 获取接口。由于定时任务自动管理刷新，`get_access_token()` 方法应直接返回当前 token，无需检查过期状态。接口应为异步方法，支持并发调用。

#### Scenario: 首次获取 token
- **WHEN** 应用程序首次调用 `get_access_token()`
- **THEN** 系统从持久化存储加载或认证获取 token
- **AND** 系统启动定时刷新任务
- **AND** 系统返回 access_token

#### Scenario: 后续获取 token
- **WHEN** 应用程序再次调用 `get_access_token()`
- **THEN** 系统直接返回当前 token
- **AND** 系统不检查过期状态（定时任务负责）
- **AND** 调用立即返回，无性能开销

#### Scenario: 异步并发调用
- **WHEN** 多个协程同时调用 `get_access_token()`
- **THEN** 所有协程都获得有效的 token
- **AND** 不会产生竞态条件

### Requirement: 刷新失败降级策略

系统必须在定时刷新失败时提供降级策略。如果刷新失败但旧 token 尚未过期，系统应保持服务可用。如果旧 token 也已过期，系统应抛出明确的异常，指导用户重新认证。

#### Scenario: 刷新失败但旧 token 仍有效
- **WHEN** 定时任务刷新失败
- **AND** 旧的 access_token 尚未过期
- **THEN** 系统记录警告日志
- **AND** 系统保留旧 token，继续提供服务
- **AND** 系统等待 60 秒后重试刷新

#### Scenario: 刷新失败且旧 token 已过期
- **WHEN** 定时任务刷新失败
- **AND** 旧的 access_token 也已过期
- **THEN** 系统抛出 `QwenTokenExpiredError` 异常
- **AND** 系统停止定时刷新任务
- **AND** 异常信息提示用户重新认证

#### Scenario: Refresh token 失效
- **WHEN** 定时任务收到 400 错误（refresh_token 无效）
- **THEN** 系统抛出 `QwenRefreshTokenInvalidError` 异常
- **AND** 系统停止定时刷新任务
- **AND** 系统清除本地 token
- **AND** 异常信息提示用户重新进行设备码认证
