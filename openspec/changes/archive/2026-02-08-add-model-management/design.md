# OpenAI 模型管理系统设计文档

## Context

### 背景
当前系统需要支持多种大语言模型（LLM）的接入和管理。为了支持 OpenAI 兼容的 API（如 DeepSeek、Moonshot、OpenAI 官方等），需要一个可配置的模型管理模块。用户希望能够灵活添加和管理不同的模型提供商及其模型列表，而无需修改代码。

### 当前状态
- 系统已有基础的模型集成能力（如 Qwen 模型）
- 已有 MySQL 数据库连接服务
- 前端使用 Vue3 + Element-Plus
- 后端使用 FastAPI + uvicorn
- 缺少统一的模型配置管理模块

### 约束条件
- 必须使用 UTF-8 编码和中文文档
- 所有 Python 代码必须遵循异步优先原则
- API key 等敏感信息需妥善保护（明文存储但仅内网访问、接口不返回、前端脱敏）
- 需要保持与现有 AgentScope 架构的兼容性
- 数据库操作需使用现有的 MySQL 连接服务

### 利益相关者
- 系统用户：需要通过界面管理模型配置
- 开发者：需要维护和扩展模型管理功能
- 管理员：需要确保 API key 等敏感信息的安全性

## Goals / Non-Goals

### Goals
1. **提供统一的模型配置管理能力**：支持多个 OpenAI 兼容的 API 提供商配置
2. **数据持久化**：所有配置信息安全存储在 MySQL 数据库中
3. **敏感信息保护**：API key 明文存储但数据库不对外暴露，前端不可查看，GET 接口不返回
4. **用户友好的管理界面**：提供直观的前端界面进行配置的增删改查
5. **灵活的模型能力标识**：支持标识模型是否支持视觉、思考等能力
6. **配置激活状态管理**：支持启用/禁用配置，便于管理

### Non-Goals
1. **不包含模型调用逻辑**：本设计仅关注配置管理，不涉及实际的模型调用
2. **不包含权限系统**：暂时不实现细粒度的用户权限控制（可在后续版本添加）
3. **不支持配置导入/导出**：暂不提供批量导入或导出配置的功能，也不提供应用层备份恢复机制
4. **不包含配置版本管理**：不追踪配置的修改历史
5. **不支持配置自动验证**：不自动验证 API key 的有效性，但提供手动测试连接功能

## Decisions

### 1. 数据模型设计

**决策**：使用嵌套的 JSON 结构存储模型列表

**理由**：
- 一个配置下可包含多个模型，每个模型有不同的能力标识
- 将模型列表作为 JSON 数组存储在一个字段中，避免了创建额外的关联表
- 简化了查询逻辑，一次查询即可获取完整的配置信息
- JSON 字段在 MySQL 5.7+ 中有良好地支持，可以进行 JSON 路径查询
- 通用的表设计可以支持多种模型类型（OpenAI、Qwen、未来扩展的其他模型）

**数据表结构**：
```sql
CREATE TABLE model_configs (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL COMMENT '配置名称（用户自定义）',
    provider VARCHAR(50) NOT NULL COMMENT '模型提供商（openai/qwen/deepseek等）',
    base_url TEXT NOT NULL COMMENT 'API baseUrl',
    api_key TEXT NOT NULL COMMENT 'API密钥（明文存储，数据库不对外暴露）',
    models JSON NOT NULL COMMENT '模型列表（JSON数组）',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否启用',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_provider (provider),
    INDEX idx_is_active (is_active)
) COMMENT='通用模型配置表';
```

**models 字段结构**：
```json
[
    {
        "model_id": "deepseek-chat",
        "support_vision": true,
        "support_thinking": false
    },
    {
        "model_id": "deepseek-coder",
        "support_vision": false,
        "support_thinking": true
    }
]
```

**provider 字段说明**：
- 当前仅支持 `openai`：OpenAI 官方及兼容的 API（如 DeepSeek、Moonshot、通义千问等）
- 未来可扩展其他提供商（如 `qwen`、`zhipu`、`baichuan` 等）
- 在验证层，provider 字段暂时只接受 `openai` 值

