# Chat 模型选择器规范

## ADDED Requirements

### Requirement: 模型选择器展示
系统 SHALL 在 ChatAnalysis 页面顶部固定显示一个下拉选择器，用于选择要使用的模型配置。

#### Scenario: 显示可用模型配置列表
- **WHEN** 用户访问 ChatAnalysis 页面
- **AND** 系统中存在至少一个已启用的模型配置
- **THEN** 系统 SHALL 在页面顶部显示一个下拉选择器
- **AND** 选择器 SHALL 处于可交互状态
- **AND** 选择器中 SHALL 显示所有已启用的模型配置
- **AND** 每个选项 SHALL 显示配置名称和包含的模型数量（格式："<配置名称> (<数量>个模型)"）

#### Scenario: 无可用模型配置
- **WHEN** 用户访问 ChatAnalysis 页面
- **AND** 系统中不存在已启用的模型配置
- **THEN** 系统 SHALL 仍然在页面顶部显示下拉选择器
- **AND** 选择器 SHALL 处于禁用（disabled）状态
- **AND** 选择器的占位符文本 SHALL 显示提示信息（如 "暂无可用模型，请先添加模型配置"）
- **AND** 用户点击选择器时 SHALL 不展开下拉列表

#### Scenario: 选择器加载状态
- **WHEN** 用户访问 ChatAnalysis 页面
- **AND** 模型配置列表正在加载中
- **THEN** 系统 SHALL 在选择器位置显示加载状态
- **AND** 加载状态 SHALL 使用 Element Plus 的 loading 组件

### Requirement: 模型选择器默认值
系统 SHALL 在页面加载时自动选择一个默认的模型配置。

#### Scenario: 恢复上次选择的模型
- **WHEN** 用户访问 ChatAnalysis 页面
- **AND** localStorage 中存在上次选择的模型配置 ID
- **AND** 该模型配置仍然存在且已启用
- **THEN** 系统 SHALL 自动选中该模型配置
- **AND** 选择器 SHALL 显示该模型配置

#### Scenario: 选择第一个启用的模型
- **WHEN** 用户访问 ChatAnalysis 页面
- **AND** localStorage 中不存在上次选择的模型配置 ID
- **OR** localStorage 中的模型配置 ID 已不存在或已禁用
- **AND** 系统中存在至少一个已启用的模型配置
- **THEN** 系统 SHALL 自动选中第一个已启用的模型配置
- **AND** 选择器 SHALL 显示该模型配置

### Requirement: 模型选择交互
系统 SHALL 允许用户通过下拉选择器切换当前使用的模型配置。

#### Scenario: 用户切换模型
- **WHEN** 用户点击下拉选择器
- **THEN** 系统 SHALL 展开所有可用的模型配置选项
- **AND** 用户点击某个选项时
- **THEN** 系统 SHALL 更新当前选中的模型配置
- **AND** 选择器 SHALL 显示新选中的配置

#### Scenario: 对话中切换模型
- **WHEN** 用户在已有对话的页面中切换模型配置
- **THEN** 系统 SHALL 更新当前选中的模型
- **AND** 后续发送的新消息 SHALL 使用新选中的模型
- **AND** 历史消息 SHALL 保持不变

### Requirement: 选中状态持久化
系统 SHALL 将用户选择的模型配置 ID 保存到 localStorage 中。

#### Scenario: 保存选择的模型
- **WHEN** 用户选择或切换模型配置
- **THEN** 系统 SHALL 将选中的模型配置 ID 保存到 localStorage
- **AND** 存储键名 SHALL 为 "chat-selected-model-config-id"

#### Scenario: 清除无效的选择
- **WHEN** 用户选择的模型配置被删除或禁用
- **THEN** 系统 SHALL 从 localStorage 中移除该选择
- **AND** 系统 SHALL 自动选择第一个可用的模型配置

### Requirement: 模型配置数据获取
系统 SHALL 在每次进入 ChatAnalysis 页面时通过后端 API 重新获取已启用的模型配置列表。

#### Scenario: 获取成功
- **WHEN** 组件挂载时（即每次进入页面时）
- **THEN** 系统 SHALL 调用 `/api/models/configs?is_active=true` 接口
- **AND** 系统 SHALL 不使用任何缓存，每次都从后端获取最新数据
- **AND** 接口返回成功时
- **THEN** 系统 SHALL 解析返回的模型配置列表
- **AND** 系统 SHALL 填充选择器的选项

#### Scenario: 获取失败
- **WHEN** 组件挂载时
- **AND** 调用接口失败
- **THEN** 系统 SHALL 在选择器位置显示错误提示
- **AND** 错误提示 SHALL 包含重试按钮
- **AND** 用户点击重试按钮时
- **THEN** 系统 SHALL 重新调用接口

### Requirement: 模型选项显示格式
系统 SHALL 在选择器中以统一的格式显示模型配置信息。

#### Scenario: 单个模型的配置
- **WHEN** 模型配置包含 1 个模型
- **THEN** 选项显示格式 SHALL 为 "<配置名称> (1个模型)"

#### Scenario: 多个模型的配置
- **WHEN** 模型配置包含多个模型
- **THEN** 选项显示格式 SHALL 为 "<配置名称> (N个模型)"
- **AND** N SHALL 为该配置中模型的总数量

#### Scenario: 配置名称截断
- **WHEN** 配置名称超过一定长度（如 30 个字符）
- **THEN** 系统 SHALL 对配置名称进行截断
- **AND** 截断后添加省略号（...）
- **AND** 鼠标悬停时 SHALL 显示完整配置名称（通过 title 属性）

### Requirement: 选择器样式和布局
系统 SHALL 提供美观且易用的选择器样式。

#### Scenario: 选择器位置
- **WHEN** ChatAnalysis 页面渲染时
- **THEN** 选择器 SHALL 始终固定显示在页面顶部
- **AND** 选择器 SHALL 居中显示
- **AND** 选择器 SHALL 与消息列表和输入框保持一致的宽度（最大 840px）
- **AND** 无论是否有可用模型配置，选择器 SHALL 始终可见

#### Scenario: 选择器样式
- **WHEN** 选择器显示时
- **THEN** 选择器 SHALL 使用 Element Plus 的默认样式
- **AND** 选择器 SHALL 支持响应式布局
- **AND** 在移动端 SHALL 保持良好的可用性

#### Scenario: 选择器禁用状态样式
- **WHEN** 选择器处于禁用状态（无可用模型配置）
- **THEN** 选择器 SHALL 显示 Element Plus 的禁用样式（灰色背景）
- **AND** 占位符文本 SHALL 显示为浅色
- **AND** 用户 SHALL 无法点击或交互
