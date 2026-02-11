# 模型配置增加 Qwen 选项

## Why

当前系统后端已经支持 Qwen 模型提供商，但前端的模型配置界面中 Provider 选择器被禁用，仅支持 OpenAI 兼容接口。用户无法通过前端界面创建 Qwen 模型配置，只能通过 API 直接操作。这降低了系统的易用性。

## What Changes

- **前端模型配置界面**: 启用 Provider 选择器，添加 Qwen 选项
- **动态表单字段**: 根据 Provider 类型显示不同的配置字段
  - OpenAI: 显示 Base URL、API Key、测试连接按钮
  - Qwen: 显示 OAuth 登录按钮（替代 Base URL 和 API Key）
- **Qwen OAuth 认证流程**:
  - 点击登录按钮后，调用后端 API 获取设备码和用户码
  - 显示用户码和验证链接，引导用户在浏览器中完成认证
  - 轮询检查认证状态，认证成功后显示"已认证"状态
  - Token 存储到数据库（与模型配置关联，加密存储）
  - 保留现有 JSON 文件存储方式（向后兼容），但系统中只使用 MySQL 方式
- **后端 OAuth API**: 新增 OAuth 相关 API 端点（设备码获取、轮询状态）
- **用户体验优化**: 根据 Provider 类型显示相应的提示信息

## Capabilities

### New Capabilities
- `qwen-model-config-ui`: 前端 Qwen 模型配置界面能力
- `qwen-oauth-api`: Qwen OAuth 认证 API（设备码获取、状态轮询）

### Modified Capabilities
- `openai-model-config`: 修改现有模型配置能力，增加对多 Provider 的支持

## Impact

### 受影响的代码
- **前端**:
  - `frontend/src/views/model-management/components/ModelConfigDialog.vue`
    - 启用 Provider 选择器
    - 添加动态表单逻辑（根据 Provider 显示不同字段）
    - Qwen: 显示登录按钮、用户码展示、认证状态轮询
    - OpenAI: 显示 Base URL、API Key、测试连接按钮

- **后端** (新增 OAuth API):
  - `src/one_dragon_agent/api/routes/qwen_oauth.py` (新建)
    - `POST /api/qwen/oauth/device-code`: 获取设备码和用户码
    - `GET /api/qwen/oauth/status`: 轮询认证状态
  - `src/one_dragon_agent/core/model/qwen/mysql_token_persistence.py` (新建)
    - 实现 MySQL token 持久化
  - 保留 `TokenPersistence`（JSON 方式）向后兼容
  - 系统使用 `MySQLTokenPersistence` 替代 `TokenPersistence`

- **数据库** (扩展 model_configs 表):
  - `oauth_access_token`: TEXT (nullable) - 访问令牌（加密）
  - `oauth_token_type`: VARCHAR(50) (nullable) - 令牌类型（如 "Bearer"）
  - `oauth_refresh_token`: TEXT (nullable) - 刷新令牌（加密）
  - `oauth_expires_at`: BIGINT (nullable) - 过期时间戳（毫秒）
  - `oauth_scope`: VARCHAR(500) (nullable) - 授权范围
  - `oauth_metadata`: JSON (nullable) - 提供商特定额外数据

### 用户体验
- 用户可以在前端界面直接创建 Qwen 模型配置
- Qwen 配置创建流程更简化（无需填写 base_url 和 api_key）
