<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import BubbleListEnhance from '../components/BubbleListEnhance.vue'
import { Sender } from 'vue-element-plus-x'
import { chatHttpService } from '../services/chatHttp'
import { getApiBaseUrl } from '../config/api'
import axios from 'axios'

import type {
  BubbleListItemProps,
  BubbleListProps
} from 'vue-element-plus-x/types/BubbleList';
import type { EnhancedMessage } from '../components/BubbleListEnhance.vue';

// EnhancedMessage工厂函数
const createEnhancedMessage = (config: {
  content: string;
  role: 'user' | 'assistant';
  messageType?: 'text' | 'chart';
  chartData?: any;
  analyseId?: string;
  messageId?: string;
  typing?: boolean | { step: number; interval: number };
  maxWidth?: string;
}): EnhancedMessage => {
  const {
    content,
    role,
    messageType = 'text',
    chartData,
    analyseId,
    messageId,
    typing = false,
    maxWidth = '100%'
  } = config;

  const isUser = role === 'user';
  const baseMessage: EnhancedMessage = {
    content,
    role,
    placement: isUser ? 'end' : 'start',
    isMarkdown: role === 'assistant',
    variant: 'outlined',
    messageType,
    chartData,
    analyseId,
    typing,
    maxWidth,
  };

  // 助手消息的特定属性
  if (role === 'assistant' && messageId) {
    baseMessage.messageId = messageId;
  }

  return baseMessage;
};

const messages = ref<EnhancedMessage[]>([])
const inputMessage = ref('')
const isLoading = ref(false)
const hasError = ref(false)
// 移除 WebSocket URL，使用 HTTP SSE

// 索引缓存：消息ID到DisplayMessage索引的映射
const messageIdToIndex = ref<Record<string, number>>({})

// 计算Sender组件的状态
const senderState = computed(() => {
  if (hasError.value) return 'error'
  return 'default'
})


// 为内容块生成唯一的消息ID
const generateMessageId = (content: any, contentIndex: number, message: any): string => {
  if (content.type === 'tool_use' || content.type === 'tool_result') {
    // 工具调用和结果使用工具调用ID
    return `tool_${content.id}`
  } else if (content.type === 'text') {
    // 文本内容使用消息ID + 内容索引
    return `text_${message.id}_${contentIndex}`
  } else if (content.type === 'tool_use' && content.name === 'generate_response') {
    // 特殊文本消息当作文本处理
    return `text_${message.id}_${contentIndex}`
  } else {
    // 默认情况下使用消息ID + 内容索引
    return `msg_${message.id}_${contentIndex}`
  }
}

// 更新索引缓存
const updateIndexCache = () => {
  const newCache: Record<string, number> = {}
  messages.value.forEach((message, index) => {
    if (message.messageId) {
      newCache[message.messageId] = index
    }
  })
  messageIdToIndex.value = newCache
}

// 通过消息ID查找消息索引
const findMessageIndexById = (messageId: string): number => {
  return messageIdToIndex.value[messageId] ?? -1
}

// 处理状态或错误类型消息包（status, error）
const handleStatusOrErrorMessage = (data: any) => {
  if (data.type === 'error') {
    // 处理错误消息，添加错误提示
    const errorMessage = createEnhancedMessage({
      content: data.message || '请求失败',
      role: 'assistant',
      messageType: 'text',
      typing: false
    })
    messages.value.push(errorMessage)
    updateIndexCache()
  }
}

// 获取消息的ID（保持向后兼容）
const getMessageId = (message: any): string => {
  if (Array.isArray(message.content) && message.content.length > 0) {
    const firstContent = message.content[0]

    // 特殊处理：generate_response 工具调用当作文本消息处理
    if (firstContent.type === 'tool_use' && firstContent.name === 'generate_response') {
      return `text_${message.id}_0`
    }

    // 如果是工具调用或工具结果，使用工具调用ID作为消息ID
    if (firstContent.type === 'tool_use') {
      return `tool_${firstContent.id}`
    } else if (firstContent.type === 'tool_result') {
      return `tool_${firstContent.id}`
    } else if (firstContent.type === 'text') {
      return `text_${message.id}_0`
    }
  }

  // 默认情况下，直接返回message.id
  return message.id
}

