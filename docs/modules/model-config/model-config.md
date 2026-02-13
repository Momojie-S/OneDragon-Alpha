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

## 数据模型设计

### ModelConfigCreate

创建模型配置时的数据结构：
- `name`: 配置名称（唯一）
- `provider`: 提供商（支持 "openai"）
- `base_url`: API 基础 URL
- `api_key`: API 密钥
- `models`: 模型列表
- `is_active`: 是否启用（默认 true）

### ModelInfo

单个模型的信息：
- `model_id`: 模型 ID
- `support_vision`: 是否支持视觉
- `support_thinking`: 是否支持思考

## 前端集成

前端通过模型配置管理服务调用后端 API。

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

## 注意事项

1. **API Key 安全**: 响应中不包含 `api_key` 字段
2. **Provider 支持**: 支持 `openai` 和 `qwen` 两种 provider
3. **模型列表**: 至少需要包含一个模型

---

## ModelFactory - 模型工厂

### 概述

`ModelFactory` 是一个工厂类，负责根据模型配置动态创建 AgentScope 模型实例。它支持多种 provider（OpenAI、Qwen），并封装了模型创建的复杂性。

### 位置

`src/one_dragon_agent/core/model/model_factory.py`

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

### 支持的 Provider

#### 1. OpenAI

- **配置要求**：
  - `provider`: `"openai"`
  - `base_url`: API 基础 URL（如 `https://api.openai.com/v1`）
  - `api_key`: API 密钥
  - 创建的模型: `OpenAIChatModel`

#### 2. Qwen

- **配置要求**：
  - `provider`: `"qwen"`
  - `base_url`: 空字符串（Qwen 使用 OAuth 认证，不需要）
  - `api_key`: 空字符串（Qwen 使用 OAuth 认证，不需要）
  - 创建的模型: `QwenChatModel`

### 验证逻辑

`ModelFactory.create_model()` 会执行以下验证：

1. **Provider 验证**: 检查 provider 是否为 `openai` 或 `qwen`
2. **模型 ID 验证**: 检查 `model_id` 是否在 `config.models` 数组中
3. **配置完整性**: 确保 API Key、Base URL 等必要字段存在

如果验证失败，会抛出 `ValueError` 并包含详细错误信息。

---

## ChatSession - 模型切换机制

### 概述

`ChatSession` 实现了动态模型切换功能，允许在同一会话中使用不同的模型配置和模型 ID。系统会智能地复用或重建 Agent，避免不必要的性能开销。

### 核心方法

#### `chat(user_input, model_config_id, model_id, config=None)`

发送聊天消息，支持动态模型切换。

**参数：**
- `user_input`: 用户输入文本
- `model_config_id`: 模型配置 ID
- `model_id`: 模型 ID（必须在配置的 models 数组中）
- `config`: 可选，模型配置对象（如果提供则跳过数据库查询）

**返回：**
- 异步生成器，产生 `SessionMessage` 对象

**行为：**
1. 首次调用时创建 Agent
2. 相同配置和模型 ID 时复用 Agent
3. 不同配置或模型 ID 时重建 Agent
4. 切换模型时清空分析 Agent 缓存

### 模型切换逻辑

系统通过比较当前配置和请求的配置来决定是否切换模型：
- 相同配置 → 复用 Agent
- 不同配置 → 重建 Agent

#### Agent 复用

**条件：** `model_config_id` 和 `model_id` 都与上次相同

**优势：**
- 避免重复创建 Agent 的开销
- 保持对话上下文连续性
- 提升响应速度

#### Agent 重建

**条件：** `model_config_id` 或 `model_id` 任意一个不同

**影响：**
- 创建新的 Agent 实例
- 清空分析 Agent 缓存（`_analyse_by_code_map`）
- 重新初始化对话上下文

### 分析 Agent 管理

分析 Agent（用于 `analyse_by_code` 功能）使用与主 Agent 相同的模型。

**缓存机制：**
- 每个分析任务（`analyse_id`）对应一个分析 Agent
- 切换主模型时清空所有缓存的分析 Agent
- 确保分析 Agent 与主 Agent 使用相同模型

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
