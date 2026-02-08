# 模型配置 API 使用文档

## 概述

模型配置管理 API 提供了完整的 CRUD 操作，支持创建、查询、更新、删除模型配置，以及测试 API 连接。

## 基础信息

- **Base URL**: `http://your-domain:21003`
- **API 前缀**: `/api/models/configs`
- **认证**: 当前版本不需要认证（生产环境建议添加）
- **Content-Type**: `application/json`

## API 端点

### 1. 创建配置

**请求**

```http
POST /api/models/configs
Content-Type: application/json

{
  "name": "DeepSeek 官方",
  "provider": "openai",
  "base_url": "https://api.deepseek.com",
  "api_key": "sk-xxxxx",
  "models": [
    {
      "model_id": "deepseek-chat",
      "support_vision": false,
      "support_thinking": true
    }
  ],
  "is_active": true
}
```

**响应** (201 Created)

```json
{
  "id": 1,
  "name": "DeepSeek 官方",
  "provider": "openai",
  "base_url": "https://api.deepseek.com",
  "models": [
    {
      "model_id": "deepseek-chat",
      "support_vision": false,
      "support_thinking": true
    }
  ],
  "is_active": true,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

**错误响应**

- `400`: 验证失败（名称重复、参数无效等）
- `422`: 请求格式错误

---

### 2. 获取配置列表

**请求**

```http
GET /api/models/configs?page=1&page_size=20&active=true&provider=openai
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | 否 | 页码，默认 1 |
| page_size | integer | 否 | 每页数量，默认 20，最大 100 |
| active | boolean | 否 | 是否启用（过滤条件） |
| provider | string | 否 | 提供商（过滤条件） |

**响应** (200 OK)

```json
{
  "total": 25,
  "page": 1,
  "page_size": 20,
  "items": [
    {
      "id": 1,
      "name": "DeepSeek 官方",
      "provider": "openai",
      "base_url": "https://api.deepseek.com",
      "models": [...],
      "is_active": true,
      "created_at": "2025-01-15T10:30:00",
      "updated_at": "2025-01-15T10:30:00"
    }
  ]
}
```

---

### 3. 获取单个配置

**请求**

```http
GET /api/models/configs/{id}
```

**响应** (200 OK)

```json
{
  "id": 1,
  "name": "DeepSeek 官方",
  "provider": "openai",
  "base_url": "https://api.deepseek.com",
  "models": [...],
  "is_active": true,
  "created_at": "2025-01-15T10:30:00",
  "updated_at": "2025-01-15T10:30:00"
}
```

**错误响应**

- `404`: 配置不存在

---

### 4. 更新配置

**请求**

```http
PUT /api/models/configs/{id}
Content-Type: application/json

{
  "name": "DeepSeek 官方（新）",
  "base_url": "https://api.deepseek.com",
  "api_key": "sk-new-key",
  "models": [...],
  "updated_at": "2025-01-15T10:30:00"
}
```

**说明**:
- `api_key` 可以留空，表示不修改
- `updated_at` 用于乐观锁验证

**响应** (200 OK)

```json
{
  "id": 1,
  "name": "DeepSeek 官方（新）",
  ...
}
```

**错误响应**

- `400`: 验证失败
- `404`: 配置不存在
- `409`: 乐观锁冲突（配置已被其他用户修改）

---

### 5. 删除配置

**请求**

```http
DELETE /api/models/configs/{id}
```

**响应** (204 No Content)

**错误响应**

- `404`: 配置不存在

---

### 6. 切换启用状态

**请求**

```http
PATCH /api/models/configs/{id}/status?is_active=false
```

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 是 | 是否启用 |

**响应** (200 OK)

```json
{
  "id": 1,
  "is_active": false,
  ...
}
```

---

### 7. 测试连接

**请求**

```http
POST /api/models/configs/test-connection
Content-Type: application/json

{
  "base_url": "https://api.deepseek.com",
  "api_key": "sk-xxxxx",
  "model_id": "deepseek-chat"
}
```

