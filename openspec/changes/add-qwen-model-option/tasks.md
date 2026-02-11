# Qwen 模型配置功能实现任务清单

## 1. 数据库迁移

- [ ] 1.1 创建数据库迁移脚本，添加 OAuth 相关字段到 model_configs 表
- [ ] 1.2 添加 oauth_access_token、oauth_token_type、oauth_refresh_token、oauth_expires_at、oauth_scope、oauth_metadata 字段
- [ ] 1.3 创建 idx_oauth_expires_at 索引
- [ ] 1.4 编写并执行数据库迁移测试

## 2. 后端 - Token 加密工具

- [ ] 2.1 创建 src/one_dragon_agent/core/security/token_encryption.py 模块
- [ ] 2.2 实现 TokenEncryption 类，封装 Fernet 加密/解密逻辑
- [ ] 2.3 添加从环境变量读取 TOKEN_ENCRYPTION_KEY 的逻辑
- [ ] 2.4 实现默认密钥生成（未配置时）
- [ ] 2.5 编写单元测试验证加密/解密功能

## 3. 后端 - MySQL Token 持久化

- [ ] 3.1 创建 src/one_dragon_agent/core/model/qwen/mysql_token_persistence.py
- [ ] 3.2 实现 MySQLTokenPersistence 类
- [ ] 3.3 实现 save_token 方法，加密并保存 token 到数据库
- [ ] 3.4 实现 load_token 方法，从数据库读取并解密 token
- [ ] 3.5 实现 delete_token 方法，清除数据库中的 token
- [ ] 3.6 编写单元测试验证持久化功能

## 4. 后端 - OAuth API 端点

- [ ] 4.1 创建 src/one_dragon_agent/api/routes/qwen_oauth.py
- [ ] 4.2 实现 POST /api/qwen/oauth/device-code 端点
- [ ] 4.3 实现内存会话存储（使用字典 + asyncio.Lock）
- [ ] 4.4 实现 GET /api/qwen/oauth/status 端点
- [ ] 4.5 添加会话超时清理逻辑（15 分钟）
- [ ] 4.6 集成 QwenOAuthClient 进行设备码和轮询逻辑
- [ ] 4.7 添加 API 频率限制（1 分钟 10 次）
- [ ] 4.8 编写端到端测试验证 OAuth 流程

## 5. 后端 - 模型配置服务扩展

- [ ] 5.1 修改 src/one_dragon_agent/core/model/repository.py
- [ ] 5.2 更新 ModelConfigORM 支持新的 OAuth 字段
- [ ] 5.3 修改 create_to_dict 方法处理 OAuth 字段
- [ ] 5.4 更新 dict_to_orm 方法支持 OAuth 字段序列化
- [ ] 5.5 修改 update_config 方法支持 OAuth 字段更新
- [ ] 5.6 编写单元测试验证仓库功能

## 6. 后端 - ModelFactory 扩展

- [ ] 6.1 修改 src/one_dragon_agent/core/model/model_factory.py
- [ ] 6.2 实现 _create_qwen_model 方法从数据库读取 token
- [ ] 6.3 添加 token 过期检查逻辑
- [ ] 6.4 实现按需刷新 token 功能（调用 MySQLTokenPersistence）
- [ ] 6.5 处理 refresh_token 过期场景
- [ ] 6.6 编写单元测试验证模型创建和 token 刷新

## 7. 后端 - API 路由注册

- [ ] 7.1 在主路由文件中注册 qwen_oauth 路由
- [ ] 7.2 添加 API 文档（OpenAPI/Swagger）
- [ ] 7.3 配置 TOKEN_ENCRYPTION_KEY 环境变量到 .env.example
- [ ] 7.4 验证 API 端点可访问

## 8. 后端测试

- [ ] 8.1 编写 MySQLTokenPersistence 单元测试
- [ ] 8.2 编写 OAuth API 端点端到端测试
- [ ] 8.3 编写 ModelFactory Qwen 模型创建测试
- [ ] 8.4 编写 token 刷新功能测试
- [ ] 8.5 运行所有测试确保通过

## 9. 前端 - API 服务

- [ ] 9.1 创建 frontend/src/services/qwenOAuthApi.ts
- [ ] 9.2 实现 getDeviceCode 方法
- [ ] 9.3 实现 pollOAuthStatus 方法
- [ ] 9.4 添加 TypeScript 类型定义
- [ ] 9.5 处理错误响应和超时

