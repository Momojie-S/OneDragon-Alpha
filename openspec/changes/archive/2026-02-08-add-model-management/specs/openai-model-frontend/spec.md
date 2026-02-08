# OpenAI 模型前端管理界面规范

## ADDED Requirements

### Requirement: 模型配置列表页面
系统 SHALL 提供模型配置列表页面，展示所有 OpenAI 模型配置。

#### Scenario: 显示配置列表
- **WHEN** 用户访问模型配置管理页面
- **THEN** 系统 SHALL 自动加载并显示所有模型配置
- **AND** 每个配置 SHALL 显示：配置名称、baseUrl、支持的能力标签、模型数量、启用状态
- **AND** API key 不显示，后端不返回此字段
- **AND** 列表 SHALL 按创建时间倒序排列

#### Scenario: 列表操作按钮
- **WHEN** 用户查看配置列表
- **THEN** 每个配置项 SHALL 提供"编辑"和"删除"按钮
- **AND** 提供"新建配置"按钮
- **AND** 提供"刷新"按钮重新加载列表

#### Scenario: 空状态展示
- **WHEN** 系统中没有任何模型配置
- **THEN** 页面 SHALL 显示空状态提示
- **AND** 提示信息 SHALL 引导用户创建第一个配置
- **AND** 提供"立即创建"按钮

### Requirement: 创建模型配置对话框
系统 SHALL 提供创建模型配置的对话框。

#### Scenario: 打开创建对话框
- **WHEN** 用户点击"新建配置"按钮
- **THEN** 系统 SHALL 打开创建配置对话框
- **AND** 对话框 SHALL 包含所有必需的表单字段

#### Scenario: 表单字段
- **WHEN** 用户查看创建配置表单
- **THEN** 表单 SHALL 包含以下字段：
  - 配置名称（必填，文本输入框）
  - Base URL（必填，文本输入框，带格式提示）
  - API Key（必填，密码输入框）
  - 模型列表（必填，模型管理区域）

#### Scenario: 添加模型
- **WHEN** 用户在模型管理区域添加模型
- **THEN** 系统 SHALL 提供表单或对话框输入以下信息：
  - 模型 ID（必填，文本输入框，如 "deepseek-chat"）
  - 支持视觉（复选框）
  - 支持思考（复选框）
- **AND** 用户点击"添加"或"确定"按钮后，模型 SHALL 添加到模型列表
- **AND** 每个模型 SHALL 以卡片或标签形式显示
- **AND** 显示模型 ID 和能力标识（视觉、思考）

#### Scenario: 编辑模型信息
- **WHEN** 用户点击已添加模型的"编辑"按钮
- **THEN** 系统 SHALL 打开编辑对话框或展开编辑区域
- **AND** 用户 SHALL 可以修改模型的能力标识
- **AND** 保存后更新该模型的信息

#### Scenario: 删除模型
- **WHEN** 用户点击已添加模型的"删除"按钮
- **THEN** 系统 SHALL 从列表中移除该模型
- **AND** 如果删除后列表为空，显示提示要求至少添加一个模型

#### Scenario: 表单验证
- **WHEN** 用户提交表单但必填字段为空
- **THEN** 系统 SHALL 显示验证错误提示
- **AND** 对应字段 SHALL 高亮显示
- **AND** 系统 SHALL 阻止提交

#### Scenario: 成功创建配置
- **WHEN** 用户填写完整并有效的表单数据并提交
- **THEN** 系统 SHALL 发送创建请求到后端 API
- **AND** 成功后关闭对话框
- **AND** 刷新配置列表
- **AND** 显示成功提示消息

#### Scenario: 创建失败处理
- **WHEN** 后端返回创建失败错误（如名称重复）
- **THEN** 系统 SHALL 显示错误提示消息
- **AND** 对话框 SHALL 保持打开状态
- **AND** 用户 SHALL 可以修改后重新提交

### Requirement: 编辑模型配置对话框
系统 SHALL 提供编辑模型配置的对话框。

#### Scenario: 打开编辑对话框
- **WHEN** 用户点击某个配置的"编辑"按钮
- **THEN** 系统 SHALL 打开编辑配置对话框
- **AND** 对话框 SHALL 预填充该配置的现有数据
- **AND** API key 字段 SHALL 显示为空或占位符（提示"留空则不修改"）

#### Scenario: 修改配置信息
- **WHEN** 用户修改表单字段并提交
- **THEN** 系统 SHALL 发送更新请求到后端 API
- **AND** 成功后关闭对话框
- **AND** 刷新配置列表显示最新数据
- **AND** 显示成功提示消息

#### Scenario: 仅修改部分字段
- **WHEN** 用户仅修改部分字段（如仅修改模型列表）
- **AND** API key 字段留空
- **THEN** 系统 SHALL 仅更新修改的字段
- **AND** API key SHALL 保持不变

