# Design: 后端聊天接口集成模型配置

## Context

### 当前状态

后端聊天接口（`/chat/stream`）目前使用硬编码的环境变量来配置 AI 模型：

```python
model=OpenAIChatModel(
    model_name=os.getenv("COMMON_MODEL_NAME"),
    api_key=os.getenv("COMMON_MODEL_API_KEY"),
    client_args={"base_url": os.getenv("COMMON_MODEL_BASE_URL")},
)
```

这种方式存在以下限制：
- 无法在运行时动态切换模型
- 需要重启服务才能更改模型配置
- 用户在前端选择的模型配置无法实际应用到聊天会话

### 已有基础设施

系统已具备完整的模型配置管理功能：
- **数据库表**: `model_configs` 存储配置（provider、base_url、api_key、models）
- **API 端点**: `/api/models/configs` 提供 CRUD 操作
- **服务层**: `ModelConfigService` 处理业务逻辑
- **前端集成**: ModelSelector 组件已实现模型选择

### 技术约束

1. **AgentScope 限制**: `ReActAgent` 不支持运行时更换 `model` 属性
2. **性能要求**: 同一会话中，大部分时候使用相同模型，应避免不必要的 Agent 重建
3. **一致性要求**: 分析 Agent（用于 `analyse_by_code` 工具）必须使用与主 Agent 相同的模型
4. **开发阶段**: 当前优先实现功能，性能优化（如配置缓存）可后续进行

---

## Goals / Non-Goals

### Goals

1. **动态模型选择**: 聊天接口支持通过 `model_config_id` + `model_id` 动态选择模型
2. **精确模型控制**: 用户可以指定配置中的具体模型，而非仅使用第一个模型
3. **运行时切换**: 同一会话的不同轮次可以使用不同的模型配置或不同的模型
4. **Provider 支持**: 支持 OpenAI 和 Qwen 两种模型提供商
5. **安全验证**: 在处理请求前验证模型配置和模型 ID 的有效性
6. **Agent 复用**: 当 `model_config_id` 和 `model_id` 都未变化时，复用现有 Agent
7. **双层选择器 UI**: 前端提供双层选择器，第一层选择配置，第二层选择模型

### Non-Goals

1. **配置缓存**: 不在内存中缓存模型配置（每次从数据库读取）
2. **自动模型选择**: 不在配置未指定 model_id 时自动选择第一个模型（必须明确指定）
3. **性能优化**: 不引入复杂的缓存或预热机制（可在后续阶段优化）
4. **向后兼容**: 不提供环境变量后备方案（`model_config_id` 和 `model_id` 为必填字段）

---

## Decisions

### 决策 1: 使用 Agent 重建机制而非修改属性

**选择**: 当 `model_config_id` 变化时，重新创建 Agent 实例。

**替代方案**:
- 直接修改 `agent.model` 属性
- 使用装饰器或代理模式

**理由**:
1. **安全性**: AgentScope 的 `ReActAgent` 可能内部缓存了模型状态，运行时修改可能导致不一致
2. **并发安全**: 重建 Agent 避免了修改正在使用的 Agent 的并发问题
3. **简洁性**: 重建逻辑清晰，易于理解和维护
4. **性能可接受**: 通过复用机制（见决策 2），大部分请求不会触发重建

**实现**:
```python
class TushareSession(Session):
    def __init__(self, ...):
        self._current_model_config_id: int | None = None
        self._current_agent: AgentBase | None = None

    async def chat(self, user_input: str, model_config_id: int):
        if self._current_model_config_id != model_config_id:
            await self._switch_model(model_config_id)
        # 使用 self._current_agent 处理消息
```

---

### 决策 2: 实现 Agent 复用机制

**选择**: Session 缓存当前的 `model_config_id`、`model_id` 和 Agent 实例，仅当任一值变化时重建。

**替代方案**:
- 每次请求都重建 Agent
- 使用全局 Agent 池

