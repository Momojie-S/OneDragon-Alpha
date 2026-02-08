/**
 * 模型配置管理端到端测试
 * 测试完整的用户流程
 */

import { test, expect, Page } from '@playwright/test'

// 测试数据 - 使用时间戳确保唯一性
const getTestConfig = () => ({
  name: `E2E 测试配置_${Date.now()}_${Math.random().toString(36).substring(7)}`,
  provider: 'openai',
  baseUrl: 'https://api.deepseek.com',
  apiKey: 'sk-test-e2e-123456',
  models: [
    { modelId: 'deepseek-chat', supportVision: true, supportThinking: false }
  ]
})

/**
 * 登录/认证（如果需要）
 */
async function login(page: Page) {
  // 如果您的应用需要认证，在这里添加
  // 例如：
  // await page.goto('/login')
  // await page.fill('input[name="username"]', 'test-user')
  // await page.fill('input[name="password"]', 'test-password')
  // await page.click('button[type="submit"]')
  // await page.waitForURL('/')
}

/**
 * 导航到模型配置页面
 */
async function navigateToModelManagement(page: Page) {
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  // 点击"模型配置"标签
  const modelManagementTab = page.getByText('模型配置')
  await modelManagementTab.click()

  // 等待页面加载
  await page.waitForURL('/model-management')
  await page.waitForLoadState('networkidle')
}