// 处理Server Message（统一处理 message_update 和 message_completed）
const handleMessageUpdate = (data: any) => {
  const message = data.message

  // 如果是响应完成类型消息包（response_completed）
  if (data.type === 'response_completed') {
    // 停止加载状态显示
    isLoading.value = false
    return
  }

  // 如果是状态或错误类型消息包（status, error）
  if (data.type === 'status' || data.type === 'error') {
    // 根据消息类型显示相应的提示信息
    handleStatusOrErrorMessage(data)
    return
  }

  // 统一处理逻辑（适用于 message_update 和 message_completed）
  if (!isContentTypeMessage(data.type)) {
    console.error('Invalid message type:', data.type)
    return
  }

  // 1. 遍历消息包中的每个内容块
  for (let contentIndex = 0; contentIndex < message.content.length; contentIndex++) {
    const content = message.content[contentIndex]

    // 2. 为每个内容块生成独立的消息ID
    const messageId = generateMessageId(content, contentIndex, message)

    // 3. 解析该内容块，获取初始内容
    const parsedResult = parseContentItem(content, messageId)

    // 4. 判断是否为新的内容块
    const existingMessageIndex = findMessageIndexById(messageId)

    let toHandle = false

    if (data.type === 'message_update') {
      // message_update：只处理文本内容，不处理tool_use和tool_result
      if (content.type === 'text' || (content.type === 'tool_use' && content.name === 'generate_response')) {
        toHandle = true
      }
    } else if (data.type === 'message_completed') {
      // message_completed：处理所有类型的内容块（包括tool_use和tool_result）
      toHandle = true
    }

    if (!toHandle) {
      console.log('Skipping content type:', content.type)
      continue
    }

    if (existingMessageIndex === -1) {
      // 直接使用parseContentItem返回的EnhancedMessage
      messages.value.push(parsedResult)
      updateIndexCache()
    } else {
      updateExistedMessage(content, messageId, existingMessageIndex)

      // 检查是否为display_analyse_by_code_result工具结果，如果是则自动创建数据分析消息
      if (data.type === 'message_completed' &&
          content.type === 'tool_result' &&
          content.name === 'display_analyse_by_code_result') {
        createAnalyseByCodeResultMessage(content)
      }
    }
  }
}

// 检查是否为内容类型消息
const isContentTypeMessage = (type: string): boolean => {
  return type === 'message_update' || type === 'message_completed'
}


// 解析单个内容项
const parseContentItem = (content: any, messageId: string): EnhancedMessage => {
  switch (content.type) {
    case 'text':
      return createEnhancedMessage({
        content: content.text,
        role: 'assistant',
        messageId,
        typing: { step: 50, interval: 10 }
      })

    case 'tool_use':
      if (content.name === 'generate_response') {
        // generate_response工具调用：特殊处理，直接显示响应内容
        return createEnhancedMessage({
          content: content.input.response,
          role: 'assistant',
          messageId,
          typing: { step: 50, interval: 10 }
        })
      } else {
        // 所有工具调用都显示相同的格式
        return createEnhancedMessage({
          content: `🔧 工具调用: ${content.name}`,
          role: 'assistant',
          messageId,
          typing: false
        })
      }

    case 'tool_result':
      // 所有工具结果都显示成功状态
      return createEnhancedMessage({
        content: '✅ 成功',
        role: 'assistant',
        messageId,
        typing: false
      })

    default:
      return createEnhancedMessage({
        content: '',
        role: 'assistant',
        messageId,
        typing: false
      })
  }
}

// 处理单个内容项更新
const updateExistedMessage = (content: any, messageId: string, messageIndex: number): void => {
  // 解析单个内容项
  const parsedResult = parseContentItem(content, messageId)

  // 获取对应的消息
  const targetMessage = messages.value[messageIndex]
  if (!targetMessage) return

  // 根据消息类型采用不同的内容处理策略
  if (messageId.startsWith('tool_')) {
    // 工具Message处理：采用累积策略
    const currentContent = targetMessage.content
    if (currentContent && !currentContent.includes(parsedResult.content)) {
      targetMessage.content = currentContent + '\n' + parsedResult.content
    } else {
      targetMessage.content = parsedResult.content
    }
  } else {
    // 文本Message处理：采用直接替换策略
    targetMessage.content = parsedResult.content
  }

  if (parsedResult.messageType) {
    targetMessage.messageType = parsedResult.messageType
  }
}

