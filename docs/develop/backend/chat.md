# 聊天

当前只支持流式响应。

## 消息类型说明

按照最外层的 `type` 字段区分基础类型。

### 连接状态消息

`type="status"`

```json
{
    "session_id": "session_id",
    "type": "status",
    "message": {
        "hint": "connected"
    }
}
```

### 处理错误消息

`type="error"`

```json
{
    "session_id": "session_id",
    "type": "error",
    "message": {
        "hint": "Internal Server Error(500)"
    }
}
```

### 响应内容消息

对于单次输入，智能体会返回若干条消息。

流式响应时，每次返回一条消息的内容，分位以下两种类型：

- `type="message_update"` - 更新一条消息的内容，是当前最新的完整内容。
- `type="message_completed"` - 标记一条消息的结束，也包含当前最新的完整内容。

#### 普通文本消息

`message.content.type="text"`

```json
{
    "session_id": "session_id",
    "type": "message_update",
    "message": {
        "id": "message_id",
        "name": "OneDragon",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "我很好，谢谢关心！"
            }
        ],
        "metadata": null,
        "timestamp": "2025-09-15 18:17:51.641"
    }
}
```

#### 特殊文本消息

AgentScope的ReAct智能体，会在大模型没有产生任何工具调用，只产生了文本输出时，将文本输出转成generate_response的工具调用。

这类消息应该当做文本消息处理。

`message.content.type = "tool_use" and message.content.name = "generate_response"` 

```json
{
    "session_id": "session_id",
    "type": "message_update",
    "message": {
        "id": "message_id",
        "name": "OneDragon",
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "tool_call_id",
                "name": "generate_response",
                "input": {
                    "response": "我很好，谢谢关心！"
                }
            }
        ],
        "metadata": null,
        "timestamp": "2025-09-15 18:18:23.152"
    }
}
```

#### 工具调用消息

可能有多个 `meesage.content.type="tool_use"` 的工具调用消息，代表并行工具调用。

最多有一个 `meesage.content.type="text"` 的文本提示消息。

注意需要忽略 `message.content.name = "generate_response"` 的特殊文本消息。

```json
{
    "session_id": "session_id",
    "type": "message_completed",
    "message": {
        "id": "message_id_1",
        "name": "OneDragon",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "我需要先获取“东财”对应的股票代码和名称，然后再进行分析。"
            },
            {
                "type": "tool_use",
                "id": "call_tool_id_1",
                "name": "tushare_stock_basic_by_name_like",
                "input": {
                    "name_like": "东财"
                }
            },
            {
                "type": "tool_use",
                "id": "call_tool_id_2",
                "name": "tushare_stock_basic_by_name_like",
                "input": {
                    "name_like": "同花顺"
                }
            }
        ],
        "metadata": null,
        "timestamp": "2025-09-22 10:19:30.709"
    }
}
```

#### 工具结果消息

`message.content.type = "tool_result"`，可能有多个，代表并行工具调用。

工具结果消息 与 工具调用消息的 `message.id` 不相同，`message.content.id` 相同。

```json
{
    "session_id": "session_id",
    "type": "message_completed",
    "message": {
        "id": "message_id_2",
        "name": "system",
        "role": "system",
        "content": [
            {
                "type": "tool_result",
                "id": "call_tool_id_1",
                "name": "tushare_stock_basic_by_name_like",
                "output": [
                    {
                        "type": "text",
                        "text": "[{\"ts_code\":\"300059.SZ\",\"股票名称\":\"东方财富\"}]"
                    }
                ]
            },
            {
                "type": "tool_result",
                "id": "call_tool_id_2",
                "name": "tushare_stock_basic_by_name_like",
                "output": [
                    {
                        "type": "text",
                        "text": "[{\"ts_code\":\"300033.SZ\",\"股票名称\":\"同花顺\"}]"
                    }
                ]
            }
        ],
        "metadata": null,
        "timestamp": "2025-09-22 10:19:31.011"
    }
}
```

#### 特殊工具 display_analyse_by_code_result

该工具调用是为了给客户端发送一个可以显示分析结果的消息。

工具调用

```json
{
    "session_id": "session_id",
    "type": "message_completed",
    "message": {
        "id": "message_id_1",
        "name": "OneDragon",
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "call_tool_id",
                "name": "display_analyse_by_code_result",
                "input": {
                    "analyse_id": 1
                }
            }
        ],
        "metadata": null,
        "timestamp": "2025-09-22 14:25:02.473"
    }
}
```

工具结果

