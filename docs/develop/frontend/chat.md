# 即席分析前端聊天消息处理流程

## 服务端消息特征

根据 `docs/develop/modules/chat.md`，服务端返回的消息具有以下特征：

### 消息类型
1. **普通文本消息**：直接包含文本内容
2. **特殊文本消息**：`generate_response` 工具调用，当作文本消息处理
3. **工具调用消息**：`tool_use` 和 `tool_result` 成对出现
4. **消息完成消息**：`message_completed` 标识一个消息的结束
5. **响应完成消息**：`response_completed` 标识整个响应的结束

### 流式返回特征
- **叠加式返回**：每个Server Message都是当前message的完整消息，包含前面的所有内容

## 基本概念定义

### Server Message（服务端消息）

**服务端发送的最小消息单元**：

- **类型**：
  - `message_update` - 消息更新
  - `message_completed` - 消息完成
  - `response_completed` - 响应完成
  - `status` - 状态消息
  - `error` - 错误消息
- **结构**：
  ```json
  {
    "session_id": "session_id",
    "type": "message_update",
    "message": {
      "id": "message_id",
      "content": [...]
    }
  }
  ```

### Display Message

**在UI层面显示的消息块**：

- **定义**：在界面上实际显示的消息块，对应一个逻辑消息
- **特征**：
  - 每个Display Message包含完整的显示内容和交互状态
  - 具有明确的UI边界和视觉效果
  - 对应ChatMessage接口组件
- **显示策略**：
  - 文本Display Message：直接显示最新内容
  - 工具Display Message：显示工具调用和结果的组合内容
  - 空Display Message：自动清理，不占用UI空间

### 状态管理

- **currentMessageId**：当前正在处理的消息ID
- **currentMessageContent**：当前消息的显示内容
- **messages列表**：存储所有ChatMessage的数组
- **isLoading**：加载状态，控制加载指示器显示

### Server Message和Display Message的关系

#### 服务端发送流程
```
用户查询
  ↓
服务端处理
  ↓
Server Message 1 (文本) → Display Message A
  ↓
Server Message 2 (文本) → Display Message A (更新内容)
  ↓
Server Message 3 (message_completed) → Display Message A 完成
  ↓
Server Message 4 (工具调用) → Display Message B
  ↓
Server Message 5 (工具结果) → Display Message B (累积内容)
  ↓
Server Message 6 (message_completed) → Display Message B 完成
  ↓
Server Message 7 (response_completed) → 整个响应完成
```

#### 对应关系表

| Server Message类型 | Display Message类型 | 处理方式 |
|-------------------|---------------------|---------|
| 普通文本 | 文本Display Message | 直接替换内容 |
| generate_response | 文本Display Message | 直接替换内容 |
| 工具调用 | 工具Display Message | 创建新显示块 |
| 工具结果 | 工具Display Message | 累积到现有显示块 |
| message_completed | - | 标记消息完成 |
| response_completed | - | 标记整个响应完成 |

## 前端消息处理逻辑

### 详细处理流程

#### 1. 消息处理流程

当接收到新的Server Message时，统一处理逻辑，根据消息包的类型执行相应的处理：

**统一处理逻辑（适用于 message_update 和 message_completed）**：
1. 检查消息类型是否为内容类型（message_update 或 message_completed）
2. 遍历消息包中的每个内容块
3. 为每个内容块生成独立的消息ID

   **如果是新的内容块**：
   1. 解析该内容块，获取初始内容
   2. 创建包含初始内容的新DisplayMessage
   3. 设置消息的messageId为生成的内容块唯一标识
   4. 将新消息添加到消息列表中
   5. 将消息ID和消息索引添加到索引缓存

   **如果是现有的内容块**：
   1. 根据消息类型（文本Message或工具Message）采用相应的内容处理策略
   2. 通过索引缓存找到对应的DisplayMessage
   3. 更新该消息的内容

4. 如果消息类型为 message_completed，额外执行：
   - 遍历消息包中的每个内容块
   - 通过messageId在消息列表中查找对应的消息
   - 标记每个Message为完成状态
   - 从索引缓存中移除对应的消息ID

**如果是响应完成类型消息包（response_completed）**：
1. 停止加载状态显示
2. 如果当前有未完成的Message，先完成该Message
3. 清空当前消息ID
4. 执行全面的空消息清理，移除消息列表中所有空内容的消息
5. 确保最终界面显示干净整洁，没有残留的空Message

**如果是状态或错误类型消息包（status, error）**：
1. 根据消息类型显示相应的提示信息
2. 不影响当前的Message处理状态

