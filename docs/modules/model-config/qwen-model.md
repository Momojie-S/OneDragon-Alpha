# Qwen 模型集成

## 概述

Qwen 模型集成提供了通过 OAuth 2.0 设备码流程使用 Qwen 模型的能力，支持自动 token 刷新和持久化存储。

## 核心组件

### 1. QwenChatModel

`QwenChatModel` 继承自 AgentScope 的 `OpenAIChatModel`，提供与 Qwen 模型的无缝集成。

**特性：**
- 自动 OAuth 认证
- 自动 token 刷新
- 支持多种 Qwen 模型类型
- 与 AgentScope 完全兼容

### 2. QwenOAuthClient

OAuth 2.0 设备码流程客户端，处理所有认证相关操作。

**主要方法：**
- `get_device_code()` - 获取设备码和用户码
- `poll_device_token()` - 轮询获取 access token
- `refresh_token()` - 刷新过期的 access token

### 3. QwenTokenManager

Token 管理器，采用单例模式，负责 token 的生命周期管理。

**特性：**
- Token 持久化存储
- 后台自动刷新（过期前 5 分钟）
- 线程安全的 token 访问
- 与 Qwen CLI token 自动同步

## 使用方法

### 基本使用

```python
import asyncio
from one_dragon_agent.core.model.qwen import QwenChatModel, login_qwen_oauth

async def main():
    # 首次使用需要进行 OAuth 认证
    await login_qwen_oauth()

    # 创建模型实例
    model = QwenChatModel(model_name="coder-model")

    # 使用模型
    response = await model("Hello, Qwen!")
    print(response)

    # 关闭 token 管理器
    from one_dragon_agent.core.model.qwen import QwenTokenManager
    await QwenTokenManager.get_instance().shutdown()

asyncio.run(main())
```

### 支持的模型类型

- `coder-model` - 代码生成模型（仅文本）
- `vision-model` - 视觉模型（文本 + 图像）

完整的模型 ID 格式为 `qwen-portal/{model_name}`。

### Token 生命周期管理

```python
from one_dragon_agent.core.model.qwen import QwenTokenManager

# 获取单例实例
manager = QwenTokenManager.get_instance()

# 获取 access token（会自动加载或刷新）
token = await manager.get_access_token()

# 关闭管理器（停止后台刷新任务）
await manager.shutdown()
```

## OAuth 认证流程

### 设备码流程

1. 调用 `login_qwen_oauth()` 启动认证
2. 系统显示用户码（user_code）和验证 URL
3. 用户在浏览器中打开验证 URL 并输入用户码
4. 程序自动轮询获取 access token
5. Token 自动保存到 `~/.one_dragon_alpha/qwen_oauth_creds.json`

### Token 刷新机制

- Token 管理器在后台运行，自动检测 token 过期时间
- 在 token 过期前 5 分钟自动刷新
- 如果刷新失败，会每 60 秒重试一次
- 如果 refresh_token 无效，停止自动刷新并提示重新认证

## 异常处理

### 异常类层次结构

```
QwenError
├── QwenOAuthError              # OAuth 认证流程错误
├── QwenRefreshTokenInvalidError # refresh_token 无效
├── QwenTokenExpiredError       # access token 过期
└── QwenTokenNotAvailableError  # token 不可用
```

### 错误处理示例

```python
from one_dragon_agent.core.model.qwen import (
    QwenTokenNotAvailableError,
    QwenRefreshTokenInvalidError,
)

try:
    model = QwenChatModel()
    response = model("Hello!")
except QwenTokenNotAvailableError:
    print("未找到有效 token，请先进行 OAuth 认证")
    await login_qwen_oauth()
except QwenRefreshTokenInvalidError:
    print("refresh_token 无效，需要重新认证")
    await login_qwen_oauth()
```

## 配置选项

### 环境变量

虽然支持通过代码参数配置，但通常使用默认值即可：

- `QWEN_OAUTH_CLIENT_ID` - OAuth 客户端 ID（默认使用内置值）
- `QWEN_TOKEN_PATH` - Token 存储路径（默认 `~/.one_dragon_alpha/qwen_oauth_creds.json`）

### 自定义配置

```python
from one_dragon_agent.core.model.qwen import QwenChatModel

model = QwenChatModel(
    model_name="coder-model",
    client_id="your-client-id",  # 可选
    token_path="/custom/path/token.json"  # 可选
)
```

## 最佳实践

### 1. Token 管理器生命周期

```python
import asyncio
from one_dragon_agent.core.model.qwen import QwenChatModel, QwenTokenManager

async def main():
    try:
        model = QwenChatModel()
        # 使用模型...
    finally:
        # 始终在程序结束时关闭 token 管理器
        await QwenTokenManager.get_instance().shutdown()

asyncio.run(main())
```

### 2. 多线程/多进程使用

`QwenTokenManager` 使用单例模式，可以在多个组件间共享：

```python
from one_dragon_agent.core.model.qwen import QwenChatModel, QwenTokenManager

# 在不同地方使用，共享同一个 token 管理器
model1 = QwenChatModel()
model2 = QwenChatModel()

# 只需关闭一次
await QwenTokenManager.get_instance().shutdown()
```

### 3. Token 同步

如果已使用 Qwen CLI 进行认证，程序会自动同步 token：
- 检查 `~/.qwen/oauth_creds.json`
- 自动复制到 `~/.one_dragon_alpha/qwen_oauth_creds.json`

## 故障排除

### 认证失败

**问题**：OAuth 认证超时或失败

**解决方案**：
1. 检查网络连接
2. 确认在浏览器中正确输入了用户码
3. 重新运行 `login_qwen_oauth()`

### Token 刷新失败

**问题**：日志显示 "Refresh token invalid, stopping auto-refresh"

**解决方案**：
1. 删除 token 文件：`rm ~/.one_dragon_alpha/qwen_oauth_creds.json`
2. 重新运行 `login_qwen_oauth()` 进行认证

### 模型调用失败

**问题**：API 返回 401 错误

**解决方案**：
1. 检查 token 是否过期
2. 手动触发 token 刷新或重新认证
3. 确认使用的模型名称正确

## 相关模块

- `one_dragon_agent.core.model.qwen.qwen_chat_model` - QwenChatModel 实现
- `one_dragon_agent.core.model.qwen.oauth` - OAuth 认证逻辑
- `one_dragon_agent.core.model.qwen.token_manager` - Token 管理器
