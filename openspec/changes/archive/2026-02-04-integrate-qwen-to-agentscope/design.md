# Qwen 模型集成技术设计

## Context

### 当前状态

项目使用 AgentScope 框架构建 AI Agent 应用，当前通过 `OpenAIChatModel` 接入大模型。模型配置通过环境变量设置（`COMMON_MODEL_NAME`, `COMMON_MODEL_API_KEY`, `COMMON_MODEL_BASE_URL`），在初始化时固定 API key。

### 问题背景

Qwen 提供了 OpenAI 兼容的 API 接口，但使用 OAuth 2.0 设备码流程进行认证，具有以下特点：

1. **Token 有时效性**: access_token 通常几小时后过期，需要使用 refresh_token 刷新
2. **设备码流程**: 适用于无浏览器环境，用户需在另一设备完成授权
3. **Token 自动刷新**: 为避免频繁重新认证，需要自动刷新机制

现有 `OpenAIChatModel` 的限制：
- 在 `__init__` 时固定 `api_key`，无法动态更新
- OpenAI Python SDK 不支持在现有 client 实例上修改 API key

### 约束条件

- **语言**: Python 3.11+
- **框架**: AgentScope 1.0.14+
- **编码**: UTF-8
- **URL 固定**: OAuth 和 API base URL 不可自定义
- **向后兼容**: 不影响现有 `OpenAIChatModel` 使用

## Goals / Non-Goals

**Goals:**

1. 封装 `QwenChatModel` 类，继承 `OpenAIChatModel`，自动处理 OAuth 认证
2. 实现 OAuth 2.0 设备码流程，支持 PKCE 安全增强
3. 提供 token 持久化存储，避免重复认证
4. 实现 token 自动定时刷新机制，确保调用不中断

**Non-Goals:**

1. 不支持自定义 OAuth 服务器 URL 和 API base URL（固定为官方地址）
2. 不实现 token 加密存储（仅文件权限保护）
3. 不支持多账户管理（单例 TokenManager）
4. 不修改 AgentScope 框架本身
5. 不在 QwenChatModel 层支持环境变量配置（由上层应用处理）

## Decisions

### 决策 1: QwenChatModel 继承 OpenAIChatModel

**选择**: 让 `QwenChatModel` 继承 `OpenAIChatModel`，在 `_call` 方法中处理 token 刷新和 client 重建。

**理由**:
- Qwen API 完全兼容 OpenAI 格式，继承可复用所有核心逻辑
- 用户可在任何使用 `OpenAIChatModel` 的场景无缝替换
- 最小化代码量，降低维护成本

**替代方案**:
- **方案 A**: 直接复制 `OpenAIChatModel` 代码并修改
  - ❌ 代码重复，维护成本高
  - ❌ 无法跟随 AgentScope 更新
- **方案 B**: 组合模式，将 `OpenAIChatModel` 作为成员
  - ❌ 需要代理所有方法，复杂度高

**实现细节**:
```python
class QwenChatModel(OpenAIChatModel):
    def __init__(self, model_name: str, ...):
        self._token_manager = QwenTokenManager.get_instance()
        token = self._token_manager.get_access_token()

        super().__init__(
            model_name=model_name,
            api_key=token,
            client_args={"base_url": "https://portal.qwen.ai/v1"},
        )

    def _call(self, *args, **kwargs):
        # 检查 token 是否过期，必要时刷新
        if self._token_manager.is_expired():
            new_token = self._token_manager.refresh_token()
            self._recreate_client(new_token)

        return super()._call(*args, **kwargs)

    def _recreate_client(self, new_token: str):
        """重新创建 OpenAI client"""
        self.client = openai.AsyncOpenAI(
            api_key=new_token,
            base_url="https://portal.qwen.ai/v1",
        )
```

### 决策 2: TokenManager 使用单例模式

**选择**: `QwenTokenManager` 使用单例模式，全局唯一实例。

**理由**:
- 多个 `QwenChatModel` 实例共享同一个 token，避免重复认证
- 防止并发刷新冲突（使用 asyncio.Lock 保护）
- 简化配置管理

**实现细节**:
```python
class QwenTokenManager:
    _instance: ClassVar[Optional["QwenTokenManager"]] = None
    _lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    @classmethod
    def get_instance(cls) -> "QwenTokenManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def refresh_token(self) -> str:
        async with self._lock:
            # 只允许一个协程执行刷新
            ...
```

### 决策 3: Token 刷新策略

**选择**: TokenManager 在获取 token 后启动后台定时任务，自动刷新 token，无需在每次调用时检查。