**替代方案**：为每个模型创建独立的表，通过外键关联到配置表
**不采用原因**：增加了查询复杂度，需要多次 JOIN 操作，对于本场景过度设计

### 2. 敏感信息保护方案

**决策**：API key 明文存储在数据库中，但前端不可查看

**理由**：
- 简化实现，避免加密/解密的复杂性
- 数据库不对外暴露，通过内网访问，安全性可控
- API key 仅在创建和更新时输入，不提供查看功能
- 降低密钥管理的复杂度

**实施细节**：
- **存储**：API key 以明文形式存储在 `api_key` 字段中
- **前端限制**：
  - 列表页不显示 API key
  - 创建/编辑对话框中，API key 字段为密码输入框
  - 编辑时，API key 字段显示为空，提示"留空则不修改"
  - 不提供"查看已有 API key"的功能
- **后端接口**：
  - GET 接口返回的配置对象中，不包含 `api_key` 字段
  - 仅在创建（POST）和更新（PUT）时接收 API key
  - 内部调用时直接使用数据库中的 API key
- **安全措施**：
  - 数据库仅允许内网访问
  - 定期备份数据库
  - 文档中明确说明数据库安全配置要求

**替代方案**：使用 Fernet 对称加密
**不采用原因**：用户选择简化方案，接受明文存储，通过数据库安全措施保障安全性

### 3. 后端架构设计

**决策**：采用三层架构（Router → Service → Repository）

**理由**：
- **Router 层**（FastAPI 路由）：处理 HTTP 请求、参数验证、响应格式化
- **Service 层**（业务逻辑）：处理业务规则、数据验证、调用 Repository
- **Repository 层**（数据访问）：封装数据库操作，提供 CRUD 接口
- 清晰的职责分离，便于测试和维护
- 符合 FastAPI 最佳实践

**模块结构**：
```
src/one_dragon_agent/core/model/
├── __init__.py
├── models.py          # Pydantic 数据模型（通用）
├── repository.py      # 数据库操作（通用）
├── service.py         # 业务逻辑（通用）
└── router.py          # FastAPI 路由（通用）
```

**替代方案**：将所有逻辑放在 Router 层
**不采用原因**：代码耦合度高，难以复用和测试

### 4. API 设计

**决策**：使用 RESTful 风格的 API 设计

**理由**：
- 直观且符合 HTTP 语义
- 易于前端理解和调用
- 与现有 FastAPI 生态一致

**API 端点**：
- `POST /api/models/configs` - 创建配置
- `GET /api/models/configs` - 获取配置列表（支持分页和过滤参数）
  - 分页参数：`?page=1&page_size=10`
  - 过滤参数：`?is_active=true&provider=openai`
  - 默认按创建时间倒序排列（最新在前）
- `GET /api/models/configs/{id}` - 获取单个配置
- `PUT /api/models/configs/{id}` - 更新配置
- `DELETE /api/models/configs/{id}` - 删除配置
- `PATCH /api/models/configs/{id}/status` - 切换启用状态
- `POST /api/models/configs/test-connection` - 测试 API 连接

**响应格式**：
- 成功响应：返回完整的配置对象（不包含 API key）
- 列表响应：包含分页信息 `{ "total": 100, "page": 1, "page_size": 10, "items": [...] }`
- 错误响应：统一格式 `{ "code": "ERROR_CODE", "message": "错误描述", "details": {} }`

**分页行为**：
- 默认 `page=1`，`page_size=20`
- `page_size` 最大值为 100，超出时自动限制为 100
- 返回 `total` 字段表示总记录数，便于前端计算总页数

### 5. 前端架构设计

**决策**：使用 Vue3 Composition API + Element-Plus 组件

**理由**：
- 项目已采用 Vue3 + Element-Plus 技术栈
- Composition API 提供更好的逻辑复用和类型推导
- Element-Plus 提供丰富的表格、表单、对话框组件

**页面结构**：
```
frontend/src/views/model-management/
├── ModelConfigList.vue    # 配置列表页面（路由: /model-management）
└── components/
    ├── ModelConfigDialog.vue    # 创建/编辑对话框
    └── ModelCard.vue            # 模型卡片组件
```