// 根据工具结果创建数据分析消息
const createAnalyseByCodeResultMessage = async (toolResultContent: any) => {
  try {
    console.log(toolResultContent)
    const analyseData = JSON.parse(toolResultContent.output[0].text)
    const analyseId = analyseData.analyse_id.toString()

    // 异步获取图表数据
    const chartDataList = await fetchChartData(analyseId)

    if (chartDataList.length > 0) {
      // 为每个图表创建一个新消息
      for (let i = 0; i < chartDataList.length; i++) {
        const chartMessage = createEnhancedMessage({
          content: `数据分析结果 ${i + 1}`,
          role: 'assistant',
          messageType: 'chart',
          chartData: chartDataList[i],
          messageId: `chart_${analyseId}_${i}`,
          typing: false
        })
        messages.value.push(chartMessage)
      }

      // 更新索引缓存
      updateIndexCache()
    }
  } catch (error) {
    console.error('解析 display_analyse_by_code_result 数据失败:', error)
    // 如果解析失败，创建一个错误消息
    const errorMessage = createEnhancedMessage({
      content: '数据分析结果解析失败',
      role: 'assistant',
      messageId: `error_${Date.now()}`,
      messageType: 'text',
      typing: false
    })
    messages.value.push(errorMessage)
    updateIndexCache()
  }
}



// 调用 /chat/get_analyse_by_code_result 接口获取图表数据
const fetchChartData = async (analyseId: string): Promise<any[]> => {
  try {
    const currentSessionId = chatHttpService.currentSessionId
    if (!currentSessionId) {
      console.error('Session ID not available')
      return []
    }

    // 动态获取图表 API base URL，支持运行时切换
      const baseUrl = getApiBaseUrl()
      const analyseUrl = `${baseUrl}/chat/get_analyse_by_code_result`
      console.log('Using analyse URL:', analyseUrl)

      const response = await axios.post(analyseUrl, {
      session_id: currentSessionId,
      analyse_id: parseInt(analyseId)
    })

    console.log('Chart API Response:', response.data)

    // 处理不同的响应格式
    const echartsList = response.data?.result?.echarts_list ||
                        response.data?.echarts_list ||
                        response.data?.data?.echarts_list ||
                        response.data?.data ||
                        []

    console.log('Extracted echartsList:', echartsList)
    return echartsList
  } catch (error) {
    console.error('获取图表数据失败:', error)
    return []
  }
}


// 发送消息
const sendMessage = () => {
  if (inputMessage.value.trim()) {
    // 添加用户消息
    const userMessage = createEnhancedMessage({
      content: inputMessage.value,
      role: 'user',
      messageType: 'text',
      typing: false
    })
    messages.value.push(userMessage)

    // 发送HTTP SSE消息
    chatHttpService.sendChatMessage(inputMessage.value)

    // 设置加载状态
    isLoading.value = true

    // 清空输入框
    inputMessage.value = ''
  }
}


// 注册HTTP SSE事件处理器
const registerHttpHandlers = () => {
  // 注册消息处理器
  chatHttpService.registerMessageHandler('message_update', handleMessageUpdate)
  chatHttpService.registerMessageHandler('message_completed', handleMessageUpdate)
  chatHttpService.registerMessageHandler('response_completed', handleMessageUpdate)
  chatHttpService.registerMessageHandler('status', handleStatusOrErrorMessage)
  chatHttpService.registerMessageHandler('error', handleStatusOrErrorMessage)

  // 注册连接状态处理器
  chatHttpService.onConnected(() => {
    hasError.value = false
  })

  chatHttpService.onError((error) => {
    hasError.value = true
    console.error('HTTP SSE connection error:', error)
  })
}

// 组件挂载时注册HTTP SSE处理器
onMounted(() => {
  registerHttpHandlers()
})


// 组件卸载时清理HTTP SSE
onUnmounted(() => {
  chatHttpService.disconnect()
})
</script>

<template>
  <div class="chat-container">
    <div class="chat-content">
      <BubbleListEnhance
        :list="messages"
        :loading="isLoading"
        :max-height="'100%'"
        :auto-scroll="true"
        class="bubble-list"
      />
    </div>

    <div class="chat-input">
      <Sender
        v-model="inputMessage"
        :state="senderState"
        :disabled="isLoading"
        placeholder="请输入您的问题..."
        @submit="sendMessage"
        :submit-type="'enter'"
        :min-rows="1"
        :max-rows="4"
        :allow-speech="false"
        class="sender"
      />
    </div>
  </div>
</template>

<style scoped>
.chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  padding-left: 20px;
  padding-right: 20px;
  max-width: 840px;
  width: 100%;
  margin: auto;
}

.chat-content {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 50px;
}

.chat-input {
  padding-bottom: 50px;
}


:deep(.el-bubble-list p) {
  margin: 0;
}

</style>
