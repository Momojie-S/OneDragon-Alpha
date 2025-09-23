/**
 * Server-Sent Events (SSE) generator utilities for mock responses
 */

export interface ChatMessage {
  type: 'message_update' | 'message_completed' | 'response_completed' | 'status' | 'error'
  session_id: string
  message: any
}

/**
 * Generate mock chat messages based on user input
 * @param userInput User's message content
 * @returns Array of mock chat messages
 */
export function generateMockChatMessages(userInput: string): ChatMessage[] {
  const sessionId = generateSessionId()
  const messages: ChatMessage[] = []

  // Connection status message
  messages.push({
    type: 'status',
    session_id: sessionId,
    message: { hint: 'connected' }
  })

  // Simulate thinking and response generation
  if (userInput.toLowerCase().includes('hello') || userInput.toLowerCase().includes('你好')) {
    const messageId = generateMessageId()

    // First message update - partial greeting
    messages.push({
      type: 'message_update',
      session_id: sessionId,
      message: {
        id: messageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{ type: 'text', text: '你好！' }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

    // Second message update - complete greeting with single text element
    messages.push({
      type: 'message_update',
      session_id: sessionId,
      message: {
        id: messageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{ type: 'text', text: '你好！我是 OneDragon Alpha，很高兴为您服务。' }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

    // Complete the message
    messages.push({
      type: 'message_completed',
      session_id: sessionId,
      message: {
        id: messageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{ type: 'text', text: '你好！我是 OneDragon Alpha，很高兴为您服务。' }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

  } else if (userInput.toLowerCase().includes('chart') || userInput.toLowerCase().includes('图表')) {
    const toolMessageId = generateMessageId()
    const analyseId = Math.floor(Math.random() * 100000)
    const toolCallId = generateToolCallId()

    // Tool call message
    messages.push({
      type: 'message_update',
      session_id: sessionId,
      message: {
        id: toolMessageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{
          type: 'tool_use',
          id: toolCallId,
          name: 'display_analyse_by_code_result',
          input: { analyse_id: analyseId }
        }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

    // Tool result message (separate message)
    const resultMessageId = generateMessageId()
    messages.push({
      type: 'message_update',
      session_id: sessionId,
      message: {
        id: resultMessageId,
        name: 'system',
        role: 'system',
        content: [{
          type: 'tool_result',
          id: toolCallId,
          name: 'display_analyse_by_code_result',
          output: [{ type: 'text', text: `{"analyse_id": ${analyseId}}` }]
        }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

    // Complete tool message
    messages.push({
      type: 'message_completed',
      session_id: sessionId,
      message: {
        id: toolMessageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{
          type: 'tool_use',
          id: toolCallId,
          name: 'display_analyse_by_code_result',
          input: { analyse_id: analyseId }
        }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

    // Complete result message
    messages.push({
      type: 'message_completed',
      session_id: sessionId,
      message: {
        id: resultMessageId,
        name: 'system',
        role: 'system',
        content: [{
          type: 'tool_result',
          id: toolCallId,
          name: 'display_analyse_by_code_result',
          output: [{ type: 'text', text: `{"analyse_id": ${analyseId}}` }]
        }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

  } else {
    const messageId = generateMessageId()

    // Text message with progressive updates (叠加式)
    messages.push({
      type: 'message_update',
      session_id: sessionId,
      message: {
        id: messageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{ type: 'text', text: '我正在处理您的问题：' + userInput }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

    // Second message update - complete content with single text element
    messages.push({
      type: 'message_update',
      session_id: sessionId,
      message: {
        id: messageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{ type: 'text', text: '我正在处理您的问题：' + userInput + '这是一个模拟的回复，用于测试前端界面。' }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })

    // Complete the message
    messages.push({
      type: 'message_completed',
      session_id: sessionId,
      message: {
        id: messageId,
        name: 'OneDragon',
        role: 'assistant',
        content: [{ type: 'text', text: '我正在处理您的问题：' + userInput + '这是一个模拟的回复，用于测试前端界面。' }],
        metadata: null,
        timestamp: getCurrentTimestamp()
      }
    })
  }

  // Complete the entire response
  messages.push({
    type: 'response_completed',
    session_id: sessionId,
    message: {}
  })

  return messages
}

/**
 * Generate a mock session ID
 * @returns Random session ID string
 */
function generateSessionId(): string {
  return 'mock_session_' + Math.random().toString(36).substr(2, 9)
}

/**
 * Generate a mock message ID
 * @returns Random message ID string
 */
function generateMessageId(): string {
  return 'msg_' + Math.random().toString(36).substr(2, 12)
}

/**
 * Generate a mock tool call ID
 * @returns Random tool call ID string
 */
function generateToolCallId(): string {
  return 'call_' + Math.random().toString(36).substr(2, 12)
}

/**
 * Get current timestamp in ISO format
 * @returns Current timestamp string
 */
function getCurrentTimestamp(): string {
  return new Date().toISOString().replace('T', ' ').substr(0, 23)
}

/**
 * Create a readable stream for SSE response (Web API version)
 * @param messages Array of chat messages
 * @returns ReadableStream that yields SSE formatted data
 */
export function createSSEStream(messages: ChatMessage[]): ReadableStream<Uint8Array> {
  return new ReadableStream({
    async start(controller) {
      try {
        for (let i = 0; i < messages.length; i++) {
          const message = messages[i]
          const sseData = `data: ${JSON.stringify(message)}\n\n`
          const encoder = new TextEncoder()
          controller.enqueue(encoder.encode(sseData))

          // Simulate delay between messages
          if (i < messages.length - 1) {
            await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000))
          }
        }
      } catch (error) {
        console.error('Error in SSE stream:', error)
        controller.error(error)
      } finally {
        controller.close()
      }
    }
  })
}

/**
 * Send SSE messages directly to Node.js response
 * @param messages Array of chat messages
 * @param res Node.js ServerResponse object
 */
export async function sendSSEMessages(messages: ChatMessage[], res: any): Promise<void> {
  try {
    for (let i = 0; i < messages.length; i++) {
      const message = messages[i]
      const sseData = `data: ${JSON.stringify(message)}\n\n`

      res.write(sseData)

      // Simulate delay between messages
      if (i < messages.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 1000))
      }
    }
  } catch (error) {
    console.error('Error sending SSE messages:', error)
    throw error
  }
}

/**
 * Simulate chart data for analysis results
 * @param analyseId Analysis ID
 * @returns Mock chart data
 */
export function generateMockChartData(analyseId: number) {
  return {
    session_id: generateSessionId(),
    analyse_id: analyseId,
    result: {
      echarts_list: [
        {
          title: {
            text: '模拟图表数据'
          },
          xAxis: {
            type: 'category',
            data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
          },
          yAxis: {
            type: 'value'
          },
          series: [{
            data: [150, 230, 224, 218, 135, 147, 260],
            type: 'line',
            name: '数据系列'
          }]
        }
      ]
    }
  }
}