#### 2. 消息ID生成

消息ID的生成遵循以下规则：

遍历消息包数组中的每个内容块，为每个内容块生成独立的消息ID：

- **文本内容**：使用 `text_` + `message.id` + `_$index` 作为唯一标识（index为内容块在数组中的位置）
- **特殊文本消息**（generate_response工具调用）：当作文本消息处理，使用 `text_` + `message.id` + `_$index` 作为唯一标识
- **工具调用**：使用 `tool_` + `message.content.id` 作为唯一标识
- **工具结果**：使用 `tool_` + `message.content.id` 作为唯一标识（与对应的工具调用相同）

**索引缓存机制**：
- 维护一个消息ID到DisplayMessage索引的映射缓存
- 当收到新的Server Message时，通过内容块的唯一标识在缓存中查找对应的DisplayMessage
- 如果找到对应的消息，则更新该消息的内容
- 如果未找到对应的消息，则创建新的DisplayMessage并添加到缓存

这样可以确保：
1. 每个内容块都有独立的DisplayMessage
2. 工具调用和工具结果能够正确匹配
3. 文本消息能够正确更新

#### 3. 内容更新处理

根据消息ID的类型采用不同的内容处理策略：

**工具Message处理（消息ID以tool_开头）**：
- 采用累积策略，因为工具调用和工具结果是服务端返回的两个不同Server Message
- 如果当前内容和新的内容都有实际内容，检查新内容是否已包含在当前内容中
- 如果新内容未被包含，则将新内容追加到当前内容中（用换行符分隔）
- 否则直接替换为新内容

**文本Message处理（消息ID以text_开头）**：
- 采用直接替换策略，因为服务端采用叠加式返回
- 每个Server Message都包含前面的所有内容，所以直接替换为最新内容即可
- 这样避免重复显示，确保只显示最终的完整内容

**多内容块处理**：
- 当收到包含多个内容块的Server Message时，遍历每个内容块
- 为每个内容块生成独立的消息ID
- 使用索引缓存查找对应的DisplayMessage
- 如果找到对应的消息，则更新该消息的内容
- 如果未找到对应的消息，则创建新的DisplayMessage并添加到缓存

**索引缓存机制**：
- 维护一个`messageIdToIndex`映射，存储消息ID到DisplayMessage索引的对应关系
- 当创建新消息时，将消息ID和消息索引添加到缓存
- 当更新消息时，通过消息ID快速查找对应的DisplayMessage
- 当消息完成时，从缓存中移除对应的消息ID

处理完内容更新后，调用显示更新函数来刷新界面。

#### 4. 内容解析

内容解析将服务端返回的复杂消息包结构转换为前端显示的文本格式：

遍历消息包数组中的每个块：
- **文本块**：直接追加文本内容
- **generate_response工具调用**：特殊处理，直接显示响应内容，不显示工具调用信息
- **其他工具调用**：显示工具图标和工具名称
- **工具结果**：显示工具名称和成功状态，不显示详细的输出文本

最终返回解析后的内容文本，去除首尾空白字符。

### 消息显示示例

#### 文本消息处理流程
```
服务端Server Message 1: "你好"
  → 消息ID: text_msg1
  → 消息内容: "你好"

服务端Server Message 2: "你好，世界" (包含前面的"你好")
  → 消息ID: text_msg1 (相同)
  → 消息内容: "你好，世界" (直接替换上一个)

服务端Server Message 3: "你好，世界！" (包含前面的所有内容)
  → 消息ID: text_msg1 (相同)
  → 消息内容: "你好，世界！" (直接替换上一个)

服务端Server Message 4 (message_completed)
  → 消息ID: text_msg1 (完成)
  → 消息内容: "你好，世界！" (最终内容)
  → 清理消息状态

最终显示：1个文本Message
```

#### 工具消息处理流程
```
服务端工具调用Server Message (包含多个工具调用):
  → 内容块1: "🔧 工具调用: execute_python_code"
    → 消息ID: tool_call_123
    → 消息内容: "🔧 工具调用: execute_python_code"
  → 内容块2: "🔧 工具调用: execute_python_code_2"
    → 消息ID: tool_call_456
    → 消息内容: "🔧 工具调用: execute_python_code_2"

服务端工具结果Server Message (包含多个工具结果):
  → 内容块1: "✅ execute_python_code 工具调用成功"
    → 消息ID: tool_call_123 (相同)
    → 消息内容:
      "🔧 工具调用: execute_python_code"
      "✅ execute_python_code 工具调用成功" (累积显示)
  → 内容块2: "✅ execute_python_code_2 工具调用成功"
    → 消息ID: tool_call_456 (相同)
    → 消息内容:
      "🔧 工具调用: execute_python_code_2"
      "✅ execute_python_code_2 工具调用成功" (累积显示)

服务端Server Message (message_completed)
  → 标记所有消息完成，清理消息状态

最终显示：2个工具Message（每个包含对应的工具调用和结果）
```

