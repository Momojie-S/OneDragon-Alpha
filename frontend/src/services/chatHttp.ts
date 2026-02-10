/**
 * HTTP SSE service for chat communication
 * Handles connection, message sending/receiving, and different message types using Server-Sent Events
 */
import { getApiBaseUrl } from '../config/api'

export class ChatHttpService {
  private sessionId: string | null = null
  private abortController: AbortController | null = null
  private isConnected = false
  private messageHandlers: Map<string, (data: any) => void> = new Map()
  private connectedHandlers: (() => void)[] = []
  private disconnectedHandlers: (() => void)[] = []
  private errorHandlers: ((error: any) => void)[] = []

  /**
   * Send a chat message to the server using HTTP POST with SSE streaming
   * @param userInput User's message content
   * @param modelConfigId Model configuration ID
   * @param modelId Model ID within the configuration
   * @param sessionId Optional session ID for existing session
   */
  async sendChatMessage(
    userInput: string,
    modelConfigId: number,
    modelId: string,
    sessionId?: string,
  ): Promise<void> {
    if (this.abortController) {
      // Cancel any ongoing request
      this.abortController.abort()
    }

    this.abortController = new AbortController()

    try {
      // Store session ID if provided
      if (sessionId) {
        this.sessionId = sessionId
      }

      // 动态获取 API base URL，支持运行时切换
      const baseUrl = getApiBaseUrl()
      const streamUrl = `${baseUrl}/chat/stream`

      const response = await fetch(streamUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: this.sessionId,
          user_input: userInput,
          model_config_id: modelConfigId,
          model_id: modelId,
        }),
        signal: this.abortController.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      if (!response.body) {
        throw new Error('Response body is null')
      }

      this.isConnected = true
      this.notifyConnected()

      // Read the stream as SSE
      await this.readSSEStream(response.body)
    } catch (error) {
      if (error.name === 'AbortError') {
        console.log('Request was aborted')
      } else {
        console.error('HTTP SSE error:', error)
        this.notifyError(error)
      }
    } finally {
      this.isConnected = false
      this.abortController = null
      this.notifyDisconnected()
    }
  }

  /**
   * Read and process SSE stream
   * @param body ReadableStream from response
   */
  private async readSSEStream(body: ReadableStream<Uint8Array>): Promise<void> {
    const reader = body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { done, value } = await reader.read()

        if (done) {
          break
        }

        buffer += decoder.decode(value, { stream: true })

        // Process complete SSE messages (ending with \n\n)
        const lines = buffer.split('\n\n')
        buffer = lines.pop() || '' // Keep incomplete data in buffer

        for (const line of lines) {
          if (line.trim()) {
            this.processSSELine(line)
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  /**
   * Process a single SSE line
   * @param line SSE line to process
   */
  private processSSELine(line: string): void {
    const lines = line.split('\n')
    let jsonData = ''

    for (const sseLine of lines) {
      if (sseLine.startsWith('data: ')) {
        jsonData = sseLine.substring(6).trim()
      }
    }

    if (jsonData) {
      try {
        const message = JSON.parse(jsonData)
        this.handleMessage(message)
      } catch (error) {
        console.error('Failed to parse SSE message:', error)
      }
    }
  }

  /**
   * Handle incoming SSE messages
   * @param message Parsed message data
   */
  private handleMessage(message: any): void {
    const { type, session_id } = message

    // Store session ID if provided in message
    if (session_id) {
      this.sessionId = session_id
    }

    // Call registered handlers for this message type
    const handler = this.messageHandlers.get(type)
    if (handler) {
      handler(message)
    }
  }

  /**
   * Interrupt current request
   */
  async sendInterrupt(): Promise<void> {
    if (this.abortController) {
      this.abortController.abort()
    }
  }

  /**
   * Register a message handler for specific message types
   * @param messageType Message type to handle
   * @param handler Handler function
   */
  registerMessageHandler(messageType: string, handler: (data: any) => void): void {
    this.messageHandlers.set(messageType, handler)
  }

  /**
   * Remove a message handler
   * @param messageType Message type to remove handler for
   */
  removeMessageHandler(messageType: string): void {
    this.messageHandlers.delete(messageType)
  }

  /**
   * Register a connected callback
   * @param handler Function to call when connected
   */
  onConnected(handler: () => void): void {
    this.connectedHandlers.push(handler)
  }

  /**
   * Register a disconnected callback
   * @param handler Function to call when disconnected
   */
  onDisconnected(handler: () => void): void {
    this.disconnectedHandlers.push(handler)
  }

  /**
   * Register an error callback
   * @param handler Function to call when error occurs
   */
  onError(handler: (error: any) => void): void {
    this.errorHandlers.push(handler)
  }

  /**
   * Notify all connected handlers
   */
  private notifyConnected(): void {
    this.connectedHandlers.forEach((handler) => handler())
  }

  /**
   * Notify all disconnected handlers
   */
  private notifyDisconnected(): void {
    this.disconnectedHandlers.forEach((handler) => handler())
  }

  /**
   * Notify all error handlers
   */
  private notifyError(error: any): void {
    this.errorHandlers.forEach((handler) => handler(error))
  }

  /**
   * Get current connection status
   */
  get isConnectedStatus(): boolean {
    return this.isConnected
  }

  /**
   * Get current session ID
   */
  get currentSessionId(): string | null {
    return this.sessionId
  }

  /**
   * Clean up resources
   */
  disconnect(): void {
    if (this.abortController) {
      this.abortController.abort()
      this.abortController = null
    }
    this.isConnected = false
  }
}

// Export singleton instance
export const chatHttpService = new ChatHttpService()
