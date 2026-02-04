# Proposal: Qwen 模型集成到 AgentScope

## Why

当前项目使用 AgentScope 框架构建，通过 `OpenAIChatModel` 接入大模型。Qwen 提供了 OpenAI 兼容的 API 接口，但需要使用 OAuth 2.0 设备码流程进行认证。现有的 `OpenAIChatModel` 需要手动管理 API key，无法自动处理 OAuth 认证和 token 刷新。为了方便地在 AgentScope 中使用 Qwen 模型，需要封装一个专门的 `QwenChatModel` 类，自动处理认证流程。

## What Changes

- 新增 `one_dragon_agent` 包，用于存放底层公共能力（如从 AgentScope 拓展的内容）
- 新增 `QwenChatModel` 类，**继承 AgentScope 的 `OpenAIChatModel`**，使用 OAuth token 作为 API key
- 新增 `QwenOAuthClient` 类，处理 OAuth 2.0 设备码流程（设备码获取、用户授权轮询、token 获取）和 refresh_token 刷新
- 新增 `QwenTokenManager` 类，管理 access token 的持久化存储和后台定时自动刷新
- 新增单元测试，覆盖 OAuth 认证、token 管理和模型调用流程
- 更新文档，说明如何在 AgentScope 中使用 Qwen 模型

## Capabilities

### New Capabilities
- `qwen-oauth-client`: Qwen OAuth 2.0 设备码认证流程，包括设备码获取、用户授权轮询、token 获取和刷新
- `qwen-chat-model`: 封装 Qwen 模型类，**继承 `OpenAIChatModel`**，使用 OAuth token 作为 API key
- `token-persistence`: Token 持久化存储（文件系统），避免重复认证
- `token-auto-refresh`: TokenManager 后台定时自动刷新 token，确保模型调用不受影响

### Modified Capabilities
- 无现有能力需要修改，这是纯新增功能

## Impact

### Affected Code
- **新增**: `src/one_dragon_agent/core/model/qwen/` - Qwen 模型相关模块
- **新增**: `src/one_dragon_agent/core/model/qwen/qwen_chat_model.py` - QwenChatModel 实现
- **新增**: `src/one_dragon_agent/core/model/qwen/oauth.py` - OAuth 认证逻辑
- **新增**: `src/one_dragon_agent/core/model/qwen/token_manager.py` - Token 管理器
- **新增**: `src/one_dragon_agent/core/system/log.py` - 日志工具
- **新增**: `tests/one_dragon_agent/core/model/qwen/` - Qwen 模型测试
- **新增**: `.env.example` - Qwen 配置示例

### Dependencies
- **新增依赖**: 无（使用 Python 内置库）
  - `asyncio`: 异步任务管理
  - `pathlib`: 文件路径处理
  - `json`: 数据序列化
  - `hashlib`: PKCE 实现
  - `httpx`: HTTP 请求（如项目中已有，复用；否则添加）
- **AgentScope**: 继续使用现有 `agentscope>=1.0.14`

### APIs
- **公共 API**: `QwenChatModel` 类，提供与 `OpenAIChatModel` 相同的接口
- **TokenManager API**: `QwenTokenManager.get_instance()`、`get_access_token()`、`shutdown()`

### Backward Compatibility
- 完全向后兼容，不影响现有的 `OpenAIChatModel` 使用
- 可以在同一项目中同时使用 OpenAI 和 Qwen 模型

### Documentation
- 新增: `docs/develop/modules/qwen-model.md` - Qwen 模型使用文档
- 新增: `examples/qwen_model_example.py` - Qwen 模型使用示例
- 更新: `.env.example` - 添加 Qwen 配置说明
- 更新: `README.md` - 添加 Qwen 模型配置说明
