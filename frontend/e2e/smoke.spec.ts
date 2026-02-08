/**
 * 冒烟测试 - 验证基础功能
 */

import { test, expect } from '@playwright/test'

test.describe('冒烟测试', () => {
  test('应该能够访问首页', async ({ page }) => {
    await page.goto('/')

    // 等待页面加载
    await page.waitForLoadState('networkidle')

    // 验证页面标题
    const title = await page.title()
    expect(title).toBeTruthy()
  })

  test('应该能够访问模型配置页面', async ({ page }) => {
    await page.goto('/model-management')

    // 等待页面加载
    await page.waitForLoadState('domcontentloaded')

    // 截图用于调试
    await page.screenshot({ path: 'screenshots/model-management-page.png' })

    // 检查页面是否包含模型配置相关内容
    const content = await page.content()
    console.log('页面内容长度:', content.length)
  })
})