**理由**:
- **性能优越**: 不在每次模型调用时检查过期时间，零性能开销
- **简化调用**: `get_access_token()` 直接返回当前 token，无需判断逻辑
- **可靠性高**: 定时任务独立运行，不依赖模型调用频率
- **资源可控**: TokenManager 失效时自动取消定时任务

**替代方案**:
- **方案 A**: 每次调用前检查是否过期
  - ❌ 每次调用都有性能开销
  - ❌ 增加调用复杂度
- **方案 B**: 仅在 API 返回 401 时刷新
  - ❌ 每次过期都会有一次失败请求
  - ❌ 用户体验差

**实现细节**:
```python
class QwenTokenManager:
    def __init__(self):
        self._token: Optional[QwenOAuthToken] = None
        self._refresh_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()

    async def get_access_token(self) -> str:
        """获取当前 access token（异步）"""
        if self._token is None:
            self._token = await self._load_or_authenticate()
            self._start_refresh_timer()
        return self._token.access_token

    def _start_refresh_timer(self):
        """启动定时刷新任务"""
        if self._refresh_task and not self._refresh_task.done():
            return  # 已在运行

        self._refresh_task = asyncio.create_task(self._refresh_loop())

    async def _refresh_loop(self):
        """定时刷新循环"""
        while not self._stop_event.is_set():
            # 计算下次刷新时间（提前 5 分钟）
            expires_at = self._token.expires_at
            refresh_at = expires_at - 5 * 60 * 1000  # 提前 5 分钟
            now_ms = int(time.time() * 1000)

            if refresh_at > now_ms:
                wait_seconds = (refresh_at - now_ms) / 1000
            else:
                wait_seconds = 60  # 默认等待 1 分钟

            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=wait_seconds
                )
                break  # 收到停止信号
            except asyncio.TimeoutError:
                pass  # 超时，执行刷新

            # 刷新 token
            try:
                self._token = await self._refresh_token()
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                # 刷新失败，等待后重试
                await asyncio.sleep(60)

    async def shutdown(self):
        """关闭 TokenManager，取消定时任务"""
        self._stop_event.set()
        if self._refresh_task:
            self._refresh_task.cancel()
            try:
                await self._refresh_task
            except asyncio.CancelledError:
                pass
```

**使用示例**:
```python
# 应用启动时
token_manager = QwenTokenManager.get_instance()
await token_manager.get_access_token()  # 首次认证并启动定时任务

# 任意时刻调用，无需检查过期
token = await token_manager.get_access_token()

# 应用关闭时
await token_manager.shutdown()
```

### 决策 4: Refresh Token 端点设计

**选择**: 使用 `/api/v1/oauth2/token` 端点，`grant_type=refresh_token`（已验证可用）。

**理由**:
- OAuth 2.0 标准流程
- Qwen API 已确认支持此方式
- 不需要 PKCE 参数（仅设备码流程需要）

**实现细节**（基于实际示例）:
```python
async def _refresh_with_refresh_token(self) -> QwenOAuthToken:
    response = await httpx.async_client.post(
        "https://chat.qwen.ai/api/v1/oauth2/token",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        data={
            "grant_type": "refresh_token",
            "refresh_token": self._token.refresh_token,
            "client_id": self._client_id,
        },
    )

    if response.status_code == 400:
        # refresh_token 过期或无效
        raise QwenRefreshTokenInvalidError(
            "Qwen OAuth refresh token expired or invalid. Please re-authenticate."
        )

    response.raise_for_status()

    payload = response.json()

    # 使用返回的 expires_in（秒）计算绝对过期时间（毫秒）
    # 示例：expires_in=7200（2小时），则 expires_at = now + 7200000
    return QwenOAuthToken(
        access_token=payload["access_token"],
        refresh_token=payload.get("refresh_token") or self._token.refresh_token,
        expires_at=int(time.time() * 1000) + payload["expires_in"] * 1000,
    )
```

**刷新时间计算**:
```python
# 在 _refresh_loop() 中
expires_at = self._token.expires_at  # 绝对时间戳（毫秒）
refresh_at = expires_at - 5 * 60 * 1000  # 提前 5 分钟刷新
wait_seconds = (refresh_at - int(time.time() * 1000)) / 1000
```

### 决策 5: Token 存储格式

**选择**: JSON 文件存储，路径为 `~/.qwen/token.json`，文件权限 0600。

**理由**:
- JSON 可读性好，便于调试
- 文件权限保护敏感信息
- 符合 Unix 传统（如 `~/.ssh`）

