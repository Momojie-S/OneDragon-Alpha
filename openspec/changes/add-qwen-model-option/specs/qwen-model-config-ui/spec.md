# 前端 Qwen 模型配置界面规范

## ADDED Requirements

### Requirement: Provider 选择器

系统 MUST 提供 Provider 选择器，允许用户选择 OpenAI 或 Qwen 提供商。

#### Scenario: 创建新配置时默认选择 OpenAI
- **WHEN** 用户打开"新建配置"对话框
- **THEN** Provider 选择器 MUST 显示 "OpenAI" 作为默认选项
- **AND** 选择器 MUST 处于可编辑状态

#### Scenario: Provider 选项包含 OpenAI 和 Qwen
- **WHEN** 用户点击 Provider 下拉框
- **THEN** 下拉列表 MUST 包含 "OpenAI" 和 "Qwen" 两个选项
- **AND** 选项 MUST 按字母顺序排列

### Requirement: 动态表单字段显示

系统 MUST 根据选择的 Provider 类型显示不同的配置字段。

#### Scenario: 选择 OpenAI 时显示完整字段
- **WHEN** 用户选择 Provider 为 "OpenAI"
- **THEN** 系统 MUST 显示 Base URL 字段
- **AND** 系统 MUST 显示 API Key 字段
- **AND** 系统 MUST 显示测试连接按钮
- **AND** 系统 MUST 隐藏 OAuth 登录按钮

#### Scenario: 选择 Qwen 时显示 OAuth 字段
- **WHEN** 用户选择 Provider 为 "Qwen"
- **THEN** 系统 MUST 隐藏 Base URL 字段
- **AND** 系统 MUST 隐藏 API Key 字段
- **AND** 系统 MUST 隐藏测试连接按钮
- **AND** 系统 MUST 显示 OAuth 登录按钮

#### Scenario: Provider 切换时清空相关字段
- **WHEN** 用户从 OpenAI 切换到 Qwen
- **THEN** 系统 MUST 清空 Base URL 字段值
- **AND** 系统 MUST 清空 API Key 字段值
- **AND** 系统 MUST 清空认证状态

### Requirement: OAuth 登录按钮

系统 MUST 为 Qwen Provider 提供 OAuth 登录按钮。

#### Scenario: 未认证时显示登录按钮
- **WHEN** 用户选择 Qwen Provider 且未完成认证
- **THEN** 系统 MUST 显示"登录 Qwen 账号"按钮
- **AND** 按钮 MUST 处于可点击状态

#### Scenario: 已认证时显示认证状态
- **WHEN** 用户已完成 Qwen OAuth 认证
- **THEN** 系统 MUST 显示"✓ 已认证"状态标签
- **AND** 状态标签 MUST 使用成功颜色（绿色）
- **AND** 系统 MUST 隐藏登录按钮

#### Scenario: 点击登录按钮触发认证流程
- **WHEN** 用户点击"登录 Qwen 账号"按钮
- **THEN** 系统 MUST 调用后端 API 获取设备码
- **AND** 系统 MUST 显示用户码和验证链接对话框

### Requirement: 用户码显示对话框

系统 MUST 在用户点击登录按钮后显示用户码和验证链接。

#### Scenario: 显示用户码和验证链接
- **WHEN** 系统 SUCCESSFULLY 获取到设备码
- **THEN** 系统 MUST 显示对话框，标题为"Qwen OAuth 认证"
- **AND** 对话框 MUST 显示验证链接（可点击）
- **AND** 对话框 MUST 显示用户码（大字体，易于复制）
- **AND** 对话框 MUST 显示操作提示文字
- **AND** 对话框 MUST 显示轮询状态（等待授权中...）

#### Scenario: 用户码可一键复制
- **WHEN** 用户点击用户码区域
- **THEN** 系统 MUST 自动复制用户码到剪贴板
- **AND** 系统 MUST 显示"已复制"提示

#### Scenario: 设备码获取失败时显示错误
- **WHEN** 后端 API 返回错误
- **THEN** 系统 MUST 显示错误提示对话框
- **AND** 错误信息 MUST 包含失败原因
- **AND** 系统 MUST 提供"重试"按钮

### Requirement: OAuth 认证状态轮询