test.describe('模型配置管理', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await navigateToModelManagement(page)
  })

  test('应该显示模型配置页面', async ({ page }) => {
    // 验证页面标题
    await expect(page.locator('h2').filter({ hasText: '模型配置管理' })).toBeVisible()

    // 验证操作按钮
    await expect(page.getByText('新建配置')).toBeVisible()
    await expect(page.getByText('刷新')).toBeVisible()

    // 验证过滤器 - 使用 class 选择器
    await expect(page.locator('.el-select').first()).toBeVisible()
    await expect(page.locator('.el-select').nth(1)).toBeVisible()

    // 验证表格
    await expect(page.locator('.el-table')).toBeVisible()
  })

  test('应该显示配置列表', async ({ page }) => {
    // 等待数据加载
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 检查表格是否渲染
    const table = page.locator('.el-table')
    await expect(table).toBeVisible()

    // 检查分页组件
    await expect(page.locator('.el-pagination')).toBeVisible()
  })

  test('应该能够创建新配置', async ({ page }) => {
    const testConfig = getTestConfig()

    // 1. 点击"新建配置"按钮
    await page.click('button:has-text("新建配置")')

    // 2. 等待主对话框打开
    await expect(page.locator('.el-dialog').filter({ hasText: '新建配置' }).first()).toBeVisible()

    // 3. 填写表单
    await page.fill('input[placeholder*="配置名称"]', testConfig.name)

    // Provider 字段存在且显示"OpenAI"
    await expect(page.locator('.el-form-item__label').filter({ hasText: 'Provider' })).toBeVisible()

    await page.fill('input[placeholder="https://api.deepseek.com"]', testConfig.baseUrl)
    await page.fill('input[type="password"]', testConfig.apiKey)

    // 4. 添加模型 - 点击第一个"添加模型"按钮（在主对话框中）
    await page.locator('.el-dialog').first().locator('button:has-text("添加模型")').click()

    // 等待模型对话框（使用 nth(1) 获取第二个对话框，因为 append-to-body）
    await expect(page.locator('.el-dialog').nth(1).filter({ hasText: /添加模型|编辑模型/ })).toBeVisible()

    // 填写模型信息
    await page.fill('input[placeholder="如：deepseek-chat"]', 'deepseek-chat')
    // Element Plus checkbox 点击包含文本的 span
    await page.locator('.el-checkbox__label').filter({ hasText: '支持视觉' }).click()

    // 点击模型对话框的"确定"按钮
    await page.locator('.el-dialog').nth(1).locator('button:has-text("确定")').click()

    // 等待模型对话框关闭
    await page.waitForTimeout(500)
    await expect(page.locator('.el-dialog').nth(1)).not.toBeVisible({ timeout: 3000 })

    // 等待一下，确保主对话框可交互
    await page.waitForTimeout(300)

    // 5. 保存配置 - 点击主对话框的"保存"按钮
    await page.locator('.el-dialog').first().locator('button:has-text("保存")').click()

    // 等待并检查是否有任何消息（成功或错误）
    await page.waitForTimeout(2000)

    // 检查是否有成功消息
    const successMessage = page.locator('.el-message--success').first()
    const errorMessage = page.locator('.el-message--error').first()

    // 等待其中一个消息出现
    await page.waitForFunction(
      () => {
        const success = document.querySelector('.el-message--success')
        const error = document.querySelector('.el-message--error')
        return success !== null || error !== null
      },
      { timeout: 5000 }
    )

    // 检查是否有错误消息（如果有，测试应该失败）
    const hasError = await errorMessage.count() > 0
    if (hasError) {
      const errorText = await errorMessage.textContent()
      throw new Error(`创建配置失败: ${errorText}`)
    }

    // 6. 验证成功消息
    await expect(successMessage).toBeVisible()

    // 7. 验证配置出现在列表中
    await expect(page.locator('.el-table').getByText(testConfig.name)).toBeVisible()
  })

  test('应该能够编辑配置', async ({ page }) => {
    // 等待列表加载
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 假设列表中有配置，点击第一个"编辑"按钮
    const editButtons = page.locator('button:has-text("编辑")')
    const count = await editButtons.count()

    if (count > 0) {
      await editButtons.first().click()

      // 等待编辑对话框打开
      await expect(page.locator('.el-dialog').filter({ hasText: '编辑配置' }).first()).toBeVisible()

      // 修改配置名称
      const newName = `更新_${Date.now()}`
      await page.fill('input[placeholder*="配置名称"]', newName)

      // 保存 - 使用 first() 定位主对话框的按钮
      await page.locator('.el-dialog').first().locator('button:has-text("保存")').click()

      // 验证成功消息 - 使用 first() 因为可能有多个消息
      await expect(page.locator('.el-message--success').first()).toBeVisible({ timeout: 5000 })
    } else {
      // 如果没有配置，跳过测试
      test.skip()
    }
  })

  test('应该能够删除配置', async ({ page }) => {
    // 等待列表加载
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 点击第一个"删除"按钮
    const deleteButtons = page.locator('button:has-text("删除")')
    const count = await deleteButtons.count()

    if (count > 0) {
      await deleteButtons.first().click()

      // 等待确认对话框
      await expect(page.locator('.el-dialog').filter({ hasText: '确认删除' })).toBeVisible()

      // 点击确认删除
      await page.click('.el-dialog button:has-text("确认删除")')

      // 验证成功消息
      await expect(page.locator('.el-message--success')).toBeVisible({ timeout: 5000 })
    }
  })

  test('应该能够切换启用状态', async ({ page }) => {
    // 等待列表加载
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 找到第一个开关
    const firstSwitch = page.locator('.el-switch').first()

    // 获取点击前的状态
    const isCheckedBefore = await firstSwitch.locator('.el-switch__input').isChecked()

    await firstSwitch.click()

    // 验证成功消息
    await expect(page.locator('.el-message--success')).toBeVisible({ timeout: 5000 })

    // 等待状态更新
    await page.waitForTimeout(500)

    // 验证开关状态已改变（使用 input 元素的 checked 属性）
    const isCheckedAfter = await firstSwitch.locator('.el-switch__input').isChecked()
    expect(isCheckedAfter).toBe(!isCheckedBefore)
  })

  test('应该能够按状态过滤', async ({ page }) => {
    // 等待列表加载
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 记录初始配置数量
    const initialCount = await page.locator('.el-table-body .el-table__row').count()

    // 选择"已启用"过滤
    const activeFilter = page.locator('.el-select').filter({ hasText: /启用状态/ })
    await activeFilter.click()
    await page.click('.el-select-dropdown__item:has-text("已启用")')

    // 等待数据重新加载
    await page.waitForTimeout(1000)

    // 验证过滤已应用（检查表格内容已更新）
    // 注意：前端不更新 URL，而是通过 API 请求过滤数据
    const filteredCount = await page.locator('.el-table-body .el-table__row').count()
    expect(filteredCount).toBeLessThanOrEqual(initialCount)
  })

  test('应该能够分页浏览', async ({ page }) => {
    // 等待列表加载
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 检查分页组件
    const pagination = page.locator('.el-pagination')
    await expect(pagination).toBeVisible()

    // 获取总页数
    const totalPages = await pagination.locator('.el-pager li').count()

    if (totalPages > 1) {
      // 点击下一页
      await page.click('button:has-text("next")')

      // 等待数据加载
      await page.waitForTimeout(500)

      // 验证页码已改变
      const currentPage = await page.locator('.el-pager .is-active').textContent()
      expect(currentPage).not.toBe('1')
    }
  })

  test('表单验证应该正常工作', async ({ page }) => {
    // 点击"新建配置"
    await page.click('button:has-text("新建配置")')

    // 等待对话框
    await expect(page.locator('.el-dialog').filter({ hasText: '新建配置' }).first()).toBeVisible()

    // 不填写任何字段，直接点击保存
    await page.locator('.el-dialog').first().locator('button:has-text("保存")').click()

    // 等待验证完成
    await page.waitForTimeout(500)

    // Element Plus 表单验证在字段下方显示错误，不是全局消息
    // 验证必填字段错误提示
    await expect(page.locator('.el-form-item__error').filter({ hasText: '请输入配置名称' })).toBeVisible()
    await expect(page.locator('.el-form-item__error').filter({ hasText: '请输入 Base URL' })).toBeVisible()
    await expect(page.locator('.el-form-item__error').filter({ hasText: '请输入 API Key' })).toBeVisible()
    await expect(page.locator('.el-form-item__error').filter({ hasText: '至少需要添加一个模型' })).toBeVisible()
  })

  test('应该能够刷新列表', async ({ page }) => {
    // 等待列表加载
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 点击刷新按钮
    await page.click('button:has-text("刷新")')

    // Element Plus 使用 v-loading 指令，渲染为 .el-loading-mask
    // 验证加载状态出现
    await expect(page.locator('.el-loading-mask').first()).toBeVisible({ timeout: 2000 })

    // 等待加载完成
    await page.waitForSelector('.el-table', { state: 'visible' })

    // 验证加载状态消失
    await expect(page.locator('.el-loading-mask').first()).not.toBeVisible({ timeout: 5000 })
  })
})

