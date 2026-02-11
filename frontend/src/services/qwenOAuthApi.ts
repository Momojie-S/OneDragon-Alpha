/**
 * Qwen OAuth 认证 API 服务
 * 提供 Qwen OAuth 设备码认证流程的相关接口
 */

import { getApiBaseUrl } from '../config/api'

// ============================================================================
// 类型定义
// ============================================================================

/**
 * 设备码响应
 */
export interface DeviceCodeResponse {
  /** 会话 ID，用于后续状态轮询 */
  session_id: string
  /** 设备码，用于轮询认证状态 */
  device_code: string
  /** 用户码，用户在验证页面输入的代码（8位，格式如 "ABCD-1234"） */
  user_code: string
  /** 验证链接 */
  verification_uri: string
  /** 完整验证链接（包含用户码） */
  verification_uri_complete: string
  /** 过期时间（秒） */
  expires_in: number
  /** 轮询间隔（秒） */
  interval: number
}

/**
 * OAuth 认证状态
 */
export type OAuthStatus = 'pending' | 'success' | 'error'

/**
 * OAuth Token 信息
 */
export interface OAuthToken {
  /** 访问令牌 */
  access_token: string
  /** 刷新令牌 */
  refresh_token: string
  /** 过期时间戳（毫秒） */
  expires_at: number
  /** 令牌类型 */
  token_type?: string
  /** 授权范围 */
  scope?: string
  /** 资源 URL */
  resource_url?: string
}

/**
 * OAuth 状态轮询响应
 */
export interface OAuthStatusResponse {
  /** 认证状态 */
  status: OAuthStatus
  /** 认证成功的 token 信息（仅 status=success 时存在） */
  token?: OAuthToken
  /** 错误信息（仅 status=error 时存在） */
  error?: string
  /** 建议重试间隔（毫秒） */
  retry_after?: number
}

/**
 * API 错误响应
 */
export interface ApiError {
  /** 错误码 */
  code?: string
  /** 错误信息 */
  message: string
  /** 错误详情 */
  details?: Record<string, unknown>
}

// ============================================================================
// API 服务类
// ============================================================================

/**
 * Qwen OAuth API 服务类
 */
export class QwenOAuthApiService {
  private baseUrl: string

  constructor() {
    this.baseUrl = getApiBaseUrl()
  }

  /**
   * 构建完整的 API URL
   */
  private buildUrl(path: string): string {
    return `${this.baseUrl}/api/qwen/oauth${path}`
  }

  /**
   * 处理 API 响应
   */
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
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
   * 获取设备码
   * 用于启动 OAuth 设备码认证流程
   *
   * @returns 设备码响应信息
   * @throws {Error} 当请求失败时抛出错误
   *
   * @example
   * ```ts
   * const deviceCode = await qwenOAuthApiService.getDeviceCode()
   * console.log(deviceCode.user_code) // "ABCD-1234"
   * console.log(deviceCode.verification_uri_complete) // 完整验证链接
   * ```
   */
  async getDeviceCode(): Promise<DeviceCodeResponse> {
    const response = await fetch(this.buildUrl('/device-code'), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({}),
    })