**数据结构**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_at": 1735689600000,
  "resource_url": "https://portal.qwen.ai",
  "client_id": "f0304373b74a44d2b584a3fb70ca9e56"
}
```

## Architecture

### 模块结构

```
src/one_dragon_agent/core/model/qwen/
├── __init__.py                 # 导出 QwenChatModel
├── qwen_chat_model.py          # QwenChatModel 实现
├── oauth.py                    # OAuth 认证逻辑
│   ├── QwenOAuthClient         # OAuth 2.0 设备码流程
│   ├── PKCE helpers            # PKCE 相关函数
│   └── Token models            # QwenOAuthToken 等数据类
└── token_manager.py            # Token 管理器
    ├── QwenTokenManager        # 单例 token 管理器
    └── TokenPersistence        # Token 文件存储
```

### 交互流程

```
┌─────────────────┐
│ QwenChatModel   │
│  (inherits      │
│  OpenAIChatModel)
└────────┬────────┘
         │ 1. __init__()
         │    get_access_token()
         ▼
┌─────────────────────────────┐
│  QwenTokenManager (singleton)│
│  - token                     │
│  - refresh_task (asyncio.Task)│
└────────┬────────────────────┘
         │ 2. 首次调用？
         │    ├─ Yes → 3. 加载或认证
         │    │         └─> 4. 启动定时刷新任务
         │    └─ No  → 5. 直接返回 token
         │ 6. 后台定时刷新（独立运行）
         │    └─> 每隔 (expires_at - 5min) 刷新一次
         ▼
┌─────────────────┐
│ QwenOAuthClient │
│  - PKCE         │
│  - HTTP requests│
└─────────────────┘
         │ 7. save token
         ▼
┌─────────────────┐
│TokenPersistence │
│  - ~/.qwen/     │
│    token.json   │
└─────────────────┘

定时刷新流程（独立运行）:
┌──────────────────────────────────┐
│  _refresh_loop()                  │
│  1. 等待 (expires_at - 5min)      │
│  2. 调用 _refresh_token()        │
│  3. 更新 self._token              │
│  4. 保存到文件                    │
│  5. 循环回到步骤 1                │
│  (直到收到 stop_event)            │
└──────────────────────────────────┘
```

### OAuth 设备码流程

```
User                    QwenChatModel              QwenOAuthClient              Qwen Server
  │                            │                            │                            │
  │  1. 首次调用                │                            │                            │
  ├───────────────────────────>│                            │                            │
  │                            │  2. get_device_code()      │                            │
  │                            ├───────────────────────────>│                            │
  │                            │                            │  3. POST /device/code      │
  │                            │                            ├───────────────────────────>│
  │                            │                            │  4. device_code + user_code│
  │                            │                            │<───────────────────────────┤
  │                            │  5. 显示 user_code         │                            │
  │<───────────────────────────┤                            │                            │
  │  6. 浏览器输入 user_code    │                            │                            │
  │  ───────────────────────>  │                            │                            │
  │                            │                            │  7. 轮询 /token            │
  │                            │  8. poll_device_token()    ├───────────────────────────>│
  │                            │  (每 2 秒)                 │  9. pending/pending/...    │
  │                            │                            │<───────────────────────────┤
  │                            │                            │ 10. success!               │
  │                            │                            │<───────────────────────────┤
  │                            │ 11. return token           │                            │
  │                            │<───────────────────────────┤                            │
  │                            │ 12. save token             │                            │
  │                            ├───────────────────────────>│                            │
  │                            │ 13. return access_token    │                            │
  │<───────────────────────────┤                            │                            │
