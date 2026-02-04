# Qwen 模型集成任务列表

## 1. OAuth 认证实现

- [x] 1.1 创建 `src/one_dragon_agent/core/model/qwen/` 目录结构
- [x] 1.2 实现 `oauth.py` 中的数据模型
  - `QwenDeviceAuthorization` 数据类
  - `QwenOAuthToken` 数据类
  - `DeviceTokenResult` 类型定义
- [x] 1.3 实现 PKCE 辅助函数
  - `generate_pkce()`: 生成 code_verifier 和 code_challenge
  - 使用 `hashlib.sha256` 和 base64url 编码
- [x] 1.4 实现 `QwenOAuthClient.get_device_code()` 方法
  - POST 请求到 `/api/v1/oauth2/device/code`
  - 包含 client_id、scope、code_challenge、code_challenge_method
  - 错误处理和响应验证
- [x] 1.5 实现 `QwenOAuthClient.poll_device_token()` 方法
  - POST 请求到 `/api/v1/oauth2/token`
  - 包含 grant_type、device_code、code_verifier
  - 处理 authorization_pending、slow_down、error 状态
- [x] 1.6 实现 `QwenOAuthClient.refresh_token()` 方法
  - POST 请求到 `/api/v1/oauth2/token`
  - 包含 grant_type=refresh_token、refresh_token、client_id
  - 处理 400 错误（refresh_token 无效）
  - 处理响应中可能缺失的 refresh_token
- [x] 1.7 实现 `login_qwen_oauth()` 完整流程
  - 调用 `get_device_code()` 和 `generate_pkce()`
  - 显示 user_code 和验证 URL
  - 轮询 `poll_device_token()` 直到授权或超时
  - 处理 slow_down（增加轮询间隔）
- [x] 1.8 为 OAuth 流程编写单元测试
  - ✅ 测试 PKCE 生成 (test_generate_pkce.py, 7 个测试)
  - ✅ 测试设备码获取 (test_get_device_code.py, 6 个测试)
  - ✅ 测试轮询逻辑（test_poll_device_token.py, 8 个测试）
  - ✅ 测试 refresh_token 流程 (test_refresh_token.py, 7 个测试)

## 2. Token 管理实现

- [x] 2.1 创建 `token_manager.py` 模块
- [x] 2.2 实现 `TokenPersistence` 类
  - `save_token()`: 保存 token 到 `~/.qwen/token.json`
  - `load_token()`: 从文件加载 token
  - `delete_token()`: 删除 token 文件
  - 设置文件权限为 0600
  - 处理文件不存在或损坏的情况
- [x] 2.3 实现 `QwenTokenManager` 单例模式
  - `get_instance()`: 类方法，返回全局唯一实例
  - `reset()`: 清除单例（用于测试）
  - 初始化 `stop_event` 和 `_lock`
- [x] 2.4 实现 `QwenTokenManager.get_access_token()` 方法
  - 异步方法
  - 首次调用时加载或认证 token
  - 调用 `_start_refresh_timer()` 启动定时任务
- [x] 2.5 实现 `QwenTokenManager._start_refresh_timer()` 方法
  - 检查定时任务是否已运行
  - 创建 asyncio.Task 运行 `_refresh_loop()`
- [x] 2.6 实现 `QwenTokenManager._refresh_loop()` 方法
  - 计算刷新时间：`expires_at - 5 * 60 * 1000`
  - 使用 `asyncio.wait_for()` 和 `stop_event.wait()` 实现可中断等待
  - 调用 `_refresh_token()` 执行刷新
  - 刷新失败时等待 60 秒后重试
  - refresh_token 无效时停止任务
- [x] 2.7 实现 `QwenTokenManager._refresh_token()` 私有方法
  - 使用 `asyncio.Lock` 保护刷新操作
  - 调用 `QwenOAuthClient.refresh_token()`
  - 更新 `self._token`
  - 调用 `TokenPersistence.save_token()`
- [x] 2.8 实现 `QwenTokenManager.shutdown()` 方法
  - 设置 `stop_event`
  - 取消定时任务
  - 等待任务完成清理
