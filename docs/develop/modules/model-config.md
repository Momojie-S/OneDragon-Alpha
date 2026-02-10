# 模型配置管理模块

## 模块概述

模型配置管理模块提供了统一的模型配置管理功能，支持创建、查询、更新、删除模型配置，以及测试 API 连接。

## 核心功能

### 1. 配置管理

- **创建配置**: 创建新的模型配置，包含 API Key、Base URL、模型列表等信息
- **查询配置**: 支持分页查询和过滤（按启用状态、Provider）
- **更新配置**: 更新配置信息，使用乐观锁防止并发冲突
- **删除配置**: 删除不需要的配置
- **状态切换**: 快速启用/禁用配置

### 2. 连接测试

- 测试 API 连接是否可用
- 使用用户配置的模型 ID 发送测试请求
- 返回详细的错误信息

### 3. 数据安全

- API Key 不在响应中返回
- 支持更新时选择性修改 API Key

## 模块结构

```
one_dragon_agent/core/model/
├── __init__.py
├── models.py           # Pydantic 数据模型
├── repository.py       # 数据库访问层
├── service.py          # 业务逻辑层
├── router.py           # FastAPI 路由
└── migrations/         # 数据库迁移脚本
```

## 核心 API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/models/configs` | 创建配置 |
| GET | `/api/models/configs` | 获取配置列表 |
| GET | `/api/models/configs/{id}` | 获取单个配置 |
| PUT | `/api/models/configs/{id}` | 更新配置 |
| DELETE | `/api/models/configs/{id}` | 删除配置 |
| PATCH | `/api/models/configs/{id}/status` | 切换启用状态 |
| POST | `/api/models/configs/test-connection` | 测试连接 |

## 数据模型

### ModelConfigCreate

```python
class ModelConfigCreate(BaseModel):
    name: str                    # 配置名称（唯一）
    provider: Literal["openai"]  # 提供商
    base_url: str                # API 基础 URL
    api_key: str                 # API 密钥
    models: list[ModelInfo]      # 模型列表
    is_active: bool = True       # 是否启用
```

### ModelInfo

```python
class ModelInfo(BaseModel):
    model_id: str           # 模型 ID
    support_vision: bool    # 是否支持视觉
    support_thinking: bool  # 是否支持思考
```

## 使用示例

### 创建配置

```python
from one_dragon_agent.core.model.models import ModelConfigCreate, ModelInfo

config = ModelConfigCreate(
    name="OpenAI GPT-4",
    provider="openai",
    base_url="https://api.openai.com",
    api_key="sk-...",
    models=[
        ModelInfo(
            model_id="gpt-4",
            support_vision=True,
            support_thinking=False
        )
    ]
)
```

### 测试连接

```python
from one_dragon_agent.core.model.models import TestConnectionRequest

request = TestConnectionRequest(
    base_url="https://api.openai.com",
    api_key="sk-...",
    model_id="gpt-4"
)

result = await ModelConfigService.test_connection(request)
```

## 前端集成

### API 服务

```typescript
import { modelApiService } from '@/services/modelApi'

// 创建配置
await modelApiService.createModelConfig(data)

// 获取配置列表
const result = await modelApiService.getModelConfigs({
  page: 1,
  page_size: 20,
  active: true
})

// 测试连接
const testResult = await modelApiService.testConnection({
  base_url: 'https://api.openai.com',
  api_key: 'sk-...',
  model_id: 'gpt-4'
})
```

### 路由

- `/model-management` - 模型配置管理页面

## 数据库表结构

### model_configs

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| name | VARCHAR(255) | 配置名称（唯一） |
| provider | VARCHAR(50) | 提供商 |
| base_url | TEXT | API 基础 URL |
| api_key | TEXT | API 密钥 |
| models | JSON | 模型列表 |
| is_active | BOOLEAN | 是否启用 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间（乐观锁） |

### 索引

- `idx_name` - name 字段
- `idx_provider` - provider 字段
- `idx_is_active` - is_active 字段

## 乐观锁机制

更新配置时使用 `updated_at` 字段实现乐观锁：

1. 客户端获取配置时记录 `updated_at`
2. 更新时发送该时间戳
3. 服务端验证时间戳，如果与数据库不一致则拒绝更新

## 错误处理

| HTTP 状态码 | 描述 |
|-------------|------|
| 400 | 请求参数错误 |
| 404 | 配置不存在 |
| 409 | 乐观锁冲突 |
| 422 | 验证错误 |
| 500 | 服务器内部错误 |

## 测试

运行测试：

```bash
# 后端测试
uv run --env-file .env pytest tests/one_dragon_agent/core/model/

# 前端测试
cd frontend
pnpm test
```