**响应** (200 OK)

成功:
```json
{
  "success": true,
  "message": "连接成功！模型回复: ..."
}
```

失败:
```json
{
  "success": false,
  "message": "API Key 无效或已过期",
  "raw_error": {
    "status_code": 401
  }
}
```

**说明**:
- 测试连接会发送一条 "hi" 消息，会消耗少量 token
- 超时时间为 15 秒
- 返回原始错误信息便于调试

---

## 错误码

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|----------|------|
| 200 | 成功 | 请求成功 |
| 201 | 创建成功 | 资源创建成功 |
| 204 | 无内容 | 删除成功 |
| 400 | 请求错误 | 参数验证失败、业务逻辑错误 |
| 404 | 未找到 | 资源不存在 |
| 409 | 冲突 | 乐观锁冲突 |
| 422 | 格式错误 | 请求格式不符合要求 |
| 500 | 服务器错误 | 服务器内部错误 |

## 数据模型

### ModelConfigCreate

```typescript
{
  name: string;              // 配置名称（唯一）
  provider: "openai";        // 提供商
  base_url: string;          // API 基础 URL
  api_key: string;           // API 密钥
  models: ModelInfo[];       // 模型列表
  is_active?: boolean;       // 是否启用（默认 true）
}
```

### ModelInfo

```typescript
{
  model_id: string;          // 模型 ID
  support_vision: boolean;   // 是否支持视觉
  support_thinking: boolean; // 是否支持思考
}
```

### TestConnectionRequest

```typescript
{
  base_url: string;          // API 基础 URL
  api_key: string;           // API 密钥
  model_id?: string;         // 模型 ID（默认 gpt-3.5-turbo）
}
```

## 使用示例

### cURL

```bash
# 创建配置
curl -X POST http://localhost:21003/api/models/configs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DeepSeek 官方",
    "provider": "openai",
    "base_url": "https://api.deepseek.com",
    "api_key": "sk-xxxxx",
    "models": [{"model_id": "deepseek-chat", "support_vision": false, "support_thinking": true}]
  }'

# 获取配置列表
curl http://localhost:21003/api/models/configs?page=1&page_size=20

# 测试连接
curl -X POST http://localhost:21003/api/models/configs/test-connection \
  -H "Content-Type: application/json" \
  -d '{
    "base_url": "https://api.deepseek.com",
    "api_key": "sk-xxxxx",
    "model_id": "deepseek-chat"
  }'
```

### Python (httpx)

```python
import httpx

async def create_config():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:21003/api/models/configs",
            json={
                "name": "DeepSeek 官方",
                "provider": "openai",
                "base_url": "https://api.deepseek.com",
                "api_key": "sk-xxxxx",
                "models": [{
                    "model_id": "deepseek-chat",
                    "support_vision": False,
                    "support_thinking": True
                }]
            }
        )
        return response.json()
```

### TypeScript

```typescript
import { modelApiService } from '@/services/modelApi'

// 创建配置
const config = await modelApiService.createModelConfig({
  name: 'DeepSeek 官方',
  provider: 'openai',
  base_url: 'https://api.deepseek.com',
  api_key: 'sk-xxxxx',
  models: [{
    model_id: 'deepseek-chat',
    support_vision: false,
    support_thinking: true
  }]
})

// 测试连接
const result = await modelApiService.testConnection({
  base_url: 'https://api.deepseek.com',
  api_key: 'sk-xxxxx',
  model_id: 'deepseek-chat'
})

console.log(result.success, result.message)
```

## 注意事项

1. **API Key 安全**: 响应中不包含 `api_key` 字段
2. **乐观锁**: 更新操作建议传入 `updated_at` 以防止并发冲突
3. **Provider 限制**: 当前仅支持 `openai` 兼容接口
4. **模型列表**: 至少需要包含一个模型
5. **连接测试**: 会消耗少量 token，请谨慎使用
