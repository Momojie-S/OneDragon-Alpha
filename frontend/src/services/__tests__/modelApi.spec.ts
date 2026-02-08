/**
 * 模型配置 API 服务单元测试
 */

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { ModelApiService } from '../modelApi'
import type {
  CreateModelConfigRequest,
  UpdateModelConfigRequest,
  ModelConfig,
  PaginatedResponse
} from '../modelApi'

// Mock fetch
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('ModelApiService', () => {
  let service: ModelApiService

  beforeEach(() => {
    service = new ModelApiService()
    mockFetch.mockClear()
  })

  describe('createModelConfig', () => {
    it('应该成功创建模型配置', async () => {
      // Given
      const requestData: CreateModelConfigRequest = {
        name: 'Test Config',
        provider: 'openai',
        base_url: 'https://api.openai.com',
        api_key: 'sk-test',
        models: [
          { model_id: 'gpt-4', support_vision: true, support_thinking: false }
        ],
        is_active: true
      }

      const mockResponse: ModelConfig = {
        id: 1,
        ...requestData,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response)

      // When
      const result = await service.createModelConfig(requestData)

      // Then
      expect(result).toEqual(mockResponse)
      expect(mockFetch).toHaveBeenCalledTimes(1)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/models/configs'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestData)
        })
      )
    })

    it('应该在创建失败时抛出错误', async () => {
      // Given
      const requestData: CreateModelConfigRequest = {
        name: 'Test',
        provider: 'openai',
        base_url: 'https://api.test.com',
        api_key: 'sk-test',
        models: [{ model_id: 'test', support_vision: false, support_thinking: false }]
      }

      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ message: '配置名称已存在' })
      } as Response)

      // When & Then
      await expect(service.createModelConfig(requestData)).rejects.toThrow('配置名称已存在')
    })
  })

  describe('getModelConfigs', () => {
    it('应该返回分页的配置列表', async () => {
      // Given
      const mockResponse: PaginatedResponse<ModelConfig> = {
        total: 100,
        page: 1,
        page_size: 20,
        items: [
          {
            id: 1,
            name: 'Config 1',
            provider: 'openai',
            base_url: 'https://api.test.com',
            models: [{ model_id: 'gpt-4', support_vision: false, support_thinking: false }],
            is_active: true,
            created_at: '2025-01-01T00:00:00Z',
            updated_at: '2025-01-01T00:00:00Z'
          }
        ]
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response)

      // When
      const result = await service.getModelConfigs({ page: 1, page_size: 20 })

      // Then
      expect(result).toEqual(mockResponse)
      expect(result.total).toBe(100)
      expect(result.items).toHaveLength(1)
    })

    it('应该正确应用过滤参数', async () => {
      // Given
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total: 0, page: 1, page_size: 20, items: [] })
      } as Response)

      // When
      await service.getModelConfigs({
        page: 2,
        page_size: 50,
        active: true,
        provider: 'openai'
      })

      // Then
      const url = mockFetch.mock.calls[0][0]
      expect(url).toContain('page=2')
      expect(url).toContain('page_size=50')
      expect(url).toContain('active=true')
      expect(url).toContain('provider=openai')
    })
  })

  describe('getModelConfig', () => {
    it('应该返回单个配置', async () => {
      // Given
      const mockConfig: ModelConfig = {
        id: 1,
        name: 'Test Config',
        provider: 'openai',
        base_url: 'https://api.test.com',
        models: [{ model_id: 'gpt-4', support_vision: false, support_thinking: false }],
        is_active: true,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig
      } as Response)

      // When
      const result = await service.getModelConfig(1)

      // Then
      expect(result).toEqual(mockConfig)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/models/configs/1'),
        expect.any(Object)
      )
    })
  })

  describe('updateModelConfig', () => {
    it('应该成功更新配置', async () => {
      // Given
      const updateData: UpdateModelConfigRequest = {
        name: 'Updated Config',
        is_active: false
      }

      const mockResponse: ModelConfig = {
        id: 1,
        name: 'Updated Config',
        provider: 'openai',
        base_url: 'https://api.test.com',
        models: [],
        is_active: false,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T01:00:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response)

      // When
      const result = await service.updateModelConfig(1, updateData)

      // Then
      expect(result.name).toBe('Updated Config')
      expect(result.is_active).toBe(false)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/models/configs/1'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData)
        })
      )
    })
  })

  describe('deleteModelConfig', () => {
    it('应该成功删除配置', async () => {
      // Given
      mockFetch.mockResolvedValueOnce({
        ok: true,
        status: 204
      } as Response)

      // When
      const result = await service.deleteModelConfig(1)

      // Then
      expect(result).toBe(true)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/models/configs/1'),
        expect.objectContaining({ method: 'DELETE' })
      )
    })

    it('应该在删除失败时返回错误', async () => {
      // Given
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ message: '配置不存在' })
      } as Response)

      // When & Then
      await expect(service.deleteModelConfig(999)).rejects.toThrow('配置不存在')
    })
  })

  describe('toggleConfigStatus', () => {
    it('应该成功切换启用状态', async () => {
      // Given
      const mockConfig: ModelConfig = {
        id: 1,
        name: 'Test',
        provider: 'openai',
        base_url: 'https://api.test.com',
        models: [],
        is_active: false,
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockConfig
      } as Response)

      // When
      const result = await service.toggleConfigStatus(1, false)

      // Then
      expect(result.is_active).toBe(false)
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/models/configs/1/status?is_active=false'),
        expect.objectContaining({ method: 'PATCH' })
      )
    })
  })

  describe('testConnection', () => {
    it('应该成功测试连接', async () => {
      // Given
      const requestData = {
        base_url: 'https://api.openai.com',
        api_key: 'sk-test'
      }

      const mockResponse = {
        success: true,
        message: '连接成功'
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response)

      // When
      const result = await service.testConnection(requestData)

      // Then
      expect(result.success).toBe(true)
      expect(result.message).toBe('连接成功')
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/models/configs/test-connection'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(requestData)
        })
      )
    })

    it('应该处理连接失败', async () => {
      // Given
      const requestData = {
        base_url: 'https://invalid-url.com',
        api_key: 'invalid-key'
      }

      const mockResponse = {
        success: false,
        message: '无法连接到服务器',
        raw_error: { error: 'Connection refused' }
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      } as Response)

      // When
      const result = await service.testConnection(requestData)

      // Then
      expect(result.success).toBe(false)
      expect(result.message).toBe('无法连接到服务器')
      expect(result.raw_error).toBeDefined()
    })
  })
})