### Requirement: 删除模型配置确认
系统 SHALL 提供删除模型配置的确认机制。

#### Scenario: 删除确认对话框
- **WHEN** 用户点击某个配置的"删除"按钮
- **THEN** 系统 SHALL 显示删除确认对话框
- **AND** 对话框 SHALL 提示"确定要删除配置 '{配置名称}' 吗？此操作不可恢复"
- **AND** 提供"确认"和"取消"按钮

#### Scenario: 确认删除
- **WHEN** 用户在确认对话框中点击"确认"按钮
- **THEN** 系统 SHALL 发送删除请求到后端 API
- **AND** 成功后刷新配置列表
- **AND** 显示成功提示消息

#### Scenario: 取消删除
- **WHEN** 用户在确认对话框中点击"取消"按钮
- **THEN** 系统 SHALL 关闭确认对话框
- **AND** 配置 SHALL 保持不变

### Requirement: 启用/禁用配置
系统 SHALL 提供切换配置启用状态的交互。

#### Scenario: 启用状态显示
- **WHEN** 某个配置的 is_active 为 true
- **THEN** 列表中 SHALL 显示"已启用"标签（绿色）
- **AND** 提供开关按钮可用于禁用

#### Scenario: 禁用状态显示
- **WHEN** 某个配置的 is_active 为 false
- **THEN** 列表中 SHALL 显示"已禁用"标签（灰色）
- **AND** 提供开关按钮可用于启用

#### Scenario: 切换启用状态
- **WHEN** 用户点击配置的开关按钮
- **THEN** 系统 SHALL 发送状态切换请求到后端 API
- **AND** 成功后更新显示状态
- **AND** 显示成功提示消息

### Requirement: 能力标签显示
系统 SHALL 在列表中清晰显示配置下模型的能力标识。

#### Scenario: 显示配置能力概览
- **WHEN** 某个配置包含多个模型
- **THEN** 列表中 SHALL 显示该配置下的能力概览
- **AND** 如果有模型支持视觉，显示"视觉"标签（标注支持数量，如 "视觉 (2)"）
- **AND** 如果有模型支持思考，显示"思考"标签（标注支持数量，如 "思考 (1)"）
- **AND** 标签 SHALL 使用不同颜色区分

#### Scenario: 无能力标识
- **WHEN** 某个配置下的所有模型都不支持视觉或思考
- **THEN** 列表中 SHALL 不显示对应的能力标签
- **AND** 仅显示配置名称和模型数量

### Requirement: 模型列表展示
系统 SHALL 在列表中展示每个配置包含的模型及其能力。

#### Scenario: 显示模型数量
- **WHEN** 某个配置包含多个模型
- **THEN** 列表中 SHALL 显示模型数量（如 "3 个模型"）
- **AND** 鼠标悬停或展开时 SHALL 显示所有模型详情

#### Scenario: 显示模型详情
- **WHEN** 用户查看配置详情或展开模型列表
- **THEN** 系统 SHALL 以卡片或表格形式显示所有模型
- **AND** 每个模型 SHALL 显示：
  - 模型 ID
  - 能力标签（视觉、思考）
- **AND** 支持视觉的模型 SHALL 显示"视觉"标签
- **AND** 支持思考的模型 SHALL 显示"思考"标签

### Requirement: 加载状态和错误处理
系统 SHALL 提供良好的加载和错误反馈。

#### Scenario: 列表加载状态
- **WHEN** 页面首次加载或刷新
- **THEN** 系统 SHALL 显示加载动画或骨架屏
- **AND** 加载完成后显示实际数据

#### Scenario: 网络错误处理
- **WHEN** API 请求失败（如网络错误）
- **THEN** 系统 SHALL 显示错误提示消息
- **AND** 错误信息 SHALL 包含问题的简要描述
- **AND** 提供"重试"按钮

#### Scenario: 权限错误处理
- **WHEN** API 返回 401 或 403 错误
- **THEN** 系统 SHALL 显示权限错误提示
- **AND** 引导用户检查登录状态或权限

### Requirement: 响应式设计
系统 SHALL 在不同屏幕尺寸下提供良好的用户体验。

#### Scenario: 大屏幕显示
- **WHEN** 用户使用桌面浏览器访问
- **THEN** 列表 SHALL 以表格或卡片形式展示
- **AND** 所有信息 SHALL 在一屏内清晰可见

#### Scenario: 小屏幕显示
- **WHEN** 用户使用移动设备访问
- **THEN** 列表 SHALL 以卡片形式垂直堆叠
- **AND** 操作按钮 SHALL 调整为适合触摸操作的大小
