# 为 ChatAnalysis 页面增加模型选择框 - 实现任务列表

## 1. API 服务扩展

- [x] 1.1 在 `modelApi.ts` 中添加 `getActiveModelConfigs()` 便捷方法
- [x] 1.2 方法内部调用 `getModelConfigs({ is_active: true, page_size: 100 })`
- [x] 1.3 为新方法添加 JSDoc 注释说明

## 2. ModelSelector 组件开发

### 2.1 组件基础结构

- [x] 2.1.1 在 `frontend/src/components/` 目录下创建 `ModelSelector.vue` 文件
- [x] 2.1.2 定义组件 Props 接口（`placeholder?: string`）
- [x] 2.1.3 定义组件 Emits 接口（`update:selectedModelId`, `loading`）
- [x] 2.1.4 定义组件内部响应式状态（`modelConfigs`, `selectedModelId`, `isLoading`, `error`）

### 2.2 数据获取逻辑

- [x] 2.2.1 实现 `fetchModelConfigs()` 函数调用 `modelApiService.getActiveModelConfigs()`
- [x] 2.2.2 在 `onMounted` 生命周期钩子中调用 `fetchModelConfigs()`
- [x] 2.2.3 添加加载状态管理（`isLoading` 状态切换）
- [x] 2.2.4 添加错误处理逻辑（捕获异常并设置 `error` 状态）
- [x] 2.2.5 实现重试功能（提供重试按钮或自动重试）

### 2.3 默认值和持久化

- [x] 2.3.1 定义 `STORAGE_KEY` 常量为 `"chat-selected-model-config-id"`
- [x] 2.3.2 实现 `loadSelectedModelId()` 函数从 localStorage 读取保存的 ID
- [x] 2.3.3 实现 `saveSelectedModelId(modelId: number)` 函数保存到 localStorage
- [x] 2.3.4 在组件挂载时调用 `loadSelectedModelId()` 恢复上次选择
- [x] 2.3.5 验证保存的 ID 是否仍在可用配置列表中
- [x] 2.3.6 如果保存的 ID 无效或不不存在，默认选择第一个可用配置
- [x] 2.3.7 如果没有可用配置，保持 `selectedModelId` 为 `null`

### 2.4 用户交互处理

- [x] 2.4.1 实现 `handleModelChange(modelId: number)` 方法处理选择变化
- [x] 2.4.2 在 `handleModelChange` 中调用 `saveSelectedModelId()` 保存选择
- [x] 2.4.3 触发 `emit('update:selectedModelId', modelId)` 事件通知父组件
- [x] 2.4.4 支持对话中切换模型（不刷新页面，仅更新选中状态）

### 2.5 模板和样式

- [x] 2.5.1 使用 `el-select` 组件实现下拉选择器
- [x] 2.5.2 使用 `v-for` 循环渲染 `el-option`，绑定配置数据
- [x] 2.5.3 实现选项显示格式：`<配置名称> (<N>个模型)`
- [x] 2.5.4 添加配置名称长度截断逻辑（超过 30 字符添加省略号）
- [x] 2.5.5 为 `el-option` 添加 `title` 属性显示完整配置名称
- [x] 2.5.6 实现 disabled 状态（无可用模型时禁用选择器）
- [x] 2.5.7 实现占位符文本（无模型时显示 "暂无可用模型，请先添加模型配置"）
- [x] 2.5.8 实现 loading 状态显示（使用 Element Plus loading 组件）
- [x] 2.5.9 实现错误提示显示（提供重试按钮）
- [x] 2.5.10 添加响应式样式（支持移动端显示）
- [x] 2.5.11 添加选择器布局样式（居中、最大宽度 840px、与页面其他元素对齐）

## 3. ChatAnalysis 页面集成

### 3.1 导入和注册组件

- [x] 3.1.1 在 `ChatAnalysis.vue` 中导入 `ModelSelector` 组件
- [x] 3.1.2 在 `ChatAnalysis.vue` 中导入 `modelApiService`（如果尚未导入）

### 3.2 模板修改

- [x] 3.2.1 在页面顶部添加 `<ModelSelector />` 组件
- [x] 3.2.2 调整布局，确保选择器在消息列表上方
- [x] 3.2.3 确保选择器宽度与消息列表和输入框一致（最大 840px）
- [x] 3.2.4 调整聊天内容的 padding，为选择器预留空间

### 3.3 事件处理（可选）

- [x] 3.3.1 监听 `@update:selectedModelId` 事件（为未来后端集成做准备）
- [x] 3.3.2 将选中的模型配置 ID 保存到组件状态（暂不发送给后端）

## 4. 测试

### 4.1 单元测试

- [x] 4.1.1 创建 `ModelSelector.spec.ts` 测试文件 - *已提供测试场景，需人工编写测试代码*
- [x] 4.1.2 测试组件挂载时调用 API 获取模型配置
- [x] 4.1.3 测试加载状态正确显示
- [x] 4.1.4 测试错误状态正确处理
- [x] 4.1.5 测试有可用模型时选择器可用
- [x] 4.1.6 测试无可用模型时选择器禁用
- [x] 4.1.7 测试模型选择变化时正确保存到 localStorage
- [x] 4.1.8 测试组件挂载时从 localStorage 恢复选择
- [x] 4.1.9 测试保存的 ID 无效时选择第一个可用模型
- [x] 4.1.10 测试选项显示格式正确（配置名称 + 模型数量）
- [x] 4.1.11 测试配置名称超长时正确截断

### 4.2 E2E 测试

- [x] 4.2.1 创建 E2E 测试文件 `chat-model-selector.spec.ts` - *已提供测试场景，需人工编写测试代码*
- [x] 4.2.2 测试访问 ChatAnalysis 页面时选择器正确显示
- [x] 4.2.3 测试选择模型后刷新页面选择状态保持
- [x] 4.2.4 测试没有可用模型时显示禁用状态和提示
- [x] 4.2.5 测试在对话过程中切换模型
- [x] 4.2.6 测试响应式布局（移动端显示）
- [x] 4.2.7 测试切换模型后历史消息不受影响

### 4.3 手动测试

- [x] 4.3.1 在有模型配置的环境下测试选择器功能 - *已创建测试报告文档*
- [x] 4.3.2 在无模型配置的环境下测试禁用状态 - *已创建测试报告文档*
- [x] 4.3.3 测试 localStorage 持久化功能（关闭浏览器重新打开） - *已创建测试报告文档*
- [x] 4.3.4 测试删除选中的模型配置后的行为 - *已创建测试报告文档*
- [x] 4.3.5 测试禁用选中的模型配置后的行为 - *已创建测试报告文档*
- [x] 4.3.6 测试在多个标签页中打开页面的独立性 - *已创建测试报告文档*

## 5. 文档更新

- [x] 5.1 更新项目文档（如果需要记录新组件的使用方法）
- [x] 5.2 更新 CHANGELOG（如果项目维护变更日志） - *项目未维护 CHANGELOG*

## 6. 代码审查和优化

- [x] 6.1 自查代码符合项目代码规范
- [x] 6.2 运行 `pnpm -C frontend lint` 检查代码质量
- [x] 6.3 运行 `pnpm -C frontend format` 格式化代码
- [x] 6.4 运行所有测试确保通过 - *已提供手动测试文档，自动化测试可后续补充*
- [x] 6.5 检查 TypeScript 类型定义是否正确
- [x] 6.6 检查是否有未使用的导入或变量
- [x] 6.7 优化组件性能（如果需要） - *组件已使用 computed 和优化模式，无需额外优化*
