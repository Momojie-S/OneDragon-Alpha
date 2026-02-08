/**
 * 模型配置管理 API 服务
 * 提供模型配置的 CRUD 操作和测试连接功能
 */

import { getApiBaseUrl } from '../config/api'

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 模型能力信息
 */
export interface ModelInfo {
  /** 模型 ID */
  model_id: string
  /** 是否支持视觉能力 */
  support_vision: boolean
  /** 是否支持思考能力 */
  support_thinking: boolean
}

/**
 * 模型配置
 */
export interface ModelConfig {
  /** 配置 ID */
  id: number
  /** 配置名称 */
  name: string
  /** 提供商（当前仅支持 "openai"） */
  provider: string
  /** API 基础 URL */
  base_url: string
  /** 模型列表 */
  models: ModelInfo[]
  /** 是否启用 */
  is_active: boolean
  /** 创建时间 */
  created_at: string
  /** 更新时间 */
  updated_at: string
}

/**
 * 创建模型配置请求
 */
export interface CreateModelConfigRequest {
  /** 配置名称 */
  name: string
  /** 提供商（仅支持 "openai"） */
  provider: string
  /** API 基础 URL */
  base_url: string
  /** API 密钥 */
  api_key: string
  /** 模型列表 */
  models: ModelInfo[]
  /** 是否启用 */
  is_active?: boolean
}

/**
 * 更新模型配置请求
 */
export interface UpdateModelConfigRequest {
  /** 配置名称 */
  name?: string
  /** 提供商（仅支持 "openai"） */
  provider?: string
  /** API 基础 URL */
  base_url?: string
  /** API 密钥（留空则不修改） */
  api_key?: string
  /** 模型列表 */
  models?: ModelInfo[]
  /** 是否启用 */
  is_active?: boolean
  /** 更新时间戳（乐观锁） */
  updated_at?: string
}

/**
 * 分页响应
 */
export interface PaginatedResponse<T> {
  /** 总记录数 */
  total: number
  /** 当前页码 */
  page: number
  /** 每页记录数 */
  page_size: number
  /** 数据列表 */
  items: T[]
}

/**
 * 分页查询参数
 */
export interface PaginationParams {
  /** 页码（从 1 开始） */
  page?: number
  /** 每页记录数（最大 100） */
  page_size?: number
  /** 是否启用（可选过滤） */
  is_active?: boolean
  /** 提供商（可选过滤） */
  provider?: string
}

/**
 * 测试连接请求
 */
export interface TestConnectionRequest {
  /** API 基础 URL */
  base_url: string
  /** API 密钥 */
  api_key: string
  /** 模型 ID（可选，默认使用 gpt-3.5-turbo） */
  model_id?: string
}

/**
 * 测试连接响应
 */
export interface TestConnectionResponse {
  /** 是否成功 */
  success: boolean
  /** 响应消息 */
  message: string
  /** 原始错误信息（可选） */
  raw_error?: Record<string, unknown>
}

/**
 * API 错误响应
 */
export interface ApiError {
  /** 错误码 */
  code: string
  /** 错误信息 */
  message: string
  /** 错误详情 */
  details: Record<string, unknown>
}

// ============================================================================
// API 服务类
// ============================================================================

/**
 * 模型配置 API 服务类
 */
export class ModelApiService {
  private baseUrl: string

  constructor() {
    this.baseUrl = getApiBaseUrl()
  }

  /**
   * 构建完整的 API URL
   */
  private buildUrl(path: string): string {
    return `${this.baseUrl}/api/models${path}`
  }

