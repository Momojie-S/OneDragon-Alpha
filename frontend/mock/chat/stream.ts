/**
 * Mock handlers for chat stream endpoint (/chat/stream)
 */

import { MockMethod } from 'vite-plugin-mock'
import { sendSSEMessages, generateMockChatMessages } from '../utils/sseGenerator'

export default [
  {
    url: '/chat/stream',
    method: 'post',
    rawResponse: async (req: any, res: any) => {
      console.log('🚀 Mock chat stream request received:', req.method, req.url)

      try {
        // Parse request body using Node.js style
        let body = ''
        await new Promise((resolve, reject) => {
          let data = ''
          req.on('data', (chunk: any) => {
            data += chunk
          })
          req.on('end', () => {
            try {
              body = JSON.parse(data)
              resolve(undefined)
            } catch (error) {
              reject(error)
            }
          })
          req.on('error', reject)
        })

        const { user_input, session_id } = body

        console.log('Mock processing user input:', user_input, 'session:', session_id)

        // Generate mock chat messages
        const messages = generateMockChatMessages(user_input)

        // Set headers for SSE
        res.setHeader('Content-Type', 'text/event-stream')
        res.setHeader('Cache-Control', 'no-cache')
        res.setHeader('Connection', 'keep-alive')
        res.setHeader('Access-Control-Allow-Origin', '*')
        res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

        res.statusCode = 200

        // Send SSE messages directly
        await sendSSEMessages(messages, res)
        res.end()
      } catch (error) {
        console.error('Mock stream error:', error)
        res.setHeader('Content-Type', 'application/json')
        res.statusCode = 500
        res.end(JSON.stringify({ error: 'Internal Server Error', message: error.message }))
      }
    }
  },
  {
    url: '/api/chat/stream',
    method: 'options',
    rawResponse: (req: any, res: any) => {
      res.setHeader('Access-Control-Allow-Origin', '*')
      res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
      res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
      res.statusCode = 200
      res.end()
    }
  }
] as MockMethod[]