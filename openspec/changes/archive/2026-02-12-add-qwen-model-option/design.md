# Qwen 模型配置功能设计文档

## Context

### 当前状态

- 后端已支持 `provider` 字段为 "openai" 或 "qwen"
- 前端模型配置界面的 Provider 选择器被禁用，仅支持 OpenAI
- Qwen OAuth token 当前存储在本地 JSON 文件（`~/.one_dragon_alpha/qwen_oauth_creds.json`）
- `QwenTokenManager` 使用单例模式管理全局 token

### 约束条件

- 保留现有 JSON 文件存储方式（向后兼容 CLI 工具）
- 系统使用 MySQL 存储方式（前端 API 创建的配置）
- Token 必须加密存储
- 遵循 OAuth 2.0 和 RFC 8628（设备码流程）标准

### 利益相关者

- 前端用户：需要通过 UI 创建和管理 Qwen 模型配置
- API 用户：需要通过 API 创建和管理 Qwen 模型配置
- 系统管理员：需要维护数据库迁移和安全性

## Goals / Non-Goals

**Goals:**
- 用户可以通过前端界面创建 Qwen 模型配置
- OAuth token 与模型配置关联，存储在数据库
- 支持多 Qwen 账号（每个配置独立 token）
- 保留 JSON 文件方式用于向后兼容

**Non-Goals:**
- 不支持从 CLI 工具创建的配置迁移到数据库
- 不修改现有的 `QwenTokenManager` 单例行为
- 不实现 OAuth token 的跨配置共享

## Decisions

### 1. 数据库表结构扩展

**决策**：在 `model_configs` 表添加 OAuth 相关字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `oauth_access_token` | TEXT (nullable) | 加密的访问令牌 |
| `oauth_token_type` | VARCHAR(50) (nullable) | 令牌类型（如 "Bearer"） |
| `oauth_refresh_token` | TEXT (nullable) | 加密的刷新令牌 |
| `oauth_expires_at` | BIGINT (nullable) | 过期时间戳（毫秒） |
| `oauth_scope` | VARCHAR(500) (nullable) | 授权范围 |
| `oauth_metadata` | JSON (nullable) | 额外元数据 |

**理由**：
- 遵循 OAuth 2.0 标准（RFC 6749）的字段命名
- 支持未来的 OAuth 提供商（不仅限于 Qwen）
- `oauth_metadata` JSON 字段提供灵活性

**替代方案考虑**：
- **独立 token 表**：被拒绝，增加了复杂度，且与现有 `api_key` 字段设计不一致
- **全局单条 token 记录**：被拒绝，不支持多账号场景

### 2. Token 加密方案

**决策**：使用 Fernet 对称加密（cryptography 库）

```python
from cryptography.fernet import Fernet

key = os.getenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key())
cipher = Fernet(key)
encrypted = cipher.encrypt(token.encode())
decrypted = cipher.decrypt(encrypted).decode()
```

**理由**：
- Fernet 提供完整的加密解决方案（加密 + 签名）
- 密钥管理简单（单一环境变量）
- Python 标准库 `cryptography` 提供

**替代方案考虑**：
- **数据库级别加密**：被拒绝，依赖数据库特定功能，降低可移植性
- **非对称加密**：被拒绝，过度设计，增加复杂度

### 3. 持久化方式设计

**决策**：实现 `MySQLTokenPersistence` 类，保留 `TokenPersistence`（JSON）类

```python
# 新建类
class MySQLTokenPersistence:
    async def save_token(self, config_id: int, token: QwenOAuthToken): ...
    async def load_token(self, config_id: int): ...

# 保留现有类
class TokenPersistence:  # JSON 文件方式
    async def save_token(self, token: QwenOAuthToken): ...
    async def load_token(self): ...
```

**理由**：
- 保留向后兼容性（CLI 工具继续使用 JSON）
- 前端 API 使用 MySQL 方式
- 清晰的职责分离

**使用场景**：
- **前端 API** → `MySQLTokenPersistence`（与配置关联）
- **CLI 工具** → `TokenPersistence`（全局单例）
- **模型调用** → 从数据库读取配置的 token

### 4. OAuth API 端点设计

**决策**：新增两个端点，使用内存会话存储

```
POST /api/qwen/oauth/device-code
  Request: {}
  Response: {
    "session_id": "uuid",
    "device_code": "...",
    "user_code": "ABCD-1234",
    "verification_uri": "...",
    "verification_uri_complete": "...",
    "expires_in": 900,
    "interval": 5
  }

GET /api/qwen/oauth/status?session_id=xxx
  Response: {
    "status": "pending" | "success" | "error",
    "token": {...},  // 仅 status=success 时
    "error": "..."    // 仅 status=error 时
  }
```

**会话存储**：使用 Python 字典 + `asyncio.Lock`（单机部署）

**理由**：
- 会话数据临时，无需持久化
- 简单高效，适合单机部署
- 会话超时后自动清理

**替代方案考虑**：
- **Redis 会话存储**：被拒绝，增加依赖，系统当前无 Redis
- **数据库会话存储**：被拒绝，过度设计，会话数据临时性