系统 MUST 在显示用户码后轮询检查认证状态。

#### Scenario: 按后端指定间隔轮询
- **WHEN** 系统 START 轮询认证状态
- **THEN** 系统 MUST 按后端返回的 interval 间隔发送请求
- **AND** 请求 MUST 发送到 `/api/qwen/oauth/status` 端点
- **AND** 请求 MUST 包含 device_code 参数

#### Scenario: 认证成功后关闭对话框
- **WHEN** 后端返回认证成功状态
- **THEN** 系统 MUST 关闭用户码对话框
- **AND** 系统 MUST 显示"认证成功"提示消息
- **AND** 系统 MUST 更新登录按钮为"✓ 已认证"状态

#### Scenario: 认证超时时显示错误
- **WHEN** 后端返回认证超时
- **THEN** 系统 MUST 关闭用户码对话框
- **AND** 系统 MUST 显示"认证超时，请重试"错误提示
- **AND** 系统 MUST 保持登录按钮可点击状态

#### Scenario: 用户手动关闭对话框时停止轮询
- **WHEN** 用户点击用户码对话框的关闭按钮
- **THEN** 系统 MUST 停止轮询
- **AND** 系统 MUST 关闭对话框
- **AND** 系统 MUST 保持登录按钮可点击状态

### Requirement: 表单验证逻辑适配

系统 MUST 根据 Provider 类型调整表单验证规则。

#### Scenario: OpenAI Provider 验证必填字段
- **WHEN** 用户选择 OpenAI Provider 并提交表单
- **THEN** 系统 MUST 验证 Base URL 不为空
- **AND** 系统 MUST 验证 API Key 不为空
- **AND** 系统 MUST 验证至少添加一个模型

#### Scenario: Qwen Provider 不验证 Base URL 和 API Key
- **WHEN** 用户选择 Qwen Provider 并提交表单
- **THEN** 系统 MUST NOT 验证 Base URL（允许为空）
- **AND** 系统 MUST NOT 验证 API Key（允许为空）
- **AND** 系统 MUST 验证已完成 OAuth 认证
- **AND** 系统 MUST 验证至少添加一个模型

#### Scenario: Qwen Provider 未认证时阻止提交
- **WHEN** 用户选择 Qwen Provider 且未完成认证
- **AND** 用户点击"保存"按钮
- **THEN** 系统 MUST 显示错误提示"请先完成 Qwen 账号认证"
- **AND** 系统 MUST 阻止表单提交

### Requirement: 编辑现有 Qwen 配置

系统 MUST 支持编辑现有的 Qwen 模型配置。

#### Scenario: 编辑 Qwen 配置时显示认证状态
- **WHEN** 用户打开编辑 Qwen 配置对话框
- **THEN** 系统 MUST 显示当前的认证状态
- **AND** 如果已认证，MUST 显示"✓ 已认证"状态
- **AND** 如果 token 已过期，MUST 显示"认证已过期"状态

#### Scenario: 重新认证替换旧 token
- **WHEN** 用户在已认证的 Qwen 配置中点击"重新登录"
- **THEN** 系统 MUST 触发新的 OAuth 认证流程
- **AND** 认证成功后 MUST 替换数据库中的旧 token
- **AND** 系统 MUST 更新认证状态显示

### Requirement: Qwen 配置列表显示

系统 MUST 在配置列表中区分 OpenAI 和 Qwen 配置。

#### Scenario: 列表项显示 Provider 类型
- **WHEN** 用户查看模型配置列表
- **THEN** 每个配置项 MUST 显示 Provider 类型标签
- **AND** OpenAI 配置 MUST 显示蓝色"OpenAI"标签
- **AND** Qwen 配置 MUST 显示绿色"Qwen"标签

#### Scenario: Qwen 配置显示认证状态指示器
- **WHEN** Qwen 配置的 token 有效
- **THEN** 配置项 MUST 显示绿色的认证成功图标
- **AND** 图标 MUST 有 tooltip 提示"已认证"

#### Scenario: Qwen 配置 token 过期时显示警告
- **WHEN** Qwen 配置的 token 已过期
- **THEN** 配置项 MUST 显示黄色的警告图标
- **AND** 图标 MUST 有 tooltip 提示"认证已过期，请重新登录"