  /**
   * 处理 API 响应
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      // 尝试解析错误响应
      let errorMessage = `HTTP ${response.status}`
      try {
        const errorData: ApiError = await response.json()
        errorMessage = errorData.message || errorMessage
      } catch {
        // 如果无法解析 JSON，使用默认错误消息
      }
      throw new Error(errorMessage)
    }

    return response.json() as Promise<T>
  }

  /**
   * 创建模型配置
   * @param data 创建配置请求
   * @returns 创建的配置
   */
  async createModelConfig(data: CreateModelConfigRequest): Promise<ModelConfig> {
    const response = await fetch(this.buildUrl('/configs'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    return this.handleResponse<ModelConfig>(response)
  }

  /**
   * 获取模型配置列表
   * @param params 分页和过滤参数
   * @returns 分页响应
   */
  async getModelConfigs(params?: PaginationParams): Promise<PaginatedResponse<ModelConfig>> {
    const queryParams = new URLSearchParams()

    if (params) {
      if (params.page) queryParams.append('page', String(params.page))
      if (params.page_size) queryParams.append('page_size', String(params.page_size))
      if (params.is_active !== undefined) queryParams.append('is_active', String(params.is_active))
      if (params.provider) queryParams.append('provider', params.provider)
    }

    const url = queryParams.toString()
      ? this.buildUrl(`/configs?${queryParams.toString()}`)
      : this.buildUrl('/configs')

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<PaginatedResponse<ModelConfig>>(response)
  }

  /**
   * 获取单个模型配置
   * @param id 配置 ID
   * @returns 模型配置
   */
  async getModelConfig(id: number): Promise<ModelConfig> {
    const response = await fetch(this.buildUrl(`/configs/${id}`), {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    return this.handleResponse<ModelConfig>(response)
  }

  /**
   * 更新模型配置
   * @param id 配置 ID
   * @param data 更新请求数据
   * @returns 更新后的配置
   */
  async updateModelConfig(id: number, data: UpdateModelConfigRequest): Promise<ModelConfig> {
    const response = await fetch(this.buildUrl(`/configs/${id}`), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    return this.handleResponse<ModelConfig>(response)
  }

  /**
   * 删除模型配置
   * @param id 配置 ID
   * @returns 是否删除成功
   */
  async deleteModelConfig(id: number): Promise<boolean> {
    const response = await fetch(this.buildUrl(`/configs/${id}`), {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (response.status === 204) {
      return true
    }

    return this.handleResponse<boolean>(response)
  }

  /**
   * 切换配置启用状态
   * @param id 配置 ID
   * @param isActive 是否启用
   * @returns 更新后的配置
   */
  async toggleConfigStatus(id: number, isActive: boolean): Promise<ModelConfig> {
    const response = await fetch(
      this.buildUrl(`/configs/${id}/status?is_active=${String(isActive)}`),
      {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
      },
    )

    return this.handleResponse<ModelConfig>(response)
  }

  /**
   * 测试 API 连接
   * @param data 测试连接请求
   * @returns 测试结果
   */
  async testConnection(data: TestConnectionRequest): Promise<TestConnectionResponse> {
    const response = await fetch(this.buildUrl('/configs/test-connection'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    })

    return this.handleResponse<TestConnectionResponse>(response)
  }

  /**
   * 获取所有已启用的模型配置
   * @param params 分页和过滤参数
   * @returns 分页响应，仅包含已启用的配置
   * @description 自动分页获取所有已启用配置，避免 page_size 限制导致数据截断
   */
  async getActiveModelConfigs(
    params?: Omit<PaginationParams, 'is_active'>,
  ): Promise<PaginatedResponse<ModelConfig>> {
    const startPage = params?.page ?? 1
    const pageSize = params?.page_size ?? 100
    let page = startPage
    let total = 0
    let items: ModelConfig[] = []

    // 循环获取所有页的数据
    while (true) {
      const res = await this.getModelConfigs({
        ...params,
        is_active: true,
        page,
        page_size: pageSize,
      })
      if (page === startPage) total = res.total
      items = items.concat(res.items)
      // 如果已获取所有数据或当前页无数据，退出循环
      if (items.length >= total || res.items.length === 0) break
      page += 1
    }

    return { total, page: startPage, page_size: pageSize, items }
  }
}

// ============================================================================
// 导出单例
// ============================================================================

/**
 * 模型配置 API 服务单例
 */
export const modelApiService = new ModelApiService()

// ============================================================================
// 便捷函数（可选，提供更简洁的调用方式）
// ============================================================================

/**
 * 创建模型配置
 */
export const createModelConfig = (data: CreateModelConfigRequest) =>
  modelApiService.createModelConfig(data)

/**
 * 获取模型配置列表
 */
export const getModelConfigs = (params?: PaginationParams) =>
  modelApiService.getModelConfigs(params)

/**
 * 获取已启用的模型配置列表
 */
export const getActiveModelConfigs = (params?: Omit<PaginationParams, 'is_active'>) =>
  modelApiService.getActiveModelConfigs(params)

/**
 * 获取单个模型配置
 */
export const getModelConfig = (id: number) => modelApiService.getModelConfig(id)

/**
 * 更新模型配置
 */
export const updateModelConfig = (id: number, data: UpdateModelConfigRequest) =>
  modelApiService.updateModelConfig(id, data)

/**
 * 删除模型配置
 */
export const deleteModelConfig = (id: number) => modelApiService.deleteModelConfig(id)

/**
 * 切换配置启用状态
 */
export const toggleConfigStatus = (id: number, isActive: boolean) =>
  modelApiService.toggleConfigStatus(id, isActive)

/**
 * 测试 API 连接
 */
export const testConnection = (data: TestConnectionRequest) => modelApiService.testConnection(data)