**理由**:
1. **性能优化**: 同一会话中，大部分时候使用相同模型，复用避免不必要的重建
2. **会话隔离**: 每个 Session 维护自己的 Agent，避免全局状态
3. **精确比较**: 比较 `model_config_id` 和 `model_id` 两个值，确保完全一致时才复用

**实现**:
```python
if (self._current_model_config_id != model_config_id or
    self._current_model_id != model_id):
    # 重建 Agent
else:
    # 复用现有 Agent
```

---

### 决策 3: 在路由层验证配置和模型的有效性

**选择**: 在聊天路由（`router.py`）中调用 `ModelConfigService` 验证配置和模型 ID。

**替代方案**:
- 在 Session 内部验证
- 使用 FastAPI 的依赖注入验证

**理由**:
1. **早期验证**: 在创建 Agent 前验证，避免无效请求进入业务逻辑
2. **清晰错误**: 可在路由层返回明确的 HTTP 错误（404、400）
3. **职责分离**: 路由负责验证，Session 负责使用

**实现**:
```python
@router.post("/stream")
async def chat_stream(request: ChatRequest, session: SessionDep):
    # 验证配置
    service = ModelConfigService(session)
    config = await service.get_model_config(request.model_config_id)

    # 验证配置是否启用
    if not config.is_active:
        raise HTTPException(status_code=400, detail="配置已禁用")

    # 验证 model_id 是否在配置中
    model_ids = [m.model_id for m in config.models]
    if request.model_id not in model_ids:
        raise HTTPException(
            status_code=400,
            detail=f"模型 ID '{request.model_id}' 不在配置中。可用模型: {model_ids}"
        )

    # 创建或获取 Session
    session_id, session = get_session(context, request.session_id)
    async for msg in session.chat(
        request.user_input,
        request.model_config_id,
        request.model_id
    ):
        ...
```

---

### 决策 4: 使用 ModelFactory 工厂模式

**选择**: 创建 `ModelFactory` 类，根据配置创建对应的模型实例。

**替代方案**:
- 在 Session 中直接创建模型
- 使用策略模式

**理由**:
1. **单一职责**: ModelFactory 专注于模型创建，Session 专注于会话管理
2. **可扩展性**: 未来支持新 Provider 时，只需在 ModelFactory 中添加逻辑
3. **可测试性**: 可独立测试模型创建逻辑

**实现**:
```python
class ModelFactory:
    @staticmethod
    def create_model(config: ModelConfigResponse, model_id: str):
        if config.provider == "openai":
            return ModelFactory._create_openai_model(config, model_id)
        elif config.provider == "qwen":
            return ModelFactory._create_qwen_model(config, model_id)
        else:
            raise ValueError(f"不支持的 provider: {config.provider}")
```

---

### 决策 5: 分析 Agent 使用与主 Agent 相同的配置和模型

**选择**: 分析 Agent（用于 `analyse_by_code`）使用当前缓存的 `model_config_id` 和 `model_id` 创建。

**替代方案**:
- 分析 Agent 使用独立的模型配置
- 每次调用时重新选择模型

**理由**:
1. **一致性**: 主对话和代码分析使用相同的模型能力
2. **简化**: 避免引入额外的配置选择逻辑
3. **用户期望**: 用户选择的模型应用于整个会话

**实现**:
```python
async def _get_analyse_by_code_agent(self, analyse_id: int):
    # 使用与主 Agent 相同的配置和模型
    if self._current_model_config_id is None or self._current_model_id is None:
        raise ValueError("主 Agent 尚未初始化")

    config = await self._get_model_config(self._current_model_config_id)
    model = ModelFactory.create_model(config, self._current_model_id)

    return ReActAgent(model=model, ...)
```

---

### 决策 6: Session 的 chat 方法接受 model_config_id 和 model_id 参数

**选择**: 修改 `Session.chat(user_input: str)` 为 `Session.chat(user_input: str, model_config_id: int, model_id: str)`。

**替代方案**:
- 在 Session 初始化时传入配置
- 使用上下文变量传递配置