**状态管理**：使用 Pinia 进行全局状态管理（如果已使用），否则使用本地状态

**API 调用**：封装在 `frontend/src/api/model.js` 中

**菜单名称**：在导航菜单中显示为"模型配置"

### 6. 数据库连接管理

**决策**：复用现有的 MySQL 连接服务

**理由**：
- 避免重复创建数据库连接池
- 保持系统架构一致性
- 减少资源消耗

**实施**：
- 使用现有的 MySQL 连接配置（从环境变量或配置文件读取）
- Repository 层通过依赖注入获取数据库连接
- 所有数据库操作使用异步方式（`async/await`）

### 7. 测试连接功能设计

**决策**：提供手动测试 API 连接的功能

**理由**：
- 用户在保存配置前验证 API key 和 baseUrl 的有效性
- 避免保存错误配置导致后续调用失败
- 提供友好的错误提示，帮助用户排查问题
- 不自动验证，由用户主动触发测试

**实施细节**：
- **API 端点**：`POST /api/models/configs/test-connection`
- **请求体**：
  ```json
  {
    "base_url": "https://api.deepseek.com",
    "api_key": "sk-xxx"
  }
  ```
- **测试方法**：发送 `GET /models` 请求到目标服务
  - OpenAI API 的 `/models` 端点需要认证，API key 无效时会返回 401 Unauthorized
  - 设置超时时间（如 10 秒）
  - 通常不消耗 API 配额（GET 请求，仅获取模型列表）
- **响应**：
  - 成功：`{ "success": true, "message": "连接成功" }`
  - 失败：`{ "success": false, "message": "服务商返回的错误信息", "raw_error": { ... } }`
    - 直接返回服务商的原始错误信息，不做加工处理
    - 前端直接显示 `message` 字段给用户
- **前端实现**：
  - 在创建/编辑对话框中添加"测试连接"按钮
  - 点击后发送请求到后端 API
  - 显示加载状态和测试结果（成功/失败提示）
  - 失败时直接显示服务商返回的错误信息

**替代方案**：在保存配置时自动验证
**不采用原因**：会增加保存操作的耗时，且某些 API 可能不支持快速验证

### 8. 事务处理策略

**决策**：在写操作（创建、更新、删除）中使用数据库事务

**理由**：
- 确保数据一致性
- 操作失败时能够回滚，避免数据损坏
- 特别是对于创建配置（涉及加密、多字段插入）和更新配置（可能部分字段成功）

**实施**：
- 使用 SQLAlchemy 或 aiomysql 的事务机制
- 异常时自动回滚
- 记录事务日志用于故障排查

## Risks / Trade-offs

### Risk 1: API key 泄露
**风险**：如果数据库被非法访问，所有 API key 将以明文形式泄露

**缓解措施**：
- 数据库仅允许内网访问，配置防火墙规则
- 使用强密码保护数据库访问
- 定期备份数据库，备份文件加密存储
- 数据库连接使用 SSL/TLS 加密
- 限制数据库用户权限，仅允许必要的操作
- 在文档中明确说明数据库安全配置要求

### Risk 2: 数据库连接池耗尽
**风险**：大量并发请求可能导致数据库连接池耗尽

**缓解措施**：
- 合理配置连接池大小（建议 10-20 个连接）
- 使用连接超时和回收机制
- 监控数据库连接数，及时预警
- 对于只读查询，可以考虑使用缓存

### Risk 3: API key 验证缺失
**风险**：系统不验证用户输入的 API key 是否有效，可能导致配置错误

**缓解措施**：
- 在前端提供"测试连接"按钮，发送简单的测试请求到 API
- 在文档中明确说明如何验证 API key 的有效性
- 记录 API 调用失败日志，便于用户排查问题
- 未来版本可添加异步的 API key 验证任务

### Trade-off 1: 查询性能 vs 数据一致性
**权衡**：使用 JSON 字段存储模型列表简化了数据模型，但查询特定能力的模型需要扫描 JSON

**决策**：接受查询性能的轻微损失，优先考虑代码简洁性