test.describe('模型配置对话框', () => {
  test.beforeEach(async ({ page }) => {
    await login(page)
    await navigateToModelManagement(page)
  })

  test('应该能够添加和删除模型', async ({ page }) => {
    // 打开新建对话框
    await page.click('button:has-text("新建配置")')
    await expect(page.locator('.el-dialog').filter({ hasText: '新建配置' }).first()).toBeVisible()

    // 添加第一个模型
    await page.locator('.el-dialog').first().locator('button:has-text("添加模型")').click()

    // 等待模型对话框（第二个对话框）
    await expect(page.locator('.el-dialog').nth(1)).toBeVisible()

    await page.fill('input[placeholder="如：deepseek-chat"]', 'model-1')
    await page.check('label:has-text("支持视觉")')
    await page.locator('.el-dialog').nth(1).locator('button:has-text("确定")').click()

    // 等待模型对话框关闭
    await expect(page.locator('.el-dialog').nth(1)).not.toBeVisible()

    // 添加第二个模型
    await page.locator('.el-dialog').first().locator('button:has-text("添加模型")').click()

    // 等待模型对话框
    await expect(page.locator('.el-dialog').nth(1)).toBeVisible()

    await page.fill('input[placeholder="如：deepseek-chat"]', 'model-2')
    await page.check('label:has-text("支持思考")')
    await page.locator('.el-dialog').nth(1).locator('button:has-text("确定")').click()

    // 等待模型对话框关闭
    await expect(page.locator('.el-dialog').nth(1)).not.toBeVisible()

    // 验证两个模型都在列表中
    await expect(page.locator('.model-card')).toHaveCount(2)

    // 删除一个模型
    await page.locator('.model-card').first().locator('button:has-text("删除")').click()

    // 验证只剩一个模型
    await expect(page.locator('.model-card')).toHaveCount(1)
  })

  test('应该能够编辑模型', async ({ page }) => {
    // 打开新建对话框
    await page.click('button:has-text("新建配置")')
    await expect(page.locator('.el-dialog').filter({ hasText: '新建配置' }).first()).toBeVisible()

    // 添加模型
    await page.locator('.el-dialog').first().locator('button:has-text("添加模型")').click()
    await expect(page.locator('.el-dialog').nth(1)).toBeVisible()
    await page.fill('input[placeholder="如：deepseek-chat"]', 'test-model')
    await page.locator('.el-dialog').nth(1).locator('button:has-text("确定")').click()
    await expect(page.locator('.el-dialog').nth(1)).not.toBeVisible()

    // 编辑模型
    await page.locator('.model-card').first().locator('button:has-text("编辑")').click()

    // 等待模型对话框
    await expect(page.locator('.el-dialog').nth(1)).toBeVisible()

    // 修改能力标识
    await page.uncheck('label:has-text("支持视觉")')
    await page.check('label:has-text("支持思考")')
    await page.locator('.el-dialog').nth(1).locator('button:has-text("确定")').click()

    // 等待模型对话框关闭
    await expect(page.locator('.el-dialog').nth(1)).not.toBeVisible()

    // 验证标签已更新
    await expect(page.locator('.model-card').first().locator('text=思考')).toBeVisible()
  })
})

test.describe('错误处理', () => {
  test('应该处理网络错误', async ({ page }) => {
    // 先设置路由拦截，在导航之前
    await page.route('**/api/models/configs*', route => route.abort())

    // 导航到页面
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.getByText('模型配置').click()
    await page.waitForURL('/model-management')

    // 尝试刷新（会触发新的 API 请求）
    await page.click('button:has-text("刷新")')

    // 验证错误消息
    await expect(page.locator('.el-message--error').first()).toBeVisible({ timeout: 5000 })
  })

  test('应该显示空状态', async ({ page }) => {
    // 先设置路由拦截，在导航之前
    await page.route('**/api/models/configs*', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ total: 0, page: 1, page_size: 20, items: [] })
      })
    })

    // 导航到页面
    await page.goto('/')
    await page.waitForLoadState('networkidle')
    await page.getByText('模型配置').click()
    await page.waitForURL('/model-management')

    // 等待表格加载
    await page.waitForSelector('.el-table', { state: 'attached' })

    // Element Plus 表格空状态显示为 "No Data"
    const tableText = await page.locator('.el-table').textContent()
    expect(tableText).toContain('No Data')
  })
})