## 注意事项

1. **API Key 安全**: 响应中不包含 `api_key` 字段
2. **Provider 支持**: 支持 `openai` 和 `qwen` 两种 provider
3. **模型列表**: 至少需要包含一个模型

---

## ModelFactory - 模型工厂

### 概述

`ModelFactory` 是一个工厂类，负责根据模型配置动态创建 AgentScope 模型实例。它支持多种 provider（OpenAI、Qwen），并封装了模型创建的复杂性。

### 位置

```
src/one_dragon_agent/core/model/model_factory.py
```

### 核心方法

#### `create_model(config: ModelConfigInternal, model_id: str)`

根据配置和模型 ID 创建模型实例。

**参数：**
- `config`: 模型配置对象（包含 API Key）
- `model_id`: 要使用的模型 ID（必须是 `config.models` 数组中的一个）

**返回：**
- AgentScope 模型实例（`OpenAIChatModel` 或 `QwenChatModel`）

**异常：**
- `ValueError`: 如果 provider 不支持、模型 ID 不在配置中、或配置无效

**示例：**
```python
from one_dragon_agent.core.model.model_factory import ModelFactory
from one_dragon_agent.core.model.service import ModelConfigService

# 获取配置
service = ModelConfigService(db_session)
config = await service.get_model_config_internal(1)

# 创建模型
model = ModelFactory.create_model(config, "gpt-4")
```

### 支持的 Provider

#### 1. OpenAI

- **配置要求**：
  - `provider`: `"openai"`
  - `base_url`: API 基础 URL（如 `https://api.openai.com/v1`）
  - `api_key`: API 密钥

- **创建的模型**: `OpenAIChatModel`

- **示例**：
```python
config = ModelConfigInternal(
    provider="openai",
    base_url="https://api.openai.com/v1",
    api_key="sk-...",
    models=[ModelInfo(model_id="gpt-4", ...)]
)

model = ModelFactory.create_model(config, "gpt-4")
# model: OpenAIChatModel
```

#### 2. Qwen

- **配置要求**：
  - `provider`: `"qwen"`
  - `base_url`: 空字符串（Qwen 使用 OAuth 认证，不需要）
  - `api_key`: 空字符串（Qwen 使用 OAuth 认证，不需要）

- **创建的模型**: `QwenChatModel`

- **示例**：
```python
config = ModelConfigInternal(
    provider="qwen",
    base_url="",
    api_key="",
    models=[ModelInfo(model_id="qwen-max", ...)]
)

model = ModelFactory.create_model(config, "qwen-max")
# model: QwenChatModel
```

### 验证逻辑

`ModelFactory.create_model()` 会执行以下验证：

1. **Provider 验证**: 检查 provider 是否为 `openai` 或 `qwen`
2. **模型 ID 验证**: 检查 `model_id` 是否在 `config.models` 数组中
3. **配置完整性**: 确保 API Key、Base URL 等必要字段存在

如果验证失败，会抛出 `ValueError` 并包含详细错误信息。

### 使用场景

#### 在 TushareSession 中使用

```python
class TushareSession(Session):
    async def _switch_model(self, model_config_id: int, model_id: str):
        # 从数据库获取配置
        config = await self._model_config_service.get_model_config_internal(model_config_id)

        # 使用 ModelFactory 创建模型
        model = ModelFactory.create_model(config, model_id)

        # 使用新模型创建 Agent
        self._current_agent = self._get_main_agent_with_model(model)
```

### 测试

运行 ModelFactory 单元测试：

```bash
uv run --env-file .env pytest tests/one_dragon_agent/core/model/model_factory/
```

测试覆盖：
- ✅ 创建 OpenAI 模型
- ✅ 创建 Qwen 模型
- ✅ 不支持的 provider 抛出异常
- ✅ 模型 ID 不在配置中抛出异常

---

## TushareSession - 模型切换机制

### 概述

`TushareSession` 实现了动态模型切换功能，允许在同一会话中使用不同的模型配置和模型 ID。系统会智能地复用或重建 Agent，避免不必要的性能开销。

### 核心方法

#### `chat(user_input, model_config_id, model_id, config)`

发送聊天消息，支持动态模型切换。

**参数：**
- `user_input`: 用户输入文本
- `model_config_id`: 模型配置 ID
- `model_id`: 模型 ID（必须在配置的 models 数组中）
- `config`: 模型配置对象（`ModelConfigInternal` 类型，由路由层验证后传入）

**返回：**
- 异步生成器，产生 `SessionMessage` 对象