**理由**：
- 模型配置的数量不会很大（通常 < 100 个）
- 查询特定能力的模型可以在应用层过滤
- 未来可以通过在模型字段上添加生成列或索引来优化

### Trade-off 2: 物理删除 vs 软删除
**权衡**：物理删除配置无法恢复，软删除会增加查询复杂度

**决策**：使用物理删除

**理由**：
- 配置数据不涉及审计或合规要求
- 用户可以通过备份恢复数据
- 软删除需要额外的字段和过滤逻辑
- 在文档中提醒用户删除前确认

### Risk 4: 前端并发更新冲突
**风险**：多个用户同时编辑同一配置可能导致数据覆盖

**缓解措施**：
- 使用 `updated_at` 字段进行乐观锁
- 更新前检查 `updated_at`，如果已被修改则返回冲突错误
- 前端显示"该配置已被其他用户修改，请刷新"提示
- 考虑在编辑时锁定配置（可选）

## Migration Plan

### 阶段 1: 后端开发（预计 2-3 天）
1. **数据模型定义**（1 天）
   - 创建 Pydantic 模型（schemas）
   - 定义 API 请求/响应模型
   - 定义分页响应模型
   - 编写单元测试

2. **数据库层开发**（0.5 天）
   - 实现 Repository 类
   - 实现分页查询逻辑
   - 编写数据库迁移脚本
   - 测试数据库操作

3. **服务层开发**（0.5 天）
   - 实现 Service 类的业务逻辑
   - 添加配置验证规则（仅支持 provider=openai）
   - 测试业务逻辑

4. **测试连接功能开发**（0.5 天）
   - 实现测试连接的 Service 方法
   - 调用目标 API 验证连通性
   - 添加错误处理和错误码映射
   - 编写单元测试

5. **API 路由开发**（0.5 天）
   - 实现 FastAPI 路由（包含测试连接接口）
   - 实现分页参数处理
   - 添加错误处理中间件
   - 编写 API 集成测试

### 阶段 2: 前端开发（预计 2-3 天）
1. **API 封装**（0.5 天）
   - 创建 `api/model.js`
   - 封装所有 API 调用方法（包含分页参数处理）
   - 封装测试连接方法
   - 添加错误处理

2. **页面开发**（2 天）
   - 实现配置列表页面（路由：/model-management）
   - 实现分页组件
   - 实现创建/编辑对话框
   - 实现测试连接按钮和结果提示
   - 实现删除确认机制
   - 添加加载状态和错误提示

3. **样式和交互优化**（0.5 天）
   - 响应式布局调整
   - 动画和过渡效果
   - 用户体验优化

### 阶段 3: 集成测试（预计 1 天）
1. **端到端测试**
   - 测试完整的用户流程
   - 测试错误场景
   - 测试并发操作

2. **性能测试**
   - 测试大量配置的加载性能
   - 测试并发请求的处理能力

### 阶段 4: 部署（预计 0.5 天）
1. **数据库迁移**
   - 在测试环境执行迁移脚本
   - 验证表结构正确性

2. **环境配置**
   - 配置数据库内网访问权限
   - 更新部署文档，说明数据库安全要求

3. **上线**
   - 部署后端代码
   - 部署前端代码
   - 验证功能正常

### 回滚策略
- **数据库回滚**：提供回滚 SQL 脚本，删除新创建的表
- **代码回滚**：保留旧版本代码，使用 Git 快速回退
- **前端回滚**：前端版本独立，可单独回退

## Open Questions

### 已决策的问题（已记录在设计中）

1. **✅ API 路由设计**：使用 `/api/models/configs`
2. **✅ provider 字段**：当前仅支持 `openai`
3. **✅ 测试连接功能**：使用 `GET /models` 端点验证，直接返回服务商错误信息
4. **✅ 分页功能**：需要实现，默认每页 20 条
5. **✅ 前端菜单名称**：显示为"模型配置"
6. **✅ 前端路由路径**：使用 `/model-management`
7. **✅ 分页排序**：按创建时间倒序（最新在前）
8. **✅ 备份恢复机制**：暂不需要，使用 MySQL 标准备份

### 暂未解决的问题

无 - 所有关键决策已完成。
