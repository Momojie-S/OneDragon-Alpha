import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright 测试配置
 * 支持在无界面 Ubuntu 服务器上运行（Headless 模式）
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html'],
    ['json', { outputFile: 'playwright-report/results.json' }],
    ['junit', { outputFile: 'playwright-report/results.xml' }]
  ],

  use: {
    // Base URL for tests
    baseURL: process.env.BASE_URL || 'http://localhost:21002',

    // 无头模式（无界面服务器必需）
    headless: true,

    // 浏览器视口大小
    viewport: { width: 1280, height: 720 },

    // 捕获追踪信息（失败时）
    trace: 'on-first-retry',

    // 截图（失败时）
    screenshot: 'only-on-failure',

    // 视频录制（可选）
    video: 'retain-on-failure',

    // 超时设置
    actionTimeout: 10 * 1000,
    navigationTimeout: 30 * 1000,
  },

  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // 如果系统已有 Chromium，可以指定路径
        // channel: 'chrome', // 或 'chromium'
      },
    },

    // 可选：添加其他浏览器
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
  ],

  // 开发服务器（可选）
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:21002',
    reuseExistingServer: !process.env.CI,
    timeout: 120 * 1000,
  },
})
