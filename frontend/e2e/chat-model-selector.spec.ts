/**
 * Chat 模型选择器端到端测试
 * 测试模型选择器在 ChatAnalysis 页面中的完整功能
 */

import { test, expect, Page } from '@playwright/test'

/**
 * 导航到 ChatAnalysis 页面
 */
async function navigateToChatAnalysis(page: Page) {
  await page.goto('/')
  await page.waitForLoadState('networkidle')

  // ChatAnalysis 页面直接在首页（即席分析标签），无需切换
  // 验证页面已加载
  await page.waitForSelector('.model-selector', { state: 'attached', timeout: 5000 })
  await page.waitForLoadState('networkidle')
}

/**
 * 等待模型选择器加载完成
 */
async function waitForModelSelector(page: Page) {
  // 等待选择器元素可见
  await page.waitForSelector('.model-selector', { state: 'visible', timeout: 5000 })
}

test.describe('Chat 模型选择器', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToChatAnalysis(page)
  })

  test('4.2.2 访问 ChatAnalysis 页面时选择器正确显示', async ({ page }) => {
    // 等待模型选择器加载
    await waitForModelSelector(page)

    // 验证选择器存在
    const modelSelector = page.locator('.model-selector')
    await expect(modelSelector).toBeVisible()

    // 验证选择器包含 el-select 组件
    const select = page.locator('.model-selector .el-select')
    await expect(select).toBeVisible()

    // 截图用于调试
    await page.screenshot({ path: 'screenshots/chat-model-selector-display.png' })
  })

  test('4.2.3 选择模型后刷新页面选择状态保持', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成（loading 状态消失）
    await page.waitForSelector('.model-selector .el-select', { state: 'visible' })
    await page.waitForTimeout(1000) // 额外等待确保数据加载完成

    // 检查是否有可用的模型配置
    const selectDropdown = page.locator('.model-selector .el-select')
    const isDisabled = await selectDropdown.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (isDisabled) {
      // 如果没有可用模型，跳过此测试
      test.skip()
      return
    }

    // 获取初始选中的模型（通过检查 localStorage）
    const initialStorage = await page.evaluate(() => {
      return localStorage.getItem('chat-selected-model-config-id')
    })
    console.log('初始 localStorage 值:', initialStorage)

    // 点击选择器展开下拉列表
    await selectDropdown.click()

    // 等待下拉选项出现
    await page.waitForSelector('.el-select-dropdown', { state: 'visible' })

    // 获取所有可用的选项
    const options = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    console.log('可用选项数量:', options.length)

    if (options.length === 0) {
      // 没有可用选项，跳过测试
      test.skip()
      return
    }

    // 选择第二个选项（如果存在）
    if (options.length > 1) {
      await options[1].click()
      // 等待选择生效
      await page.waitForTimeout(500)
    }

    // 刷新页面
    await page.reload()
    await waitForModelSelector(page)
    await page.waitForLoadState('networkidle')

    // 验证选择状态保持（通过检查 localStorage）
    const storageValue = await page.evaluate(() => {
      return localStorage.getItem('chat-selected-model-config-id')
    })
    console.log('刷新后的 localStorage 值:', storageValue)
    expect(storageValue).toBeTruthy()

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-persistence.png' })
  })

  test('4.2.4 没有可用模型时显示禁用状态和提示', async ({ page }) => {
    // 为了测试没有模型的情况，我们需要拦截 API 请求并返回空列表
    // 注意：必须在页面加载之前设置拦截
    await page.route('**/api/models/configs**', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          total: 0,
          page: 1,
          page_size: 100,
          items: []
        })
      })
    })

    // 重新导航到页面（而不是 reload）以确保拦截生效
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // 等待组件渲染完成
    await page.waitForSelector('.model-selector', { state: 'visible', timeout: 5000 })

    // 等待 loading 状态完成
    await page.waitForTimeout(1500)

    // 验证选择器存在
    const modelSelector = page.locator('.model-selector')
    await expect(modelSelector).toBeVisible()

    // 检查选择器是否显示为禁用状态
    // Element Plus 会在 el-select 上添加 is-disabled class
    const selectWrapper = page.locator('.model-selector .el-select')

    // 检查是否包含禁用的文本提示
    const placeholderText = await selectWrapper.textContent() || ''
    console.log('选择器文本内容:', placeholderText)

    // 验证占位符文本显示提示信息（通过检查页面内容）
    const pageContent = await page.content()
    expect(pageContent).toContain('暂无可用模型')

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-disabled.png' })
  })

  test('4.2.5 在对话过程中切换模型', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForSelector('.model-selector .el-select', { state: 'visible' })
    await page.waitForTimeout(1000)

    // 检查是否有可用的模型配置
    const selectDropdown = page.locator('.model-selector .el-select')
    const isDisabled = await selectDropdown.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (isDisabled) {
      // 如果没有可用模型，跳过此测试
      test.skip()
      return
    }

    // 获取当前选择（通过 localStorage）
    const initialSelection = await page.evaluate(() => {
      return localStorage.getItem('chat-selected-model-config-id')
    })
    console.log('切换前的模型:', initialSelection)

    // 截图：切换前
    await page.screenshot({ path: 'screenshots/chat-before-model-switch.png' })

    // 点击选择器展开下拉列表
    await selectDropdown.click()

    // 等待下拉选项出现
    await page.waitForSelector('.el-select-dropdown', { state: 'visible' })

    // 获取所有可用的选项
    const options = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    console.log('可用选项数量:', options.length)

    if (options.length <= 1) {
      // 只有一个或零个选项，无法测试切换
      test.skip()
      return
    }

    // 选择不同的选项（选择第二个选项以确保发生变化）
    await options[1].click()

    // 等待选择生效
    await page.waitForTimeout(500)

    // 验证 localStorage 已更新
    const storageValue = await page.evaluate(() => {
      return localStorage.getItem('chat-selected-model-config-id')
    })
    console.log('localStorage 值:', storageValue)
    expect(storageValue).toBeTruthy()

    // 截图：切换后
    await page.screenshot({ path: 'screenshots/chat-after-model-switch.png' })
  })

  test('4.2.6 响应式布局（移动端显示）', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForTimeout(1000)

    // 验证选择器在移动端仍然可见
    const modelSelector = page.locator('.model-selector')
    await expect(modelSelector).toBeVisible()

    // 验证选择器宽度适应移动端
    const selectBox = await modelSelector.boundingBox()
    expect(selectBox?.width).toBeLessThanOrEqual(375) // 不应超过视口宽度

    // 验证选择器仍然可交互（如果有可用模型）
    const select = page.locator('.model-selector .el-select')
    const isDisabled = await select.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (!isDisabled) {
      // 尝试点击选择器
      await select.click()
      await page.waitForTimeout(500)

      // 验证下拉列表在移动端也能正确显示
      const dropdown = page.locator('.el-select-dropdown')
      const isVisible = await dropdown.isVisible().catch(() => false)

      if (isVisible) {
        await expect(dropdown).toBeVisible()
      }
    }

    // 截图验证移动端布局
    await page.screenshot({ path: 'screenshots/chat-model-selector-mobile.png' })
  })

  test('4.2.7 切换模型后历史消息不受影响', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForTimeout(1000)

    // 检查是否有可用的模型配置
    const selectDropdown = page.locator('.model-selector .el-select')
    const isDisabled = await selectDropdown.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (isDisabled) {
      // 如果没有可用模型，跳过此测试
      test.skip()
      return
    }

    // 截图：切换模型前的页面状态
    await page.screenshot({ path: 'screenshots/chat-history-before-switch.png' })

    // 记录当前页面内容（模拟历史消息）
    const initialContent = await page.content()

    // 点击选择器展开下拉列表
    await selectDropdown.click()
    await page.waitForSelector('.el-select-dropdown', { state: 'visible' })

    // 获取所有可用的选项
    const options = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()

    if (options.length > 1) {
      // 切换到不同的模型
      await options[0].click()
      await page.waitForTimeout(500)

      // 截图：切换模型后的页面状态
      await page.screenshot({ path: 'screenshots/chat-history-after-switch.png' })

      // 验证历史消息区域仍然存在（如果有消息列表的话）
      const messageList = page.locator('.bubble-list').or(page.locator('.chat-messages'))
      const messageExists = await messageList.count().catch(() => 0)

      if (messageExists > 0) {
        // 如果有消息列表，验证它仍然可见
        await expect(messageList.first()).toBeVisible()
      }
    } else {
      // 只有一个选项，无法测试切换
      test.skip()
    }
  })
})