## 10. 前端 - Provider 选择器

- [ ] 10.1 修改 ModelConfigDialog.vue，启用 Provider 选择器
- [ ] 10.2 添加 Qwen 选项到下拉列表
- [ ] 10.3 设置默认值为 "openai"
- [ ] 10.4 添加 Provider 切换事件监听

## 11. 前端 - 动态表单字段

- [ ] 11.1 使用 computed 属性动态控制字段显示/隐藏
- [ ] 11.2 选择 "openai" 时显示 Base URL、API Key、测试连接按钮
- [ ] 11.3 选择 "qwen" 时显示 OAuth 登录按钮
- [ ] 11.4 Provider 切换时清空相关字段值
- [ ] 11.5 添加过渡动画

## 12. 前端 - OAuth 登录按钮

- [ ] 12.1 添加"登录 Qwen 账号"按钮
- [ ] 12.2 实现点击事件调用 getDeviceCode API
- [ ] 12.3 处理 API 错误并显示提示
- [ ] 12.4 添加加载状态

## 13. 前端 - 用户码对话框

- [ ] 13.1 创建用户码显示对话框组件
- [ ] 13.2 显示验证链接（可点击）
- [ ] 13.3 显示用户码（大字体，可点击复制）
- [ ] 13.4 显示操作提示文字
- [ ] 13.5 显示轮询状态（等待授权中...）
- [ ] 13.6 实现关闭按钮停止轮询

## 14. 前端 - OAuth 状态轮询

- [ ] 14.1 实现轮询逻辑，按后端返回的间隔轮询
- [ ] 14.2 处理 pending 状态，继续轮询
- [ ] 14.3 处理 success 状态，关闭对话框，更新认证状态
- [ ] 14.4 处理 timeout 错误，显示提示
- [ ] 14.5 处理其他错误，显示提示并提供重试
- [ ] 14.6 组件销毁时清理轮询定时器

## 15. 前端 - 表单验证

- [ ] 15.1 使用 computed 属性动态生成验证规则
- [ ] 15.2 OpenAI Provider 验证 base_url 和 api_key 不为空
- [ ] 15.3 Qwen Provider 验证 oauth_access_token 不为空
- [ ] 15.4 Qwen Provider 未认证时阻止提交并提示
- [ ] 15.5 两种 Provider 都验证 models 不为空

## 16. 前端 - 认证状态显示

- [ ] 16.1 已认证时显示"✓ 已认证"绿色标签
- [ ] 16.2 未认证时显示"登录 Qwen 账号"按钮
- [ ] 16.3 Token 过期时显示"认证已过期，请重新登录"
- [ ] 16.4 编辑配置时显示当前认证状态
- [ ] 16.5 添加"重新登录"按钮（已认证状态下）

## 17. 前端 - 配置列表显示

- [ ] 17.1 在配置列表中显示 Provider 类型标签
- [ ] 17.2 OpenAI 配置显示蓝色标签
- [ ] 17.3 Qwen 配置显示绿色标签
- [ ] 17.4 Qwen 配置显示认证状态指示器
- [ ] 17.5 Token 过期时显示黄色警告图标

## 18. 前端测试

- [ ] 18.1 使用 chrome-devtools 测试 Provider 切换
- [ ] 18.2 测试 OpenAI 配置创建流程
- [ ] 18.3 测试 Qwen OAuth 认证流程
- [ ] 18.4 测试 Qwen 配置创建流程
- [ ] 18.5 测试 Qwen 配置编辑流程
- [ ] 18.6 编写 Playwright 端到端测试
- [ ] 18.7 编写关键组件单元测试

## 19. 集成测试

- [ ] 19.1 后端 + 前端联调，创建 Qwen 配置
- [ ] 19.2 使用 Qwen 模型进行对话测试
- [ ] 19.3 验证 token 自动刷新功能
- [ ] 19.4 测试多个 Qwen 配置场景
- [ ] 19.5 测试 token 过期后重新登录

## 20. 文档和部署

- [ ] 20.1 更新 API 文档
- [ ] 20.2 编写用户使用指南
- [ ] 20.3 配置 TOKEN_ENCRYPTION_KEY 环境变量
- [ ] 20.4 执行数据库迁移脚本
- [ ] 20.5 部署后端代码
- [ ] 20.6 部署前端代码
- [ ] 20.7 验证生产环境功能
