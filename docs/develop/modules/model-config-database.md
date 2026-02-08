# 模型配置数据库表设计

## 表名

`model_configs`

## 表结构

| 字段名 | 类型 | 约束 | 默认值 | 说明 |
|--------|------|------|--------|------|
| id | INT | PRIMARY KEY, AUTO_INCREMENT | - | 主键 ID |
| name | VARCHAR(255) | NOT NULL, UNIQUE | - | 配置名称（全局唯一） |
| provider | VARCHAR(50) | NOT NULL | - | 提供商（当前仅支持 "openai"） |
| base_url | TEXT | NOT NULL | - | API 基础 URL |
| api_key | TEXT | NOT NULL | - | API 密钥（加密存储） |
| models | JSON | NOT NULL | - | 模型列表 |
| is_active | BOOLEAN | NOT NULL | TRUE | 是否启用 |
| created_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP | 创建时间 |
| updated_at | DATETIME | NOT NULL | CURRENT_TIMESTAMP ON UPDATE | 更新时间（用于乐观锁） |

## 索引

| 索引名 | 字段 | 类型 | 说明 |
|--------|------|------|------|
| PRIMARY | id | PRIMARY KEY | 主键索引 |
| idx_name | name | UNIQUE | 配置名称唯一索引 |
| idx_provider | provider | INDEX | 提供商索引（用于过滤查询） |
| idx_is_active | is_active | INDEX | 启用状态索引（用于过滤查询） |
| idx_created_at | created_at | INDEX | 创建时间索引（用于排序） |

## 字段说明

### name

- **类型**: VARCHAR(255)
- **约束**: NOT NULL, UNIQUE
- **说明**: 配置名称，必须全局唯一
- **验证规则**:
  - 长度: 1-255 字符
  - 不能为空字符串
  - 自动去除首尾空格

### provider

- **类型**: VARCHAR(50)
- **约束**: NOT NULL
- **说明**: 模型提供商标识
- **当前支持的值**: `openai`
- **未来扩展**: 可能支持 `anthropic`, `google`, `deepseek` 等

### base_url

- **类型**: TEXT
- **约束**: NOT NULL
- **说明**: API 基础 URL
- **格式要求**: 必须以 `http://` 或 `https://` 开头
- **示例**:
  - `https://api.openai.com`
  - `https://api.deepseek.com`
  - `https://api-inference.modelscope.cn`

### api_key

- **类型**: TEXT
- **约束**: NOT NULL
- **说明**: API 密钥
- **安全性**:
  - 不会在响应中返回给前端
  - 建议在生产环境中使用加密存储
- **更新策略**: 编辑时可以留空，表示不修改

### models

- **类型**: JSON
- **约束**: NOT NULL
- **说明**: 模型列表数组
- **JSON 结构**:
  ```json
  [
    {
      "model_id": "gpt-4",
      "support_vision": true,
      "support_thinking": false
    },
    {
      "model_id": "gpt-3.5-turbo",
      "support_vision": false,
      "support_thinking": false
    }
  ]
  ```
- **验证规则**: 至少包含一个模型

### is_active

- **类型**: BOOLEAN
- **约束**: NOT NULL
- **默认值**: TRUE
- **说明**: 配置启用状态
- **用途**: 控制配置是否可用，禁用后不会被查询使用

### created_at

- **类型**: DATETIME
- **约束**: NOT NULL
- **默认值**: CURRENT_TIMESTAMP
- **说明**: 记录创建时间

### updated_at

- **类型**: DATETIME
- **约束**: NOT NULL
- **默认值**: CURRENT_TIMESTAMP ON UPDATE
- **说明**: 记录更新时间
- **用途**: 实现乐观锁，防止并发修改冲突

## 乐观锁机制

更新配置时使用 `updated_at` 字段实现乐观锁：

1. **读取**: 客户端读取配置时获取 `updated_at` 时间戳
2. **更新**: 客户端更新时发送该时间戳
3. **验证**: 服务端比较时间戳，如果与数据库不一致则拒绝更新
4. **错误**: 返回 HTTP 409 Conflict 状态码

```sql
-- 更新时检查 updated_at
UPDATE model_configs
SET name = ?, base_url = ?, updated_at = CURRENT_TIMESTAMP
WHERE id = ? AND updated_at = ?

-- 检查 affected_rows
-- 如果为 0，说明记录已被其他用户修改
```

## 数据迁移

### 创建表

```sql
CREATE TABLE model_configs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    provider VARCHAR(50) NOT NULL,
    base_url TEXT NOT NULL,
    api_key TEXT NOT NULL,
    models JSON NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_provider (provider),
    INDEX idx_is_active (is_active),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

### 回滚脚本

```sql
-- 谨慎使用！会删除所有数据
DROP TABLE IF EXISTS model_configs;
```

## 查询示例

### 基础查询

```sql
-- 查询所有启用的配置
SELECT * FROM model_configs WHERE is_active = TRUE;

-- 查询特定 provider 的配置
SELECT * FROM model_configs WHERE provider = 'openai';

-- 分页查询
SELECT * FROM model_configs
ORDER BY created_at DESC
LIMIT 20 OFFSET 0;
```

### 统计查询

```sql
-- 统计各 provider 的配置数量
SELECT provider, COUNT(*) as count
FROM model_configs
GROUP BY provider;

-- 统计启用/禁用配置数量
SELECT is_active, COUNT(*) as count
FROM model_configs
GROUP BY is_active;
```

## 性能优化

### 索引策略

- `idx_name`: 支持按名称快速查找和唯一性检查
- `idx_provider`: 支持按 provider 过滤查询
- `idx_is_active`: 支持按启用状态过滤查询
- `idx_created_at`: 支持按创建时间排序

### 查询优化建议

1. **使用索引过滤**: 尽量使用 `provider`、`is_active` 等索引字段作为查询条件
2. **避免 SELECT ***: 仅查询需要的字段，减少数据传输
3. **使用 LIMIT**: 分页查询时使用 LIMIT 限制返回行数
4. **JSON 字段查询**: MySQL 5.7+ 支持 JSON 字段索引，可根据需要添加

### 数据量建议

- **配置数量**: 建议不超过 1000 个配置
- **模型列表**: 每个配置建议不超过 50 个模型
- **分页大小**: 前端建议使用 20-100 的分页大小

## 安全建议

1. **API Key 加密**: 生产环境中建议对 `api_key` 字段使用 AES 加密
2. **访问控制**: 数据库用户权限最小化，仅允许必要的 CRUD 操作
3. **备份策略**: 定期备份配置数据
4. **审计日志**: 记录配置变更日志（可选）