#### 混合消息处理流程
```
服务端Server Message (包含文本和工具调用):
  → 内容块1: "我需要分析数据"
    → 消息ID: text_msg1_0
    → 消息内容: "我需要分析数据"
  → 内容块2: "🔧 工具调用: execute_python_code"
    → 消息ID: tool_call_123
    → 消息内容: "🔧 工具调用: execute_python_code"

服务端Server Message (更新文本内容):
  → 内容块1: "我需要分析数据，请稍等"
    → 消息ID: text_msg1_0 (相同)
    → 消息内容: "我需要分析数据，请稍等" (直接替换)

服务端Server Message (工具结果):
  → 内容块1: "✅ execute_python_code 工具调用成功"
    → 消息ID: tool_call_123 (相同)
    → 消息内容:
      "🔧 工具调用: execute_python_code"
      "✅ execute_python_code 工具调用成功" (累积显示)

服务端Server Message (message_completed)
  → 标记所有消息完成，清理消息状态

最终显示：1个文本Message + 1个工具Message

## 模型选择器组件

### 组件概述

`ModelSelector` 是一个独立的 Vue 3 组件，用于在聊天界面中选择 AI 模型配置。

**文件位置**: `frontend/src/components/ModelSelector.vue`

### 功能特性

1. **模型配置展示**
   - 自动获取所有已启用的模型配置
   - 显示配置名称和包含的模型数量
   - 格式：`<配置名称> (<N>个模型)`

2. **状态持久化**
   - 使用 localStorage 保存用户选择的模型配置
   - 存储键名：`chat-selected-model-config-id`
   - 页面刷新后自动恢复上次选择

3. **智能默认选择**
   - 优先恢复用户上次选择的模型
   - 如果上次选择无效，默认选择第一个可用模型
   - 验证保存的模型 ID 是否仍在可用列表中

4. **错误处理**
   - 网络错误时显示友好提示
   - 提供重试按钮
   - 加载状态显示

5. **响应式设计**
   - 支持移动端显示
   - 最大宽度 840px，与聊天界面保持一致
   - 自动截断过长的配置名称（超过 30 字符）

### 组件接口

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

### 使用示例

```vue
<template>
  <ModelSelector
    placeholder="选择 AI 模型"
    @update:selectedModelId="handleModelChange"
  />
</template>

<script setup lang="ts">
import ModelSelector from '@/components/ModelSelector.vue'

const handleModelChange = (modelId: number) => {
  console.log('选中的模型配置 ID:', modelId)
  // TODO: 将模型配置 ID 传递给后端聊天接口
}
</script>
```

### 数据获取

组件通过 `modelApiService.getActiveModelConfigs()` 方法获取已启用的模型配置：

- **API 端点**: `/api/models/configs?is_active=true&page_size=100`
- **调用时机**: 组件 `onMounted` 生命周期钩子
- **无缓存策略**: 每次进入页面都重新获取最新数据

### 状态管理

组件内部维护以下响应式状态：

```typescript
const modelConfigs = ref<ModelConfig[]>([])      // 模型配置列表
const selectedModelId = ref<number | null>(null) // 当前选中的 ID
const isLoading = ref<boolean>(false)             // 加载状态
const error = ref<string | null>(null)            // 错误信息
```

### 样式定制

组件使用以下 CSS 类名：

- `.model-selector` - 容器
- `.model-selector-select` - 选择器
- `.option-text` - 选项文本
- `.model-selector-error` - 错误提示区域
- `.error-message` - 错误消息文本

可以通过覆盖这些类名来自定义样式。

### 与 ChatAnalysis 页面的集成

模型选择器已集成到 `ChatAnalysis.vue` 页面中：

- 位置：页面顶部，消息列表上方
- 布局：居中显示，最大宽度 840px
- 事件：监听 `@update:selectedModelId` 事件

**注意**: 当前实现仅保存用户选择到组件状态，尚未将选中的模型配置 ID 传递给后端聊天接口。这是为未来功能预留的扩展点。

```