- [x] 2.9 为 TokenManager 编写单元测试
  - ✅ 测试 token 文件读写和权限 (test_token_persistence.py, 11 个测试)
  - ✅ 测试定时任务启动和停止 (test_token_manager.py, 3 个测试)
  - ✅ 测试刷新循环逻辑 (test_token_manager.py, 3 个测试)
  - ✅ 测试并发场景 (test_token_manager.py, 2 个测试)

## 3. QwenChatModel 集成

- [x] 3.1 创建 `qwen_chat_model.py` 模块
- [x] 3.2 实现 `QwenChatModel` 类继承 `OpenAIChatModel`
  - `__init__()` 方法：
    - 获取 `QwenTokenManager` 单例
    - 调用 `get_access_token()` 获取 token
    - 调用父类构造函数，传入 api_key 和 base_url
- [x] 3.3 定义支持的模型类型
  - `coder-model`: 仅文本输入
  - `vision-model`: 文本和图像输入
  - 模型 ID 格式：`qwen-portal/{model_name}`
- [x] 3.4 创建 `__init__.py` 导出公共 API
  - `QwenChatModel`
  - 异常类（`QwenOAuthError`, `QwenRefreshTokenInvalidError` 等）
- [x] 3.5 为 QwenChatModel 编写集成测试
  - ✅ Mock TokenManager 测试初始化 (test_qwen_chat_model.py, 4 个测试)
  - ✅ 测试与 AgentScope 的集成 (test_qwen_chat_model.py, 3 个测试)
  - ✅ 测试不同模型类型 (test_qwen_chat_model.py, 2 个测试)

## 4. 异常处理

- [x] 4.1 定义异常类层次结构
  - `QwenError`: 基础异常类
  - `QwenOAuthError`: OAuth 流程错误
  - `QwenRefreshTokenInvalidError`: refresh_token 无效
  - `QwenTokenExpiredError`: token 过期
  - `QwenTokenNotAvailableError`: token 不可用
- [x] 4.2 为异常类添加清晰的错误信息
  - 包含错误原因
  - 提供解决建议（如"请重新认证"）

## 5. 测试

- [x] 5.1 创建 `tests/one_dragon_agent/core/model/qwen/` 目录
- [x] 5.2 编写 OAuth 流程测试
  - ✅ `test_generate_pkce.py`: 7 个测试
  - ✅ `test_get_device_code.py`: 6 个测试
  - ✅ `test_poll_device_token.py`: 8 个测试
  - ✅ `test_refresh_token.py`: 7 个测试
- [x] 5.3 编写 Token 管理测试
  - ✅ `test_token_persistence.py`: 11 个测试
  - ✅ `test_token_manager.py`: 12 个测试
  - ✅ `test_refresh_loop.py`: 包含在 test_token_manager.py 中
- [x] 5.4 编写 QwenChatModel 测试
  - ✅ `test_qwen_chat_model.py`: 9 个测试
- [x] 5.5 运行所有测试并确保通过
  - ✅ 总计 60 个测试全部通过
  - ✅ 命令: `uv run --env-file .env pytest tests/one_dragon_agent/core/model/qwen/`

## 6. 文档

- [x] 6.1 创建 `docs/develop/modules/qwen-model.md`
  - QwenChatModel 使用说明
  - TokenManager 生命周期管理
  - OAuth 认证流程
  - 异常处理指南
- [x] 6.2 创建使用示例
  - ✅ `examples/qwen_model_example.py` 包含基本使用、多模型类型、错误处理示例
- [x] 6.3 更新 `.env.example`
  - 添加 Qwen 相关注释
- [x] 6.4 更新主 README
  - 添加 Qwen 模型配置说明

## 7. 代码质量

- [x] 7.1 运行 ruff 检查
  - `uv run ruff check src/one_dragon_agent/core/model/qwen/`
  - 修复所有警告和错误
- [x] 7.2 运行 ruff 格式化
  - `uv run ruff format src/one_dragon_agent/core/model/qwen/`
- [x] 7.3 添加类型提示
  - 确保所有函数签名包含类型提示
  - 使用 `TYPE_CHECKING` 导入类型注解
- [x] 7.4 添加 docstring
  - ✅ 所有公共类和方法包含 Google 风格的 docstring
  - ✅ 通过 pydocstyle 检查