```json
{
    "session_id": "session_id",
    "type": "message_completed",
    "message": {
        "id": "message_id_2",
        "name": "system",
        "role": "system",
        "content": [
            {
                "type": "tool_result",
                "id": "call_tool_id",
                "name": "display_analyse_by_code_result",
                "output": [
                    {
                        "type": "text",
                        "text": "{\"analyse_i\"': 1}"
                    }
                ]
            }
        ],
        "metadata": null,
        "timestamp": "2025-09-22 09:59:28.540"
    }
}
```

客户端收到调用结果后，可以调用 `/chat/get_analyse_by_code_result` 接口获取

### 响应完成消息

`type="response_completed"`

该消息没有任何实际内容，仅标记一轮响应(若干条消息)的结束。

```json
{
    "session_id": "session_id",
    "type": "response_completed",
    "message": {}
}
```

## 消息包发送顺序

### 文本消息流程
```
用户查询
  ↓
服务端处理
  ↓
消息 1 (文本) → 消息 A
  ↓
消息 2 (文本) → 消息 A (更新内容)
  ↓
消息 3 (文本) → 消息 A (更新内容)
  ↓
消息 4 (MESSAGE_COMPLETED) → 消息 A 完成
  ↓
消息 5 (RESPONSE_COMPLETED) → 整个响应完成
```

### 工具消息流程
```
用户查询
  ↓
服务端处理
  ↓
消息 1 (工具调用) → 消息 B1
  ↓
消息 2 (工具结果) → 消息 B2 (合并显示工具调用结果)
  ↓
消息 3 (MESSAGE_COMPLETED) → 消息 B 完成
  ↓
消息 4 (文本) → 消息 A
  ↓
消息 5 (MESSAGE_COMPLETED) → 消息 A 完成
  ↓
消息 6 (RESPONSE_COMPLETED) → 整个响应完成
```


## 接口说明

### /chat/get_analyse_by_code_result

- 方法 POST
- Body JSON
- 所需字段 `analyse_id`
- 请求结果，一个JSON对象，包含
  - echarts_list: 一个数组，每个元素是一个标准的Echarts数据结果，可以用于展示图表。

请求参数示例：

```json
{ "analyse_id": 1 }
```

请求结果示例:
```json
{
  "echarts_list": []
}
```

### /chat/stream

- 方法 POST
- 流式响应（Server-Sent Events）
- 必须提供 `model_config_id` 和 `model_id` 参数

#### 请求参数

```json
{
  "session_id": "session_id_123",  // 可选，不提供则创建新会话
  "user_input": "你好，请分析贵州茅台的股价",
  "model_config_id": 1,            // 必填，模型配置 ID
  "model_id": "gpt-4"               // 必填，配置中的模型 ID
}
```

**字段说明：**
- `session_id`：会话 ID，可选。如果不提供，系统会创建一个新会话并返回在响应中。
- `user_input`：用户输入的文本内容。
- `model_config_id`：模型配置 ID，必填。必须是数据库中已存在的配置 ID。
- `model_id`：模型 ID，必填。必须是指定配置的 `models` 数组中的一个。

#### 错误响应

**400 Bad Request - 配置已禁用**
```json
{
  "detail": "模型配置 'Test Config' 已禁用"
}
```

**400 Bad Request - 模型 ID 不在配置中**
```json
{
  "detail": "模型 ID 'invalid-model' 不在配置 'Test Config' 中。可用模型: ['gpt-4', 'gpt-4-turbo']"
}
```

**404 Not Found - 配置不存在**
```json
{
  "detail": "配置不存在"
}
```

#### 使用示例

**1. 发送聊天请求**
```bash
curl -X POST http://localhost:21003/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "分析贵州茅台最近一个月的股价走势",
    "model_config_id": 1,
    "model_id": "gpt-4"
  }'
```

**2. 在同一会话中切换模型**
```bash
# 第一次请求使用 gpt-4
curl -X POST http://localhost:21003/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "user_input": "你好",
    "model_config_id": 1,
    "model_id": "gpt-4"
  }'

# 第二次请求切换到 gpt-4-turbo（同一配置，不同模型）
curl -X POST http://localhost:21003/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "user_input": "继续分析",
    "model_config_id": 1,
    "model_id": "gpt-4-turbo"
  }'

# 第三次请求切换到不同的配置
curl -X POST http://localhost:21003/chat/stream \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "session_123",
    "user_input": "用另一个模型重新分析",
    "model_config_id": 2,
    "model_id": "qwen-max"
  }'
```

**注意：**
- 每次切换 `model_config_id` 或 `model_id` 时，系统会重新创建 AI Agent。
- 如果 `model_config_id` 和 `model_id` 都与上次请求相同，系统会复用现有 Agent，避免不必要的重建开销。
- 模型配置和模型 ID 的有效性会在请求开始时验证，无效请求会立即返回错误。