**理由**:
1. **灵活性**: 支持会话中切换模型配置或模型
2. **显式性**: 每次调用明确指定使用的配置和模型
3. **一致性**: 路由层和 Session 层的参数保持一致

---

## 架构设计

### 组件交互流程

```text
┌─────────────┐
│   Client    │
└─────┬───────┘
      │ POST /chat/stream
      │ { session_id, user_input, model_config_id, model_id }
      ▼
┌─────────────────────────────────────┐
│      Chat Router (router.py)        │
│  1. 验证 model_config_id             │
│  2. 验证 model_id 是否在配置中        │
│  3. 检查配置是否启用                  │
│  4. 获取或创建 Session               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│    TushareSession (Session)         │
│  1. 比较 (config_id, model_id)       │
│  2. 如果任一不同，重建 Agent          │
│  3. 如果都相同，复用 Agent            │
│  4. 调用 Agent 处理消息               │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      ModelFactory                   │
│  根据 provider 和 model_id 创建      │
│  - openai → OpenAIChatModel          │
│  - qwen → QwenChatModel              │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│      ReActAgent                     │
│  使用指定的模型处理消息               │
└─────────────────────────────────────┘
```

### 数据流

1. **请求阶段**:
   ```text
   Client → Router → 验证配置和模型 → Session.chat(model_config_id, model_id)
   ```

2. **Agent 创建/复用**:
   ```text
   Session → 比较 (config_id, model_id) → ModelFactory → ReActAgent
   ```

3. **响应阶段**:
   ```text
   ReActAgent → Session → Router → Client (SSE Stream)
   ```

---

## Risks / Trade-offs

### Risk 1: Agent 重建的性能开销

**描述**: 当用户频繁切换模型配置时，每次切换都会触发 Agent 重建，可能影响性能。

**缓解措施**:
- 实现了 Agent 复用机制，避免不必要的重建
- 同一会话中，大部分时候使用相同模型，重建频率低
- 未来可引入配置缓存或 Agent 池进一步优化

---

### Risk 2: 数据库查询频率

**描述**: 每次切换模型时都需要查询数据库，可能成为性能瓶颈。

**缓解措施**:
- 仅在 `model_config_id` 变化时查询，不是每次请求都查询
- 开发阶段可接受，生产环境可后续引入缓存
- 数据库查询有索引，性能影响有限

---

### Risk 3: 并发安全问题

**描述**: 如果多个请求同时到达，并发重建 Agent 可能导致竞态条件。

**缓解措施**:
- FastAPI 的异步特性确保单个 Session 的请求是串行处理的
- Agent 重建是原子操作（先清空再创建），不会出现中间状态
- 未来可引入锁机制进一步保护

---

### Risk 4: 分析 Agent 的配置依赖

**描述**: 分析 Agent 依赖主 Agent 先创建，如果主 Agent 未初始化会报错。

**缓解措施**:
- 在 `TushareSession.__init__` 中创建初始 Agent
- 添加防御性检查，如果主 Agent 未创建则抛出明确错误

---

## 实现要点

### 1. ModelFactory 实现

**位置**: `src/one_dragon_agent/core/model/model_factory.py`

**关键方法**:
- `create_model(config, model_id)`: 根据配置创建模型
- `get_first_model_id(config)`: 获取第一个模型 ID

**Provider 支持**:
- `openai`: 使用 `OpenAIChatModel`，传入 `base_url`、`api_key`、`model_id`
- `qwen`: 使用 `QwenChatModel`，仅传入 `model_id`（OAuth 认证）

---

### 2. TushareSession 修改

**位置**: `src/one_dragon_alpha/agent/tushare/tushare_session.py`

**新增属性**:
```python
self._current_model_config_id: int | None = None
self._current_agent: AgentBase | None = None
self._model_config_service: ModelConfigService
```

