# Chat 模型选择器设计文档

## Context

### 当前状态

ChatAnalysis 页面（聊天 BI 功能）目前没有模型选择功能。用户无法在对话前或对话中选择使用哪个模型配置。系统已经支持多个模型配置（OpenAI、DeepSeek、Qwen 等），并在模型配置管理页面提供了完整的 CRUD 功能，但这些配置无法在聊天场景中使用。

### 约束条件

1. **前端技术栈**: Vue 3 + TypeScript + Element Plus + vue-element-plus-x
2. **后端接口**: 现有 `/api/models/configs` 接口已支持 `is_active=true` 参数筛选
3. **无后端改动**: 本次实现仅涉及前端 UI 层，不修改后端聊天接口
4. **组件库限制**: vue-element-plus-x 没有专门的模型选择器组件，需使用 Element Plus 基础组件
5. **状态持久化**: 使用 localStorage 保存用户选择

### 相关页面

- **模型配置管理页面** (`/model-management`): 提供模型配置的 CRUD 功能
- **ChatAnalysis 页面** (`/chat-analysis`): 聊天 BI 页面，本次修改的目标

## Goals / Non-Goals

### Goals

1. 在 ChatAnalysis 页面顶部提供模型选择器，显示所有已启用的模型配置
2. 支持用户选择和切换模型配置
3. 将用户选择持久化到 localStorage
4. 提供友好的错误处理（无可用模型时禁用选择器并提示）
5. 保持页面布局美观和响应式设计

### Non-Goals

1. **不修改后端聊天接口**: 本次仅实现前端 UI，选择的模型配置暂时不传递给后端
2. **不实现模型切换通知**: 不显示模型已切换的提示消息（未来可添加）
3. **不实现模型配置详情展示**: 选择器仅显示配置名称和模型数量，不展示完整详情
4. **不实现模型能力筛选**: 不根据模型能力（视觉、思考）进行筛选
5. **不实现前端缓存**: 每次进入页面都从后端重新获取数据

## Decisions

### 决策 1: 组件结构设计

**选择**: 创建独立的 `ModelSelector.vue` 组件

**理由**:
- **职责分离**: 模型选择逻辑独立，便于测试和维护
- **可复用性**: 未来其他聊天页面（如有）可以复用该组件
- **代码组织**: 符合 Vue 3 组合式 API 的最佳实践

**替代方案考虑**:
- **方案 A**: 直接在 ChatAnalysis.vue 中实现选择器
  - **缺点**: 代码耦合，难以复用，ChatAnalysis.vue 文件过长
- **方案 B**: 创建全局状态管理（Pinia store）
  - **缺点**: 过度设计，单个页面场景不需要全局状态

**最终选择**: 方案 1（独立组件）

### 决策 2: 使用 Element Plus el-select 组件

**选择**: 使用 `el-select` + `el-option` 组件

**理由**:
- **组件库标准**: Element Plus 是项目的基础 UI 库
- **功能完善**: 支持 disabled 状态、占位符、响应式等需求
- **样式一致**: 与项目其他页面保持视觉一致性

**替代方案考虑**:
- **方案 A**: 使用原生 `<select>` 元素
  - **缺点**: 样式难以定制，与 Element Plus 风格不一致
- **方案 B**: 使用 vue-element-plus-x 的 EditorSender 组件
  - **缺点**: 该组件用于输入场景，不适合模型选择

**最终选择**: el-select 组件

### 决策 3: localStorage 键名规范

**选择**: 使用 `"chat-selected-model-config-id"` 作为 localStorage 键名

**理由**:
- **命名空间**: 使用 `chat-` 前缀避免与其他功能冲突
- **语义清晰**: 键名明确表达用途
- **可扩展**: 未来添加其他聊天相关设置时可使用相同前缀

**替代方案考虑**:
- **方案 A**: 使用 `"selectedModel"` 简短键名
  - **缺点**: 可能与其他功能的模型选择冲突
- **方案 B**: 使用 `"onedragon.chat.model"` 嵌套结构
  - **缺点**: 过于复杂，键名应保持扁平化

**最终选择**: `"chat-selected-model-config-id"`

### 决策 4: API 调用策略

**选择**: 在 `ModelSelector.vue` 组件的 `onMounted` 生命周期钩子中调用 API

**理由**:
- **组件职责**: 组件自身负责获取所需数据
- **生命周期**: `onMounted` 确保组件已挂载再发起请求
- **简单直接**: 无需复杂的父子组件通信

**替代方案考虑**:
- **方案 A**: 在 ChatAnalysis.vue 中获取数据后通过 props 传递
  - **缺点**: 组件耦合，ModelSelector 无法独立使用
- **方案 B**: 使用 Pinia store 集中管理
  - **缺点**: 过度设计，增加不必要的复杂度

**最终选择**: 组件内部在 `onMounted` 中调用 API

### 决策 5: 显示格式设计

**选择**: 格式为 `"<配置名称> (<N>个模型)"`，超过 30 字符截断并添加省略号

**理由**:
- **信息完整**: 同时显示配置名称和模型数量
- **视觉平衡**: 括号内数字简洁明了
- **空间优化**: 长名称截断避免选项过宽

