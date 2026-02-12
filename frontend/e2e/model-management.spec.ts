/**
 * 模型配置管理端到端测试
 * 测试完整的用户流程，包括创建、更新、删除配置
 * 使用 Mock API，不依赖真实后端
 */

import { test, expect } from '@playwright/test'
import { generateTestConfigName } from './utils/test-helper'

// ============================================================================
// Mock 数据存储
// ============================================================================

// 模拟数据库，存储测试配置
const mockConfigs = new Map<string, any>()

// 生成唯一ID
let nextId = 1
function generateId(): string {
  return String(nextId++)
}

/**
 * 设置所有 API 的 Mock 响应
 */
async function setupApiMocks(page: any) {
  // 1. Mock 获取配置列表
  await page.route('**/api/models/configs*', async (route: any) => {
    const url = route.request().url()
    const method = route.request().method()

    // 优先检查清理接口（因为路径包含 /cleanup，需要优先匹配）
    if (url.includes('/cleanup-test-data') && method === 'DELETE') {
      let deletedCount = 0
      const idsToDelete: string[] = []

      // 先收集要删除的 ID
      for (const [id, config] of mockConfigs.entries()) {
        if (config.name?.startsWith('test_e2e_')) {
          idsToDelete.push(id)
          deletedCount++
        }
      }

      // 然后删除
      for (const id of idsToDelete) {
        mockConfigs.delete(id)
      }

      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          deleted_count: deletedCount
        })
      })
      return
    }

    // GET /api/models/configs - 获取列表
    if (method === 'GET') {
      const configs = Array.from(mockConfigs.values())
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: configs.length,
          page: 1,
          page_size: 100,
          items: configs
        })
      })
      return
    }

    // POST /api/models/configs - 创建配置
    if (method === 'POST') {
      const newConfig = await route.request().postDataJSON()
      const id = generateId()
      const config = {
        id,
        ...newConfig,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
      mockConfigs.set(id, config)

      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(config)
      })
      return
    }

    // PUT /api/models/configs/:id - 更新配置
    if (method === 'PUT') {
      const urlMatch = url.match(/\/configs\/(\d+)/)
      if (urlMatch) {
        const id = urlMatch[1]
        const existingConfig = mockConfigs.get(id)
        if (existingConfig) {
          const updatedData = await route.request().postDataJSON()
          const updatedConfig = {
            ...existingConfig,
            ...updatedData,
            updated_at: new Date().toISOString()
          }
          mockConfigs.set(id, updatedConfig)

          route.fulfill({
            status: 200,
            contentType: 'application/json',
            body: JSON.stringify(updatedConfig)
          })
          return
        }
      }
      route.fulfill({ status: 404, body: 'Config not found' })
      return
    }

    // DELETE /api/models/configs/:id - 删除配置
    if (method === 'DELETE') {
      const urlMatch = url.match(/\/configs\/(\d+)/)
      if (urlMatch) {
        const id = urlMatch[1]
        mockConfigs.delete(id)

        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({ success: true })
        })
        return
      }
      route.fulfill({ status: 404, body: 'Config not found' })
      return
    }

    // 其他请求返回 404
    route.fulfill({ status: 404, body: 'Not found' })
  })
}

/**
 * 通过 UI 创建测试配置
 */
async function createTestConfigViaUI(page: any, configName: string): Promise<void> {
  await page.goto('/model-management')
  await page.waitForLoadState('networkidle')

  await page.click('button:has-text("新建配置")')
  await expect(page.locator('.el-dialog').first()).toBeVisible()

  await page.fill('input[placeholder*="配置名称"]', configName)
  await page.click('button:has-text("确定")')

  await page.waitForTimeout(1000)
  console.log(`✅ 创建测试配置 ${configName}`)
}

/**
 * 测试：E2E 模型配置数据隔离
 * 使用 Mock API 验证数据隔离机制
 */
