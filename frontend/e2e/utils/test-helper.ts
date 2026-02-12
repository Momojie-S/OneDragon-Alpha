/**
 * E2E 测试辅助工具模块
 * 提供统一的测试数据生成、清理、页面导航等函数
 */
import { Page } from '@playwright/test'

/**
 * 测试配置
 */
const TEST_CONFIG = {
  token: process.env.TEST_TOKEN || 'test-token-123',
  baseUrl: 'http://localhost:21003',
  dataPrefix: 'test_e2e_'
}

/**
 * 生成唯一的测试配置名称
 * 格式: test_e2e_config_<timestamp>_<random>
 *
 * @returns {string} 测试配置名称
 */
export function generateTestConfigName(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `${TEST_CONFIG.dataPrefix}config_${timestamp}_${random}`
}

/**
 * 生成唯一的测试用户名（如需要）
 * 格式: test_e2e_user_<timestamp>_<random>
 *
 * @returns {string} 测试用户名
 */
export function generateTestUserName(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `${TEST_CONFIG.dataPrefix}user_${timestamp}_${random}`
}

/**
 * 创建测试配置
 * 通过 API 调用后端创建测试模型配置
 *
 * @param {Page} page - Playwright Page 对象
 * @param {string} configName - 配置名称
 * @returns {Promise<void>}
 */
export async function createTestConfig(
  page: Page,
  configName: string
): Promise<void> {
  const config = {
    name: configName,
    provider: 'openai',
    base_url: 'https://api.deepseek.com',
    api_key: 'sk-test-e2e-123456',
    models: [
      {
        model_id: 'deepseek-chat',
        support_vision: true,
        support_thinking: false
      }
    ],
    is_active: true
  }

  const response = await page.request.post(
    `${TEST_CONFIG.baseUrl}/api/models/configs`,
    {
      headers: {
        'Content-Type': 'application/json',
        'x-test-token': TEST_CONFIG.token
      },
      data: config
    }
  )

  if (response.ok()) {
    console.log(`✅ 创建测试配置: ${configName}`)
  } else {
    console.error(`❌ 创建测试配置失败: ${response.status()}`)
    throw new Error(`创建测试配置失败: ${response.status()}`)
  }
}

/**
 * 清理测试数据
 * 调用后端清理接口，删除所有 test_e2e_ 前缀的数据
 *
 * @param {Page} page - Playwright Page 对象
 * @returns {Promise<{success: boolean, deletedCount: number}>}
 */
export async function cleanupTestData(
  page: Page
): Promise<{ success: boolean; deletedCount: number }> {
  const response = await page.request.delete(
    `${TEST_CONFIG.baseUrl}/api/models/configs/cleanup-test-data`,
    {
      headers: {
        'x-test-token': TEST_CONFIG.token
      }
    }
  )

  if (response.ok()) {
    const result = await response.json()
    console.log(`✅ 清理测试数据成功，删除 ${result.deleted_count} 条记录`)
    return { success: true, deletedCount: result.deleted_count || 0 }
  } else {
    console.warn(`⚠️ 清理测试数据失败: ${response.status()}`)
    return { success: false, deletedCount: 0 }
  }
}

/**
 * 导航到模型配置管理页面
 *
 * @param {Page} page - Playwright Page 对象
 * @returns {Promise<void>}
 */
export async function navigateToModelManagement(page: Page): Promise<void> {
  await page.goto('/model-management')
  await page.waitForLoadState('networkidle')
  console.log('✅ 导航到模型配置管理页面')
}

/**
 * 登录并获取测试令牌
 * 注意：当前实现为简化版，直接返回环境变量中的令牌
 * 在生产环境中，这个函数需要实现真实的登录流程
 *
 * @param {Page} page - Playwright Page 对象
 * @returns {Promise<string>} 测试令牌
 */
export async function loginAndGetTestToken(page: Page): Promise<string> {
  // 简化实现：直接返回环境变量中的令牌
  // TODO: 生产环境需要实现真实的登录流程

  const token = TEST_CONFIG.token
  console.log('✅ 获取测试令牌')

  return token
}