**新增方法**:
```python
async def _switch_model(self, model_config_id: int):
    """切换模型配置，重建主 Agent 和分析 Agent"""
    config = await self._model_config_service.get_model_config(model_config_id)
    model_id = ModelFactory.get_first_model_id(config)
    model = ModelFactory.create_model(config, model_id)

    # 重建主 Agent
    self._current_agent = self._get_main_agent_with_model(model)

    # 清空分析 Agent 缓存
    self._analyse_by_code_map.clear()
    self._current_model_config_id = model_config_id
```

**修改方法**:
- `chat(user_input, model_config_id)`: 添加 `model_config_id` 参数，实现切换逻辑
- `_get_main_agent_with_model(model)`: 新建 Agent 时接受指定的 model 实例

---

### 3. Chat Router 修改

**位置**: `src/one_dragon_alpha/server/chat/router.py`

**修改 `ChatRequest`**:
```python
class ChatRequest(BaseModel):
    session_id: str | None = None
    user_input: str
    model_config_id: int  # 新增必填字段
```

**添加依赖注入**:
```python
async def get_db_session() -> AsyncSession:
    # 复用模型配置路由的 get_db_session
    ...

SessionDep = Annotated[AsyncSession, Depends(get_db_session)]
```

**修改 `chat_stream` 端点**:
```python
@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    session: SessionDep,  # 新增数据库会话
    context: ContextDep
):
    # 验证配置
    service = ModelConfigService(session)
    config = await service.get_model_config(request.model_config_id)
    if not config.is_active:
        raise HTTPException(status_code=400, detail="配置已禁用")

    # 调用 Session
    session_id, tushare_session = get_session(context, request.session_id)
    return StreamingResponse(
        stream_response_generator(
            session_id=session_id,
            session=tushare_session,
            user_input=request.user_input,
            model_config_id=request.model_config_id,  # 传递配置
        ),
        ...
    )
```

---

### 4. Session 基类修改

**位置**: `src/one_dragon_alpha/session/session.py`

**修改 `chat` 方法签名**:
```python
async def chat(self, user_input: str, model_config_id: int) -> AsyncGenerator[SessionMessage, None]:
    """添加 model_config_id 参数"""
```

---

## Open Questions

1. **Q: Session 创建时是否需要初始 model_config_id？**
   - **A**: 当前设计不要求。第一次聊天请求时才创建 Agent。未来可考虑在 Session 创建时传入默认配置。

2. **Q: 如何处理 Agent 创建失败的情况？**
   - **A**: 捕获异常并返回 HTTP 500 错误，包含详细错误信息。

3. **Q: 是否需要支持配置热更新（不重建 Agent）？**
   - **A**: 不在当前范围内。如果配置更新（如 api_key 变化），下次切换时会使用新配置。

4. **Q: 分析 Agent 的内存是否需要清理？**
   - **A**: 切换模型时会清空 `_analyse_by_code_map`，允许旧 Agent 被垃圾回收。

---

## 测试策略

### 单元测试

1. **ModelFactory 测试**:
   - 测试创建 OpenAI 模型
   - 测试创建 Qwen 模型
   - 测试不支持的 provider 抛出异常

2. **Session 测试**:
   - 测试首次请求创建 Agent
   - 测试相同 config_id 复用 Agent
   - 测试不同 config_id 重建 Agent
   - 测试分析 Agent 使用相同配置

3. **Router 测试**:
   - 测试缺少 model_config_id 返回 400
   - 测试不存在的 config_id 返回 404
   - 测试已禁用的 config_id 返回 400

### 集成测试

1. **端到端测试**:
   - 创建模型配置
   - 发送聊天请求使用该配置
   - 切换到不同的配置
   - 验证响应使用正确的模型

---

## 未来优化

1. **配置缓存**: 在内存中缓存模型配置，减少数据库查询
2. **Agent 池**: 预创建常用配置的 Agent，进一步减少重建开销
3. **模型级选择**: 支持在单个配置中选择特定的模型（而非仅使用第一个）
4. **性能监控**: 添加 Agent 重建频率和耗时监控