```

## Risks / Trade-offs

### 风险 1: Refresh Token 过期

**风险**: refresh_token 也可能过期（如长期未使用），返回 400 错误。

**缓解措施**:
1. 捕获 400 错误，抛出 `QwenRefreshTokenInvalidError`
2. 提示用户重新进行设备码认证
3. 在文档中明确说明此限制
4. 考虑实现 refresh_token 的定期刷新（如果 Qwen 支持）

### 风险 2: 并发请求的 Token 刷新

**风险**: 多个协程同时检测到 token 过期，可能重复刷新。

**缓解措施**:
1. 使用单例 `QwenTokenManager`
2. 使用 `asyncio.Lock` 保护刷新操作
3. 等待中的协程使用刷新后的 token

### 风险 3: Token 文件权限问题

**风险**: 在 Windows 或某些文件系统上，0600 权限可能不生效。

**缓解措施**:
1. 使用 `pathlib.Path.chmod()` 设置权限
2. 捕获 `OSError`，记录警告但不中断流程
3. 建议用户设置正确的文件权限

### 风险 4: 定时任务资源占用

**风险**: 后台定时刷新任务会占用一个 asyncio.Task 和相关资源。

**缓解措施**:
1. 使用单例 TokenManager，全局只有一个定时任务
2. 提供 `shutdown()` 方法，应用关闭时必须调用
3. 使用 `stop_event` 优雅停止任务
4. 定时任务仅在获取 token 后启动，未使用时不占用资源

### Trade-off 1: 灵活性 vs 复杂度

**选择**: 固定 OAuth 和 API URL，不支持自定义。

**权衡**:
- ✅ 简化配置和实现
- ✅ 降低用户出错可能
- ❌ 无法适配私有部署或代理场景

**理由**: 大多数用户使用官方 Qwen 服务，固定 URL 可满足 99% 需求。

## Implementation Plan

### Phase 1: OAuth 认证 (Foundation)

**目标**: 实现 OAuth 2.0 设备码流程

**任务**:
1. 创建 `oauth.py`，实现 `QwenOAuthClient`
   - `get_device_code()`: 获取设备码
   - `poll_device_token()`: 轮询授权状态
   - `login_qwen_oauth()`: 完整流程
2. 实现 PKCE 辅助函数
   - `generate_pkce()`: 生成 verifier 和 challenge
3. 定义数据模型
   - `QwenDeviceAuthorization`
   - `QwenOAuthToken`

**测试**:
- Mock Qwen OAuth 端点响应
- 验证 PKCE 参数正确性
- 测试轮询超时和错误处理

### Phase 2: Token 管理 (Core)

**目标**: 实现 token 持久化和自动定时刷新

**任务**:
1. 创建 `token_manager.py`，实现 `QwenTokenManager`
   - 单例模式
   - `get_access_token()`: 获取当前 token（异步）
   - `shutdown()`: 取消定时任务，清理资源
   - 并发控制（asyncio.Lock 用于刷新操作）
2. 创建 `TokenPersistence` 类
   - `save_token()`: 保存到文件
   - `load_token()`: 从文件加载
   - `delete_token()`: 删除 token
3. 实现定时刷新逻辑
   - `_start_refresh_timer()`: 启动后台定时任务
   - `_refresh_loop()`: 定时刷新循环
   - `_refresh_token()`: 实际刷新操作
   - 尝试 refresh_token 端点
   - 失败处理和重试

**测试**:
- 测试 token 文件读写
- 测试定时刷新任务启动和停止
- 测试刷新失败重试
- 测试并发场景

### Phase 3: QwenChatModel (Integration)

**目标**: 集成到 AgentScope

**任务**:
1. 创建 `qwen_chat_model.py`，实现 `QwenChatModel`
   - 继承 `OpenAIChatModel`
   - 初始化时从 TokenManager 获取 token
   - 由于 TokenManager 自动刷新，无需在 `_call` 中检查
2. 创建 `__init__.py`，导出公共 API
   - `QwenChatModel`
   - 相关异常类

**测试**:
- 集成测试：真实调用 Qwen API
- 测试多模型类型（coder, vision）
- 测试 TokenManager 生命周期

### Phase 4: 测试和文档 (Polish)

**目标**: 完善测试和文档

**任务**:
1. 编写单元测试
   - OAuth 流程测试
   - Token 管理测试
   - QwenChatModel 测试
2. 更新文档
   - API 文档
   - 使用示例
   - TokenManager 生命周期说明

## Open Questions

### Q1: Token 生命周期长度？

**状态**: 待实际测试验证

**影响**: 决定提前刷新的缓冲区大小（当前假设 5 分钟）

**方法**: 实际测试获取 `expires_in` 值，根据实际情况调整缓冲区

**说明**: 典型的 OAuth token 生命周期为 1-24 小时，当前假设的 5 分钟缓冲区适用于大多数场景。

## Dependencies

### 内部依赖
- `agentscope.models.OpenAIChatModel`
- `one_dragon_agent.core.system.log.get_logger`

### 外部依赖
- `agentscope>=1.0.14` (已有)
- `httpx` (用于 OAuth HTTP 请求)
- `openai` (AgentScope 依赖)

### 无新增外部依赖
- 使用 `pathlib` 处理文件路径
- 使用 `asyncio` 处理并发
- 使用 `json` 处理序列化
- 使用 `hashlib` 实现 PKCE
