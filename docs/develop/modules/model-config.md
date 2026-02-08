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
2. **Provider 限制**: 当前仅支持 `openai` 兼容接口
3. **模型列表**: 至少需要包含一个模型
4. **乐观锁**: 更新操作建议传入 `updated_at` 以防止并发冲突
