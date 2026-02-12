/**
 * 测试数据工厂模块
 * 提供统一的测试数据生成函数
 * 确保所有测试数据使用 test_ 前缀
 */

/**
 * 测试数据配置
 */
const TEST_DATA_PREFIX = 'test_'

/**
 * 生成唯一的测试配置名称
 *
 * @returns {string} 测试配置名称
 */
export function createTestModelConfigName(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `${TEST_DATA_PREFIX}config_${timestamp}_${random}`
}

/**
 * 生成测试用户名（如需要）
 *
 * @returns {string} 测试用户名
 */
export function createTestUserName(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `${TEST_DATA_PREFIX}user_${timestamp}_${random}`
}

/**
 * 生成唯一的 ID（时间戳+随机数）
 *
 * @returns {string} 唯一 ID
 */
export function generateUniqueId(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `${timestamp}_${random}`
}

/**
 * 创建测试模型配置对象
 *
 * @param {Partial<ModelConfig>} overrides - 可选的覆盖字段
 * @returns {ModelConfig} 测试模型配置对象
 *
 * @example
 * // 使用默认值
 * const config = createTestModelConfig()
 *
 * // 覆盖特定字段
 * const config = createTestModelConfig({
 *   provider: 'deepseek',
 *   models: [{ model_id: 'deepseek-chat', support_vision: true, support_thinking: false }]
 * })
 */
export function createTestModelConfig(overrides: Partial<ModelConfig> = {}): ModelConfig {
  const defaultConfig: ModelConfig = {
    id: 1,
    name: createTestModelConfigName(),
    provider: 'openai',
    base_url: createTestBaseUrl(),
    api_key: createTestApiKey(),
    models: [
      {
        model_id: createTestModelId(),
        support_vision: false,
        support_thinking: false
      }
    ],
    is_active: true,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }

  return {
    ...defaultConfig,
    ...overrides,
    // 确保 id 字段正确合并
    id: overrides.id ?? defaultConfig.id
  }
}

/**
 * 生成唯一的模型 ID
 *
 * @returns {string} 模型 ID
 */
export function createTestModelId(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `model_${timestamp}_${random}`
}

/**
 * 生成唯一的 API Key
 *
 * @returns {string} API Key
 */
export function createTestApiKey(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `sk-test-${timestamp}_${random}`
}

/**
 * 生成唯一的 Base URL
 *
 * @returns {string} Base URL
 */
export function createTestBaseUrl(): string {
  return 'https://api.test.com'
}

/**
 * 类型定义：模型信息
 */
interface ModelInfo {
  model_id: string
  support_vision: boolean
  support_thinking: boolean
}

/**
 * 类型定义：模型配置
 */
interface ModelConfig {
  id: number
  name: string
  provider: string
  base_url: string
  api_key: string
  models: ModelInfo[]
  is_active: boolean
  created_at: string
  updated_at: string
}

// 导出类型供测试使用
export type { ModelConfig, ModelInfo }