**行为：**
1. 首次调用时创建 Agent
2. 相同配置和模型 ID 时复用 Agent
3. 不同配置或模型 ID 时重建 Agent
4. 切换模型时清空分析 Agent 缓存

### 模型切换逻辑

```python
async def chat(self, user_input: str, model_config_id: int, model_id: str, config=None):
    # 检查是否需要切换模型
    if (self._current_model_config_id != model_config_id or
        self._current_model_id != model_id):
        # 切换模型
        await self._switch_model(model_config_id, model_id, config)

    # 使用当前 Agent 处理请求
    async for message in self._current_agent(...):
        yield message
```

### Agent 管理策略

#### 1. Agent 复用

**条件：** `model_config_id` 和 `model_id` 都与上次相同

```python
# 相同配置 → 复用 Agent
if (self._current_model_config_id == model_config_id and
    self._current_model_id == model_id):
    # 使用现有 Agent
    return self._current_agent
```

**优势：**
- 避免重复创建 Agent 的开销
- 保持对话上下文连续性
- 提升响应速度

#### 2. Agent 重建

**条件：** `model_config_id` 或 `model_id` 任意一个不同

```python
# 不同配置 → 重建 Agent
model = ModelFactory.create_model(config, model_id)
self._current_agent = self._get_main_agent_with_model(model)
self._current_model_config_id = model_config_id
self._current_model_id = model_id
```

**影响：**
- 创建新的 Agent 实例
- 清空分析 Agent 缓存（`_analyse_by_code_map`）
- 重新初始化对话上下文

### 分析 Agent 管理

分析 Agent（用于 `analyse_by_code` 功能）使用与主 Agent 相同的模型：

```python
async def _get_analyse_by_code_agent(self, analyse_id: int):
    # 创建分析 Agent 时使用当前模型
    model = self._current_agent.model
    return self._get_analyse_by_code_agent_with_model(model)
```

**缓存机制：**
- 每个分析任务（`analyse_id`）对应一个分析 Agent
- 切换主模型时清空所有缓存的分析 Agent
- 确保分析 Agent 与主 Agent 使用相同模型

### 使用示例

#### 示例 1: 同一配置内切换模型

```python
# 第一次请求使用 gpt-4
async for msg in session.chat(
    user_input="分析贵州茅台",
    model_config_id=1,
    model_id="gpt-4"
):
    ...

# 第二次请求切换到 gpt-4-turbo（同一配置）
# Agent 会被重建，但使用相同的 API Key
async for msg in session.chat(
    user_input="继续分析",
    model_config_id=1,
    model_id="gpt-4-turbo"
):
    ...
```

#### 示例 2: 切换到不同配置

```python
# 使用配置 1 (OpenAI)
async for msg in session.chat(..., model_config_id=1, model_id="gpt-4"):
    ...

# 切换到配置 2 (Qwen)
# Agent 会被重建，使用不同的 API
async for msg in session.chat(..., model_config_id=2, model_id="qwen-max"):
    ...
```

#### 示例 3: 复用 Agent

```python
# 第一次请求
async for msg in session.chat(..., model_config_id=1, model_id="gpt-4"):
    ...
# Agent ID: 140123456789

# 第二次请求（相同配置和模型）
async for msg in session.chat(..., model_config_id=1, model_id="gpt-4"):
    ...
# Agent ID: 140123456789 (复用，相同对象)
```

### 性能考虑

1. **Agent 创建成本**：
   - 创建 Agent 需要初始化模型、内存、工具等
   - 首次创建约需 100-300ms
   - Agent 复用时无额外开销

2. **推荐做法**：
   - 相同对话中尽量使用相同模型
   - 需要切换时明确指定不同的 `model_id`
   - 避免在短时间内频繁切换模型

3. **缓存清理**：
   - 切换模型时自动清空分析 Agent 缓存
   - 释放不再使用的 Agent 资源
   - 防止内存泄漏

### 测试

运行 TushareSession 单元测试：

```bash
# 单元测试（使用 Mock）
uv run --env-file .env pytest tests/one_dragon_alpha/agent/tushare/tushare_session/test_unit.py

# E2E 测试（使用真实数据库和 API）
uv run --env-file .env pytest tests/one_dragon_alpha/agent/tushare/tushare_session/test_e2e.py
```

测试覆盖：
- ✅ 首次聊天请求创建 Agent
- ✅ 相同配置和模型复用 Agent
- ✅ 不同配置重建 Agent
- ✅ 不同模型 ID 重建 Agent
- ✅ 分析 Agent 使用相同模型
- ✅ 切换模型清空分析 Agent 缓存
4. **乐观锁**: 更新操作建议传入 `updated_at` 以防止并发冲突