### 5. 前端表单动态验证

**决策**：使用 Vue 3 computed 属性动态调整验证规则

```typescript
const formRules = computed(() => {
  if (formData.provider === 'qwen') {
    return {
      name: [...],
      models: [...],
      // 不验证 base_url 和 api_key
    }
  } else {
    return {
      name: [...],
      base_url: [...],
      api_key: [...],
      models: [...],
    }
  }
})
```

**理由**：
- 响应式，Provider 切换时自动更新
- 清晰的验证逻辑分离
- 符合 Vue 3 最佳实践

### 6. Token 刷新策略

**决策**：在模型调用时检查并刷新 token

```python
# 在 ModelFactory._create_qwen_model 中
async def _create_qwen_model(...):
    config = await get_config_with_token(config_id)

    # 检查是否需要刷新
    if config.oauth_expires_at < now + 5min:
        await refresh_token(config_id)

    return QwenChatModel(token=config.oauth_access_token)
```

**理由**：
- 按需刷新，避免后台定时任务
- 5 分钟缓冲期确保不会过期
- 刷新失败时提示用户重新登录

**替代方案考虑**：
- **后台定时刷新**：被拒绝，增加复杂度，且可能有多个配置需要刷新

## Risks / Trade-offs

### 风险 1: Token 加密密钥管理

**风险**：`TOKEN_ENCRYPTION_KEY` 泄露可能导致所有 Qwen token 泄露

**缓解措施**：
- 使用环境变量存储密钥
- 提供密钥生成脚本
- 文档说明密钥管理最佳实践
- 如果未配置，使用默认密钥并记录警告

### 风险 2: OAuth 会话存储丢失

**风险**：服务重启导致进行中的 OAuth 会话丢失

**缓解措施**：
- 会话超时时间较短（15 分钟）
- 前端显示友好错误，提示用户重试
- 考虑未来升级到 Redis 会话存储（多实例部署时）

### 风险 3: 多个 Qwen 配置使用同一账号

**风险**：用户创建多个 Qwen 配置，但使用同一个 Qwen 账号授权

**影响**：Token 重复存储，浪费空间，但功能正常

**缓解措施**：
- 文档说明每个配置对应一个 Qwen 账号
- 未来可考虑添加"复用已有 token"功能

### Trade-off 1: JSON vs MySQL 持久化

**权衡**：保留两种方式增加了代码复杂度

**决策理由**：
- 向后兼容性优先（CLI 工具）
- 清晰的职责分离（API vs CLI）
- 代码维护成本可控（两个独立的类）

### Trade-off 2: Provider 类型扩展性

**权衡**：当前仅支持 OpenAI 和 Qwen，未来可能需要支持其他提供商

**设计考虑**：
- `provider` 字段使用字符串，易于扩展
- `oauth_*` 字段通用，支持任何 OAuth 2.0 提供商
- `oauth_metadata` JSON 字段提供灵活性

## Migration Plan

### 部署步骤

1. **数据库迁移**
   ```sql
   ALTER TABLE model_configs ADD COLUMN oauth_access_token TEXT DEFAULT NULL;
   ALTER TABLE model_configs ADD COLUMN oauth_token_type VARCHAR(50) DEFAULT NULL;
   ALTER TABLE model_configs ADD COLUMN oauth_refresh_token TEXT DEFAULT NULL;
   ALTER TABLE model_configs ADD COLUMN oauth_expires_at BIGINT DEFAULT NULL;
   ALTER TABLE model_configs ADD COLUMN oauth_scope VARCHAR(500) DEFAULT NULL;
   ALTER TABLE model_configs ADD COLUMN oauth_metadata JSON DEFAULT NULL;
   CREATE INDEX idx_oauth_expires_at ON model_configs(oauth_expires_at);
   ```

2. **后端部署**
   - 部署新代码
   - 配置 `TOKEN_ENCRYPTION_KEY` 环境变量

3. **前端部署**
   - 部署新代码

### 回滚策略

- 数据库字段为 nullable，不影响现有 OpenAI 配置
- 前端 Provider 选择器可重新禁用
- 后端 API 可通过路由禁用

### 验证步骤

1. 创建 OpenAI 配置（确保不影响现有功能）
2. 创建 Qwen 配置（完成 OAuth 流程）
3. 使用 Qwen 模型进行对话
4. 验证 token 自动刷新

## Open Questions

### Q1: 是否需要支持从 JSON 迁移到 MySQL？

**状态**：已决定 - 不支持

**理由**：
- JSON 和 MySQL 的使用场景不同（CLI vs API）
- 用户可以通过 API 重新创建配置
- 简化实现复杂度

### Q2: OAuth 会话是否需要持久化？

**状态**：已决定 - 不持久化（内存存储）

**理由**：
- 会话临时性（15 分钟超时）
- 单机部署场景
- 未来多实例部署时再考虑 Redis

### Q3: Token 刷新是否需要后台任务？

**状态**：已决定 - 按需刷新（模型调用时）

**理由**：
- 避免后台任务复杂度
- Qwen token 有效期较长（通常 24 小时+）
- 按需刷新足够及时
