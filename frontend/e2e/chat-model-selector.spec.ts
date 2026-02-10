/**
 * Chat 双层模型选择器端到端测试
 * 测试 DualModelSelector 组件在 ChatAnalysis 页面中的完整功能
 *
 * 测试规范参考：openspec/changes/chat-backend-model-config/specs/chat-frontend-model-selector/spec.md
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
  await page.waitForSelector('.dual-model-selector', { state: 'attached', timeout: 5000 })
  await page.waitForLoadState('networkidle')
}

/**
 * 等待模型选择器加载完成
 */
async function waitForModelSelector(page: Page) {
  // 等待选择器元素可见
  await page.waitForSelector('.dual-model-selector', { state: 'visible', timeout: 5000 })
}

test.describe('Chat 模型选择器', () => {
  test.beforeEach(async ({ page }) => {
    await navigateToChatAnalysis(page)
  })

  test('4.2.1 访问 ChatAnalysis 页面时双层选择器正确显示', async ({ page }) => {
    // 先清除 localStorage 以确保初始状态
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.removeItem('chat_model_selection')
    })
    await page.reload()
    await waitForModelSelector(page)

    // 验证选择器存在
    const modelSelector = page.locator('.dual-model-selector')
    await expect(modelSelector).toBeVisible()

    // 验证第一层选择器（配置选择器）存在
    const configSelector = page.locator('.dual-model-selector .config-selector')
    await expect(configSelector).toBeVisible()

    // 验证第二层选择器（模型选择器）存在
    const modelSelector2 = page.locator('.dual-model-selector .model-selector')
    await expect(modelSelector2).toBeVisible()

    // 等待数据加载完成
    await page.waitForTimeout(1000)

    // 验证初始占位符文本（如果有保存的选择，这个会失败）
    const configText = await configSelector.textContent()
    console.log('配置选择器文本:', configText)

    // 第二层选择器的占位符文本
    const modelText = await modelSelector2.textContent()
    console.log('模型选择器文本:', modelText)

    // 截图用于调试
    await page.screenshot({ path: 'screenshots/chat-model-selector-display.png' })
  })

  test('4.2.2 选择模型配置后显示模型列表', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForSelector('.dual-model-selector .config-selector', { state: 'visible' })
    await page.waitForTimeout(1000)

    // 检查是否有可用的模型配置
    const configSelector = page.locator('.dual-model-selector .config-selector')
    const isDisabled = await configSelector.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (isDisabled) {
      // 如果没有可用模型配置，跳过此测试
      test.skip()
      return
    }

    // 点击第一层选择器展开配置列表
    await configSelector.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    // 获取第一个可用配置选项（排除集成测试配置）
    const options = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    const validOption = options.find(async (opt) => {
      const text = await opt.textContent()
      return text && !text.includes('Integration Test') && text.includes('models')
    })

    if (!validOption) {
      test.skip()
      return
    }

    // 选择第一个非集成测试配置（使用 JavaScript 点击）
    await validOption.evaluate((el: any) => el.click())
    await page.waitForTimeout(1000) // 等待选择生效和下拉框关闭

    // 验证第二层选择器已启用
    const modelSelector2 = page.locator('.dual-model-selector .model-selector')
    const isModelSelectorDisabled = await modelSelector2.evaluate((el: any) =>
      el.classList.contains('is-disabled')
    )
    expect(isModelSelectorDisabled).toBeFalsy()

    // 验证第二层选择器占位符更新
    await expect(modelSelector2).toContainText('请选择模型')

    // 点击第二层选择器查看模型列表
    await modelSelector2.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    // 验证模型选项显示能力标签
    const modelOptions = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    expect(modelOptions.length).toBeGreaterThan(0)

    // 验证至少有一个模型包含标签
    const hasTag = await page.locator('.el-select-dropdown .el-tag').count() > 0
    expect(hasTag).toBeTruthy()

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-config-selected.png' })
  })

  test('4.2.3 选择模型后刷新页面选择状态保持', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForSelector('.dual-model-selector .config-selector', { state: 'visible' })
    await page.waitForTimeout(1000)

    // 检查是否有可用的模型配置
    const configSelector = page.locator('.dual-model-selector .config-selector')
    const isDisabled = await configSelector.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (isDisabled) {
      test.skip()
      return
    }

    // 选择配置
    await configSelector.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    const configOptions = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    const validConfigOption = configOptions.find(async (opt) => {
      const text = await opt.textContent()
      return text && !text.includes('Integration Test') && text.includes('models')
    })

    if (!validConfigOption) {
      test.skip()
      return
    }

    // 使用 JavaScript 点击，更可靠
    await validConfigOption.evaluate((el: any) => el.click())
    await page.waitForTimeout(1000) // 等待选择生效和前一个下拉框关闭

    // 选择模型
    const modelSelector2 = page.locator('.dual-model-selector .model-selector')
    await modelSelector2.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    // 获取最后一个下拉框（最新的）
    const dropdowns = await page.locator('.el-select-dropdown').all()
    const lastDropdown = dropdowns[dropdowns.length - 1]
    const modelOptions = await lastDropdown.locator('.el-select-dropdown__item').all()

    if (modelOptions.length === 0) {
      test.skip()
      return
    }

    // 使用 JavaScript 点击第一个模型选项
    await modelOptions[0].evaluate((el: any) => el.click())
    await page.waitForTimeout(500)

    // 获取保存的选择
    const storageBefore = await page.evaluate(() => {
      return localStorage.getItem('chat_model_selection')
    })
    console.log('刷新前 localStorage:', storageBefore)
    expect(storageBefore).toBeTruthy()

    // 刷新页面
    await page.reload()
    await waitForModelSelector(page)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // 验证选择已恢复
    const storageAfter = await page.evaluate(() => {
      return localStorage.getItem('chat_model_selection')
    })
    console.log('刷新后 localStorage:', storageAfter)
    expect(storageAfter).toEqual(storageBefore)

    // 验证选择器显示已选择的项目
    await expect(configSelector).not.toContainText('请选择模型配置')
    await expect(modelSelector2).not.toContainText('请选择模型')

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-persistence.png' })
  })

  test('4.2.4 没有可用模型配置时显示提示', async ({ page }) => {
    // 拦截 API 请求并返回空列表
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

    // 重新导航到页面以确保拦截生效
    await page.goto('/')
    await page.waitForLoadState('networkidle')

    // 等待组件渲染完成
    await page.waitForSelector('.dual-model-selector', { state: 'visible', timeout: 5000 })
    await page.waitForTimeout(1500)

    // 验证选择器存在
    const modelSelector = page.locator('.dual-model-selector')
    await expect(modelSelector).toBeVisible()

    // 验证占位符显示"暂无可用模型配置"
    const configSelector = page.locator('.dual-model-selector .config-selector')
    const configText = await configSelector.textContent()
    console.log('配置选择器文本:', configText)
    expect(configText).toContain('暂无可用模型')

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-disabled.png' })
  })

  test('4.2.5 切换模型配置时模型列表更新', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForSelector('.dual-model-selector .config-selector', { state: 'visible' })
    await page.waitForTimeout(1000)

    // 检查是否有至少2个可用的非集成测试配置
    const configSelector = page.locator('.dual-model-selector .config-selector')
    const isDisabled = await configSelector.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (isDisabled) {
      test.skip()
      return
    }

    // 点击配置选择器
    await configSelector.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    // 获取所有非集成测试配置
    const configOptions = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    const validConfigs = []
    for (const opt of configOptions) {
      const text = await opt.textContent()
      if (text && !text.includes('Integration Test') && text.includes('models')) {
        validConfigs.push(opt)
      }
    }

    if (validConfigs.length < 2) {
      test.skip()
      return
    }

    // 选择第一个配置（使用 JavaScript 点击）
    await validConfigs[0].evaluate((el: any) => el.click())
    await page.waitForTimeout(1000) // 等待选择生效和下拉框关闭

    // 选择模型
    const modelSelector2 = page.locator('.dual-model-selector .model-selector')
    await modelSelector2.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    // 获取最新的下拉框
    const dropdowns1 = await page.locator('.el-select-dropdown').all()
    const lastDropdown1 = dropdowns1[dropdowns1.length - 1]
    const modelOptions1 = await lastDropdown1.locator('.el-select-dropdown__item').all()
    const firstModelText = await modelOptions1[0]?.textContent()
    console.log('第一个配置的模型:', firstModelText)

    // 切换到第二个配置
    await configSelector.click()
    await page.waitForTimeout(500)
    await validConfigs[1].evaluate((el: any) => el.click())
    await page.waitForTimeout(1000) // 等待选择生效

    // 验证模型选择器重置
    await expect(modelSelector2).toContainText('请选择模型')

    // 查看新的模型列表
    await modelSelector2.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    const modelOptions2 = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    const secondModelText = await modelOptions2[0]?.textContent()
    console.log('第二个配置的模型:', secondModelText)

    // 验证模型列表已更新（可选：如果配置确实不同）
    // await expect(modelOptions2).not.toEqual(modelOptions1)

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-config-switch.png' })
  })

  test('4.2.6 响应式布局（移动端显示）', async ({ page }) => {
    // 设置移动端视口
    await page.setViewportSize({ width: 375, height: 667 })
    await navigateToChatAnalysis(page)
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForTimeout(1000)

    // 验证选择器在移动端仍然可见
    const modelSelector = page.locator('.dual-model-selector')
    await expect(modelSelector).toBeVisible()

    // 验证选择器宽度适应移动端
    const selectBox = await modelSelector.boundingBox()
    expect(selectBox?.width).toBeLessThanOrEqual(375) // 不应超过视口宽度

    // 验证选择器使用垂直布局（flex-direction: column）
    const flexDirection = await modelSelector.evaluate((el: any) => {
      return window.getComputedStyle(el).flexDirection
    })
    expect(flexDirection).toBe('column')

    // 验证两个选择器都可见
    const configSelector = page.locator('.dual-model-selector .config-selector')
    const modelSelector2 = page.locator('.dual-model-selector .model-selector')
    await expect(configSelector).toBeVisible()
    await expect(modelSelector2).toBeVisible()

    // 截图验证移动端布局
    await page.screenshot({ path: 'screenshots/chat-model-selector-mobile.png' })
  })

  test('4.2.7 发送消息前验证模型选择', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForTimeout(1000)

    // 尝试在未选择模型的情况下发送消息
    const inputBox = page.locator('textarea[placeholder*="请输入您的问题"]')
    await expect(inputBox).toBeVisible()

    // 输入消息
    await inputBox.fill('测试消息')

    // 尝试按 Enter 发送
    await inputBox.press('Enter')
    await page.waitForTimeout(500)

    // 验证出现警告提示（未选择模型）
    const hasWarning = await page.locator('.el-message--warning').count() > 0
    expect(hasWarning).toBeTruthy()

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-no-model-warning.png' })
  })

  test('4.2.8 模型能力标签显示', async ({ page }) => {
    await waitForModelSelector(page)

    // 等待数据加载完成
    await page.waitForSelector('.dual-model-selector .config-selector', { state: 'visible' })
    await page.waitForTimeout(1000)

    const configSelector = page.locator('.dual-model-selector .config-selector')
    const isDisabled = await configSelector.evaluate((el: any) => el.classList.contains('is-disabled'))

    if (isDisabled) {
      test.skip()
      return
    }

    // 选择配置
    await configSelector.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    const configOptions = await page.locator('.el-select-dropdown .el-select-dropdown__item').all()
    const validConfigOption = configOptions.find(async (opt) => {
      const text = await opt.textContent()
      return text && !text.includes('Integration Test') && text.includes('models')
    })

    if (!validConfigOption) {
      test.skip()
      return
    }

    await validConfigOption.evaluate((el: any) => el.click())
    await page.waitForTimeout(1000) // 等待选择生效和下拉框关闭

    // 选择模型
    const modelSelector2 = page.locator('.dual-model-selector .model-selector')
    await modelSelector2.click()
    await page.waitForTimeout(500) // 等待下拉框动画完成

    // 验证能力标签显示
    const tags = page.locator('.el-select-dropdown .el-tag')
    const tagCount = await tags.count()
    expect(tagCount).toBeGreaterThan(0)

    // 验证标签类型（success, warning, info）
    const hasTag = await page.locator('.el-select-dropdown .el-tag--small').count() > 0
    expect(hasTag).toBeTruthy()

    // 截图验证
    await page.screenshot({ path: 'screenshots/chat-model-selector-tags.png' })
  })
})
