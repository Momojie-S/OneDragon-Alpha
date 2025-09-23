/**
 * Mock handlers for chat analysis endpoint (/chat/get_analyse_by_code_result)
 */

import { MockMethod } from 'vite-plugin-mock'
import { generateMockChartData } from '../utils/sseGenerator'

export default [
  {
    url: '/chat/get_analyse_by_code_result',
    method: 'post',
    rawResponse: async (req: any, res: any) => {
      console.log('Mock analyse request received:', req.method, req.url)

      try {
        // Parse request body using Node.js style
        let body = {}
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

        const { session_id, analyse_id } = body

        console.log('Mock processing analyse request:', session_id, analyse_id)

        // Generate mock chart data
        const mockData = generateMockChartData(analyse_id)

        // Add some delay to simulate network latency
        await new Promise(resolve => setTimeout(resolve, 300 + Math.random() * 500))

        // Set headers
        res.setHeader('Content-Type', 'application/json')
        res.setHeader('Access-Control-Allow-Origin', '*')
        res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

        res.statusCode = 200
        res.end(JSON.stringify(mockData))
      } catch (error) {
        console.error('Mock analyse error:', error)

        // Return error response
        const errorResponse = {
          error: 'Analysis not found',
          message: `Analysis data for ID not found: ${error.message}`,
          session_id: body?.session_id || 'unknown',
          analyse_id: body?.analyse_id || 0
        }

        res.setHeader('Content-Type', 'application/json')
        res.setHeader('Access-Control-Allow-Origin', '*')
        res.setHeader('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
        res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')

        res.statusCode = 404
        res.end(JSON.stringify(errorResponse))
      }
    }
  },
  {
    url: '/api/chat/get_analyse_by_code_result',
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