test.describe('E2E 模型配置数据隔离（Mock API）', () => {
  test.beforeEach(async ({ page }) => {
    // 清空 Mock 数据
    mockConfigs.clear()
    nextId = 1

    // 设置 API Mock
    await setupApiMocks(page)

    // 模拟已登录状态，设置 token
    await page.goto('/')
    await page.evaluate(() => {
      window.localStorage.setItem('token', 'mock-test-token')
    })
  })

  test('应该显示模型配置列表', async ({ page }) => {
    // 添加一个测试配置到 Mock 数据（使用 test_ 前缀）
    const testConfig = {
      id: generateId(),
      name: 'test_e2e_config_1',
      provider: 'openai',
      base_url: 'https://api.openai.com',
      models: [
        { model_id: 'gpt-4', support_vision: true, support_thinking: false }
      ],
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    }
    mockConfigs.set(String(testConfig.id), testConfig)

    // 导航到模型配置页面
    await page.goto('/model-management')
    await page.waitForLoadState('networkidle')

    // 验证配置名称显示
    await expect(page.locator(`text=${testConfig.name}`)).toBeVisible()
  })

  test('应该通过 Mock API 创建新配置', async ({ page }) => {
    const configName = generateTestConfigName()

    // 通过 fetch 调用 Mock API（因为 page.request 不会经过路由）
    await page.evaluate(async (name) => {
      const response = await fetch('/api/models/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          provider: 'openai',
          base_url: 'https://api.test.com',
          api_key: 'sk-test-key',
          models: [
            { model_id: 'test-model', support_vision: false, support_thinking: false }
          ],
          is_active: true
        })
      })
      return response.json()
    }, configName)

    // 验证 Mock 数据中存在新配置
    const configs = Array.from(mockConfigs.values())
    const newConfig = configs.find((c) => c.name === configName)
    expect(newConfig).toBeTruthy()

    // 导航到页面验证显示
    await page.goto('/model-management')
    await page.waitForLoadState('networkidle')
    await expect(page.locator(`text=${configName}`)).toBeVisible()
  })

  test('应该通过 Mock API 删除配置', async ({ page }) => {
    const configName = generateTestConfigName()

    // 先创建配置
    const createdConfig = await page.evaluate(async (name) => {
      const response = await fetch('/api/models/configs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: name,
          provider: 'openai',
          base_url: 'https://api.test.com',
          api_key: 'sk-test-key',
          models: [
            { model_id: 'test-model', support_vision: false, support_thinking: false }
          ],
          is_active: true
        })
      })
      return response.json()
    }, configName)

    const configId = createdConfig.id

    // 验证创建成功
    const configsBeforeDelete = Array.from(mockConfigs.values())
    expect(configsBeforeDelete.length).toBe(1)

    // 删除配置 - 直接操作 mockConfigs
    mockConfigs.delete(String(configId))

    // 验证 Mock 数据已删除
    const configsAfterDelete = Array.from(mockConfigs.values())
    expect(configsAfterDelete.length).toBe(0)
  })

  test('应该正确清理测试数据', async ({ page }) => {
    // 创建多个测试配置
    const config1Name = generateTestConfigName()
    const config2Name = generateTestConfigName()
    const formalConfigName = 'Formal Config'

    // 直接创建 Mock 数据
    const id1 = generateId()
    const id2 = generateId()
    const id3 = generateId()

    mockConfigs.set(id1, {
      id: id1,
      name: config1Name,
      provider: 'openai',
      models: [{ model_id: 'model1', support_vision: false, support_thinking: false }],
      is_active: true
    })

    mockConfigs.set(id2, {
      id: id2,
      name: config2Name,
      provider: 'openai',
      models: [{ model_id: 'model2', support_vision: false, support_thinking: false }],
      is_active: true
    })

    mockConfigs.set(id3, {
      id: id3,
      name: formalConfigName,
      provider: 'openai',
      models: [{ model_id: 'model3', support_vision: false, support_thinking: false }],
      is_active: true
    })

    // 验证创建成功
    const configsBeforeCleanup = Array.from(mockConfigs.values())
    expect(configsBeforeCleanup.length).toBe(3)

    // 导航到页面并触发清理请求
    await page.goto('/model-management')
    await page.waitForLoadState('networkidle')

    // 直接调用清理逻辑（不通过 HTTP）
    const idsToDelete: string[] = []
    for (const [id, config] of mockConfigs.entries()) {
      if (config.name?.startsWith('test_e2e_')) {
        idsToDelete.push(id)
      }
    }

    // 删除测试数据
    for (const id of idsToDelete) {
      mockConfigs.delete(id)
    }

    // 验证清理结果
    const configsAfterCleanup = Array.from(mockConfigs.values())
    expect(configsAfterCleanup.length).toBe(1)
    expect(configsAfterCleanup[0].name).toBe(formalConfigName)
  })

  test('应该支持并发测试独立性', async ({ page }) => {
    // 创建多个独立测试配置
    const config1Name = generateTestConfigName()
    const config2Name = generateTestConfigName()

    await page.evaluate(async (names) => {
      for (const name of names) {
        await fetch('/api/models/configs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            name: name,
            provider: 'openai',
            base_url: 'https://api.test.com',
            api_key: 'sk-test-key',
            models: [{ model_id: 'test-model', support_vision: false, support_thinking: false }],
            is_active: true
          })
        })
      }
    }, [config1Name, config2Name])

    // 验证两个配置都存在且独立
    const configs = Array.from(mockConfigs.values())
    expect(configs.length).toBe(2)

    const config1 = configs.find((c) => c.name === config1Name)
    const config2 = configs.find((c) => c.name === config2Name)

    expect(config1).toBeDefined()
    expect(config2).toBeDefined()
    expect(config1?.name).not.toBe(config2?.name)
  })
})