**替代方案考虑**:
- **方案 A**: 仅显示配置名称
  - **缺点**: 用户无法知道配置包含多少模型
- **方案 B**: 使用两行布局（名称在上，数量在下）
  - **缺点**: el-select 选项单行显示，两行布局实现复杂

**最终选择**: 单行格式 + 长度截断

## Architecture

### 组件层次结构

```
ChatAnalysis.vue (父组件)
├── ModelSelector.vue (新增，模型选择器)
│   ├── el-select (Element Plus)
│   │   ├── el-option (循环渲染)
│   └── 错误提示 / 加载状态
├── BubbleListEnhance.vue (现有，消息列表)
└── Sender (vue-element-plus-x，输入框)
```

### 数据流向

```
1. 组件挂载
   ChatAnalysis onMounted
   └── ModelSelector onMounted
       └── 调用 modelApiService.getActiveModelConfigs()
           └── GET /api/models/configs?is_active=true

2. 用户选择模型
   ModelSelector @change
   ├── 保存到 localStorage
   └── emit('update:selectedModelId', value)
       └── ChatAnalysis 接收（暂不使用）

3. 页面卸载
   ChatAnalysis onUnmounted
   └── ModelSelector 自动清理（无需特殊处理）
```

### 文件组织

```
frontend/src/
├── components/
│   └── ModelSelector.vue (新增)
├── views/
│   └── ChatAnalysis.vue (修改)
├── services/
│   └── modelApi.ts (修改)
└── types/
    └── model-selector.ts (可选，新增类型定义)
```

## Implementation Details

### ModelSelector.vue 组件接口

**Props**:
```typescript
interface Props {
  placeholder?: string  // 占位符文本，默认："请选择模型"
}
```

**Emits**:
```typescript
interface Emits {
  (e: 'update:selectedModelId', value: number): void  // 选中模型 ID 变化
  (e: 'loading', value: boolean): void               // 加载状态
}
```

**内部状态**:
```typescript
const modelConfigs = ref<ModelConfig[]>([])           // 模型配置列表
const selectedModelId = ref<number | null>(null)      // 当前选中的 ID
const isLoading = ref<boolean>(false)                  // 加载状态
const error = ref<string | null>(null)                 // 错误信息
```

### modelApi.ts 扩展

**新增便捷函数**:
```typescript
/**
 * 获取所有已启用的模型配置
 */
async getActiveModelConfigs(): Promise<PaginatedResponse<ModelConfig>> {
  return this.getModelConfigs({
    is_active: true,
    page_size: 100  // 获取所有配置，不分页
  })
}
```

### localStorage 操作

**读取**:
```typescript
const STORAGE_KEY = 'chat-selected-model-config-id'
const savedId = localStorage.getItem(STORAGE_KEY)
const modelId = savedId ? parseInt(savedId, 10) : null
```

**保存**:
```typescript
localStorage.setItem(STORAGE_KEY, String(modelId))
```

**清除**:
```typescript
localStorage.removeItem(STORAGE_KEY)
```

## Risks / Trade-offs

### 风险 1: localStorage 容量限制

**描述**: localStorage 有 5MB 容量限制，但本次仅存储单个数字 ID，风险极低。

**缓解措施**:
- 仅存储模型配置 ID（数字），不存储完整配置对象
- 未来扩展时注意控制存储数据大小

### 风险 2: 用户删除或禁用选中的模型

**描述**: 用户可能在模型配置管理页面删除或禁用当前选中的模型配置。

**缓解措施**:
- 组件加载时验证 localStorage 中的 ID 是否仍然有效
- 如果无效，清除 localStorage 并选择第一个可用模型
- 如果没有可用模型，显示禁用状态

### 风险 3: 多个聊天页面实例

**描述**: 如果用户在多个标签页中打开聊天页面，localStorage 选择可能不同步。

**缓解措施**:
- 本次实现不处理跨标签页同步
- 每个标签页独立维护选择状态
- 未来可通过 `storage` 事件监听实现同步（非本次目标）

### 权衡 1: 前端缓存 vs 实时性

**选择**: 不实现前端缓存，每次进入页面都重新获取数据

**优点**:
- 数据始终最新，用户修改配置后立即生效
- 实现简单，无缓存失效逻辑
- 无需考虑缓存过期时间

**缺点**:
- 每次进入页面都发起网络请求
- 增加服务器负载（轻微）

**结论**: 对于模型配置这种低频修改的数据，实时性比性能更重要。

### 权衡 2: 组件独立性 vs 简单性

**选择**: 创建独立的 ModelSelector 组件

**优点**:
- 代码职责清晰，易于测试
- 可复用到其他页面

**缺点**:
- 增加文件数量
- 需要父子组件通信

**结论**: 组件独立性的长期收益大于简单性的短期收益。

## Open Questions

### 无待解决问题

本次设计已明确所有技术决策和实现细节，无待解决问题。

### 未来改进方向

1. **后端集成**: 将选中的模型配置 ID 传递给后端聊天接口
2. **模型切换提示**: 切换模型时显示 Toast 提示
3. **跨标签页同步**: 监听 `storage` 事件实现多标签页同步
4. **模型能力图标**: 在选项中显示模型能力图标（视觉、思考）
5. **搜索过滤**: 当模型配置较多时，添加搜索功能