    return this.handleResponse<DeviceCodeResponse>(response)
  }

  /**
   * 轮询 OAuth 认证状态
   * 用于检查用户是否已完成授权
   *
   * @param deviceCode 设备码
   * @returns 认证状态响应
   * @throws {Error} 当请求失败或设备码无效时抛出错误
   *
   * @example
   * ```ts
   * // 轮询示例
   * const pollStatus = async () => {
   *   const status = await qwenOAuthApiService.pollOAuthStatus(deviceCode)
   *   if (status.status === 'success') {
   *     console.log('认证成功:', status.token)
   *     return true
   *   } else if (status.status === 'error') {
   *     console.error('认证失败:', status.error)
   *     return false
   *   }
   *   // 继续轮询
   *   return false
   * }
   * ```
   */
  async pollOAuthStatus(deviceCode: string): Promise<OAuthStatusResponse> {
    const response = await fetch(
      this.buildUrl(`/status?device_code=${encodeURIComponent(deviceCode)}`),
      {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      },
    )

    return this.handleResponse<OAuthStatusResponse>(response)
  }

  /**
   * 带自动重试的状态轮询
   * 自动按照返回的间隔进行轮询，直到认证成功、失败或超时
   *
   * @param deviceCode 设备码
   * @param options 轮询选项
   * @returns 认证成功的 token 信息
   * @throws {Error} 当认证失败、超时或出错时抛出错误
   *
   * @example
   * ```ts
   * try {
   *   const token = await qwenOAuthApiService.pollWithRetry(deviceCode, {
   *     timeout: 900000, // 15分钟超时
   *     onPending: (interval) => console.log(`等待中，${interval}ms 后重试`)
   *   })
   *   console.log('认证成功:', token)
   * } catch (error) {
   *   console.error('认证失败:', error)
   * }
   * ```
   */
  async pollWithRetry(
    deviceCode: string,
    options: {
      /** 超时时间（毫秒），默认 15 分钟 */
      timeout?: number
      /** 最大轮询次数，默认 180 次（15分钟 / 5秒） */
      maxAttempts?: number
      /** 状态回调 */
      onStatusChange?: (status: OAuthStatusResponse) => void
      /** 取消信号 */
      signal?: AbortSignal
    } = {},
  ): Promise<OAuthToken> {
    const { timeout = 900000, maxAttempts = 180, onStatusChange, signal } = options

    const startTime = Date.now()
    let attempts = 0
    let currentInterval = 5000 // 默认 5 秒

    while (attempts < maxAttempts) {
      // 检查超时
      if (Date.now() - startTime > timeout) {
        throw new Error('认证超时，请重新开始')
      }

      // 检查取消信号
      if (signal?.aborted) {
        throw new Error('认证已取消')
      }

      attempts++

      try {
        const statusResponse = await this.pollOAuthStatus(deviceCode)

        // 触发状态回调
        onStatusChange?.(statusResponse)

        if (statusResponse.status === 'success' && statusResponse.token) {
          return statusResponse.token
        }

        if (statusResponse.status === 'error') {
          throw new Error(statusResponse.error || '认证失败')
        }

        // 如果返回了重试间隔，使用该间隔
        if (statusResponse.retry_after) {
          currentInterval = statusResponse.retry_after
        }

        // 等待后重试
        await this.sleep(currentInterval)
      } catch (error) {
        // 如果是 408 超时或 400 无效设备码，直接抛出
        if (error instanceof Error) {
          if (error.message.includes('408') || error.message.includes('认证超时')) {
            throw new Error('认证超时，设备码已过期，请重新开始')
          }
          if (error.message.includes('400') || error.message.includes('设备码无效')) {
            throw new Error('设备码无效，请重新获取')
          }
        }
        // 其他错误继续重试
        await this.sleep(currentInterval)
      }
    }

    throw new Error('认证超时，请重试')
  }

  /**
   * 延迟函数
   */
  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms))
  }
}

// ============================================================================
// 导出单例
// ============================================================================

/**
 * Qwen OAuth API 服务单例
 */
export const qwenOAuthApiService = new QwenOAuthApiService()

// ============================================================================
// 便捷函数
// ============================================================================

/**
 * 获取设备码
 */
export const getDeviceCode = () => qwenOAuthApiService.getDeviceCode()

/**
 * 轮询 OAuth 认证状态
 */
export const pollOAuthStatus = (deviceCode: string) =>
  qwenOAuthApiService.pollOAuthStatus(deviceCode)

/**
 * 带自动重试的状态轮询
 */
export const pollWithRetry = (deviceCode: string, options?: Parameters<QwenOAuthApiService['pollWithRetry']>[1]) =>
  qwenOAuthApiService.pollWithRetry(deviceCode, options)
