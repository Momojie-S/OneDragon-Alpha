# Playwright 端到端测试指南

## 概述

本项目使用 Playwright 进行端到端（E2E）测试，完全支持在无界面的 Ubuntu 服务器上运行。

## 系统要求

### 依赖库（无界面 Ubuntu）

```bash
# 安装必要的系统依赖
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

## 安装步骤

### 1. 安装 Playwright

```bash
cd frontend
pnpm add -D @playwright/test
```

### 2. 安装浏览器（两种方式）

#### 方式 A: 使用 Playwright 安装（推荐）

在有网络的环境：

```bash
npx playwright install chromium
```

#### 方式 B: 使用系统已有浏览器

如果系统已安装 Chromium/Chrome，可以在配置中指定：

```typescript
// playwright.config.ts
use: {
  channel: 'chrome', // 或 'chromium'
}
```

或者设置环境变量：

```bash
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin
```

### 3. 验证安装

```bash
npx playwright --version
```

## 配置文件

### playwright.config.ts

配置文件已优化为无界面服务器运行：

- ✅ **Headless 模式**: 自动启用，不需要图形界面
- ✅ **CI 模式**: 自动检测 CI 环境
- ✅ **截图和视频**: 失败时自动捕获
- ✅ **并行执行**: 加速测试运行
- ✅ **多种报告**: HTML、JSON、JUnit

## 运行测试

### 本地开发（有后端服务）

```bash
# 确保 Vue 开发服务器在运行
pnpm dev

# 在另一个终端运行测试
pnpm exec playwright test

# 或使用配置的脚本
pnpm test:e2e
```

### 指定浏览器

```bash
# Chromium（默认）
pnpm exec playwright test --project=chromium

# Firefox（如果安装了）
pnpm exec playwright test --project=firefox

# WebKit（如果安装了）
pnpm exec playwright test --project=webkit
```

### 调试模式

```bash
# 有界面的调试模式（需要在有显示器的环境）
pnpm exec playwright test --debug

# 显示浏览器窗口（禁用 headless）
HEADLESS=false pnpm exec playwright test
```

### 单个测试文件

```bash
# 运行模型管理测试
pnpm exec playwright test e2e/model-management.spec.ts
```

### 单个测试用例

```bash
# 运行特定测试
pnpm exec playwright test -g "应该显示配置列表"

# 运行包含特定文本的所有测试
pnpm exec playwright test -g "创建"
```

### 更新快照（如果使用）

```bash
pnpm exec playwright test --update-snapshots
```

## CI/CD 集成

### GitHub Actions 示例

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 20

      - Install pnpm
        uses: pnpm/action-setup@v2
        with:
          version: 8

      - Install dependencies
        run: pnpm install

      - Install Playwright Browsers
        run: npx playwright install --with-deps chromium

      - Run E2E tests
        run: pnpm exec playwright test

      - Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30
```

### GitLab CI 示例

```yaml
e2e:test:
  image: node:20
  stage: test
  before_script:
    - npm install -g pnpm
    - pnpm install
    - npx playwright install --with-deps chromium
  script:
    - pnpm exec playwright test
  artifacts:
    when: always()
    paths:
      - playwright-report/
    expire_in: 1 week
```

## 测试报告

### HTML 报告

```bash
# 运行测试
pnpm exec playwright test

# 查看 HTML 报告
pnpm exec playwright show-report
```

HTML 报告会自动生成在 `playwright-report/` 目录。

### JSON 报告

JSON 报告用于 CI/CD 集成，位于 `playwright-report/results.json`。

### JUnit 报告

JUnit 报告用于 CI 系统解析，位于 `playwright-report/results.xml`。

## 常见问题

### 1. 下载浏览器失败

**问题**: 网络问题导致浏览器下载失败

**解决方案**:
```bash
# 使用国内镜像
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/
npx playwright install chromium
```

### 2. 缺少系统库

**问题**: 运行时提示缺少某些库

**解决方案**:
```bash
# 安装所有依赖
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2
```

### 3. 内存不足

**问题**: 测试运行时内存溢出

**解决方案**:
```bash
# 减少并行进程
pnpm exec playwright test --workers=1

# 或者限制每个 worker 的内存
NODE_OPTIONS="--max-old-space-size=4096" pnpm exec playwright test
```

### 4. 超时问题

**问题**: 测试超时

**解决方案**:
```typescript
// 在测试中增加超时
test('慢速测试', async ({ page }) => {
  test.setTimeout(60000) // 60秒
  // ...
})
```

## 编写测试的最佳实践

### 1. 使用 Page Object Model

```typescript
// pages/ModelManagementPage.ts
export class ModelManagementPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/model-management')
  }

  async createConfig(data: any) {
    await this.page.click('button:has-text("新建配置")')
    await this.page.fill('[placeholder*="配置名称"]', data.name)
    // ...
  }
}
```

### 2. 等待策略

```typescript
// ✅ 好的做法
await page.waitForSelector('el-table', { state: 'visible' })
await expect(page.locator('.el-dialog')).toBeVisible()

// ❌ 不好的做法
await page.waitForTimeout(5000)
```

### 3. 选择器优先级

```typescript
// 1. 优先使用 user-visible 文本
page.getByText('新建配置')
page.getByPlaceholder('请输入配置名称')

// 2. 使用 data-testid
page.getByTestId('submit-button')

// 3. 最后使用 CSS 选择器
page.locator('button.primary')
```

### 4. 测试隔离

```typescript
test.beforeEach(async ({ page }) => {
  // 每个测试前清理数据
  await resetTestData()
})

test.afterEach(async ({ page }) => {
  // 每个测试后截图（如果失败）
  if (test.info().status !== 'passed') {
    await page.screenshot({ path: `screenshots/${test.info().title}.png` })
  }
})
```

## 持续集成建议

### 1. 并行执行

```bash
# 默认并行（推荐）
pnpm exec playwright test

# 限制并行数
pnpm exec playwright test --workers=4
```

### 2. 分片执行（大型项目）

```bash
# 分成 4 个分片
pnpm exec playwright test --shard=1/4
pnpm exec playwright test --shard=2/4
pnpm exec playwright test --shard=3/4
pnpm exec playwright test --shard=4/4
```

### 3. 仅运行失败的测试

```bash
pnpm exec playwright test --only-failed
```

## 性能优化

### 1. 禁用不必要的资源

```typescript
// 在 playwright.config.ts
use: {
  // 禁用图片加载
  // javaScriptEnabled: false,
}
```

### 2. 使用缓存

```bash
# 使用 CI 缓存
pnpm exec playwright test --workers=same
```

## 总结

- ✅ **完全支持无界面服务器**: Headless 模式
- ✅ **零配置运行**: 默认配置已优化
- ✅ **丰富的报告**: HTML、JSON、JUnit
- ✅ **CI/CD 友好**: 自动检测环境
- ✅ **并行执行**: 快速反馈
- ✅ **失败重试**: CI 环境自动重试

## 参考资源

- [Playwright 官方文档](https://playwright.dev)
- [Playwright 最佳实践](https://playwright.dev/docs/best-practices)
- [Playwright 在 CI 中运行](https://playwright.dev/docs/ci)
