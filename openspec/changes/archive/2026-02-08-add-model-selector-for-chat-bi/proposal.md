# 为 ChatAnalysis 页面增加模型选择框

## Why

当前 ChatAnalysis 页面（聊天 BI 功能）没有模型选择功能，用户无法在对话前选择使用哪个模型配置。由于系统已支持多个模型配置（如 OpenAI、DeepSeek、Qwen 等），用户需要能够在不同模型之间切换以测试和比较不同模型的效果，或者根据不同场景选择最合适的模型。

## What Changes

- **新增模型选择器组件**：在 ChatAnalysis 页面顶部添加一个下拉选择框，显示所有已启用的模型配置
- **模型信息展示**：选择框中每个选项显示配置名称和包含的模型数量（如 "DeepSeek 官方 (3个模型)"）
- **默认模型选择**：页面加载时自动选择第一个启用的模型配置，或从 localStorage 恢复用户上次选择的模型
- **实时切换支持**：用户可以在对话过程中切换模型，新消息将使用当前选中的模型
- **选中状态持久化**：将用户选择的模型配置 ID 保存到 localStorage，下次打开页面时自动恢复
- **错误处理**：当没有可用的模型配置时，显示友好的提示信息

## Capabilities

### New Capabilities
- `chat-model-selector`: 为 ChatAnalysis 页面提供模型选择器功能，包括获取可用模型配置列表、展示模型选项、处理用户选择、持久化选择状态等能力。

### Modified Capabilities
- `openai-model-frontend`: 扩展现有前端模型配置功能，增加在聊天场景下获取可用模型列表的 API 接口。

## Impact

### 前端影响
- **新增组件**：创建 `ModelSelector.vue` 组件
- **修改页面**：更新 `ChatAnalysis.vue`，集成模型选择器
- **新增服务**：在 `modelApi.ts` 中添加获取已启用模型配置列表的便捷方法
- **路由配置**：无需修改

### 后端影响
- 无需修改后端代码，现有的 `/api/models/configs` 接口已支持通过 `is_active=true` 参数筛选已启用的配置

### 依赖影响
- 使用现有的 Element Plus `el-select` 组件
- 使用现有的 `modelApiService` 服务
- 使用 localStorage 进行状态持久化

### 用户体验影响
- 用户可以在聊天前选择合适的模型
- 支持对话中切换模型，提供更灵活的使用体验
- 选择状态持久化，减少重复操作
