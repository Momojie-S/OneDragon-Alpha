# Playwright E2E 测试快速开始

## 一分钟快速开始

### 1. 在无界面 Ubuntu 服务器上运行

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装系统依赖（首次运行）
sudo apt-get update
sudo apt-get install -y libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2

# 3. 安装 Playwright 浏览器（有网络时）
npx playwright install chromium --with-deps

# 4. 启动后端服务（在一个终端）
cd ..
uv run --env-file .env uvicorn src.one_dragon_agent.server.app:app --reload

# 5. 运行 E2E 测试（在另一个终端）
cd frontend
pnpm test:e2e
```

### 2. 使用系统已有的 Chrome/Chromium

```bash
# 设置环境变量指向系统浏览器
export PLAYWRIGHT_BROWSERS_PATH=/usr/bin

# 或者修改配置使用系统通道
# 在 playwright.config.ts 中添加：
# use: { channel: 'chromium' }

# 运行测试
pnpm test:e2e
```

## 可用的测试命令

```bash
# 运行所有 E2E 测试
pnpm test:e2e

# 运行特定测试文件
pnpm test:e2e e2e/model-management.spec.ts

# 运行匹配名称的测试
pnpm test:e2e -g "应该显示配置列表"

# 调试模式（需要在有显示器的环境）
pnpm test:e2e:debug

# UI 模式（交互式测试）
pnpm test:e2e:ui

# 生成 HTML 报告
pnpm test:e2e --reporter=html
npx playwright show-report
```

## 测试场景清单

当前 E2E 测试覆盖以下场景：

### ✅ 页面和导航
- [x] 显示模型配置页面
- [x] 显示配置列表
- [x] 正确的路由导航

### ✅ CRUD 操作
- [x] 创建新配置
- [x] 编辑配置
- [x] 删除配置（带确认）
- [x] 切换启用/禁用状态

### ✅ 过滤和分页
- [x] 按启用状态过滤
- [x] 按提供商过滤
- [x] 分页浏览

### ✅ 表单验证
- [x] 必填字段验证
- [x] URL 格式验证
- [x] 模型列表非空验证

### ✅ 高级功能
- [x] 添加和删除模型
- [x] 编辑模型能力标识
- [x] 列表刷新

### ✅ 错误处理
- [x] 网络错误处理
- [x] 空状态显示

## 配置说明

### 无界面模式（默认）

```typescript
// playwright.config.ts 已配置
use: {
  headless: true,  // 无界面模式
  viewport: { width: 1280, height: 720 }
}
```

### 超时设置

```typescript
use: {
  actionTimeout: 10 * 1000,      // 操作超时 10 秒
  navigationTimeout: 30 * 1000   // 导航超时 30 秒
}
```

### 失败处理

```typescript
use: {
  trace: 'on-first-retry',        // 首次重试时记录追踪
  screenshot: 'only-on-failure',  // 失败时截图
  video: 'retain-on-failure'      // 失败时录像
}
```

## 常见使用场景

### CI/CD 中运行

```yaml
# .github/workflows/e2e.yml
- name: Run E2E tests
  run: |
    cd frontend
    pnpm install
    npx playwright install --with-deps chromium
    pnpm test:e2e
```

### 定时运行

```bash
# 添加到 crontab
# 每天凌晨 2 点运行测试
0 2 * * * cd /path/to/frontend && pnpm test:e2e
```

### 仅运行冒烟测试

```bash
# 创建冒烟测试文件
# e2e/smoke.spec.ts

test.describe('冒烟测试', () => {
  test('基本功能可用', async ({ page }) => {
    await page.goto('/model-management')
    await expect(page.locator('h2')).toBeVisible()
  })
})

# 运行
pnpm test:e2e e2e/smoke.spec.ts
```

## 调试技巧

### 1. 查看测试运行

```bash
# 详细输出
DEBUG=pw:api pnpm test:e2e

# 使用报告器
pnpm test:e2e --reporter=list
```

### 2. 暂停执行

```javascript
// 在测试中添加
await page.pause()
```

### 3. 截图调试

```javascript
// 任意位置截图
await page.screenshot({ path: 'debug.png' })
```

### 4. 保留浏览器状态

```bash
# 测试后不关闭浏览器
HEADLESS=true pnpm test:e2e --headed
```

## 性能优化

### 加速测试运行

```bash
# 增加并行数
pnpm test:e2e --workers=4

# 禁用视频录制
# 在配置中设置 video: 'off'

# 仅运行快速测试
pnpm test:e2e -g "@fast"
```

### 减少资源消耗

```typescript
// 禁用图片加载
await page.route('**/*.{png,jpg,jpeg}', route => route.abort())

// 禁用 CSS
await page.route('**/*.css', route => route.abort())
```

## 与现有测试集成

### 同时运行单元测试和 E2E 测试

```bash
# 运行所有测试
pnpm test:unit && pnpm test:e2e

# 或使用 npm-run-all
pnpm install -D npm-run-all2
# package.json: "test": "run-p test:unit test:e2e"
```

## 测试覆盖率

### E2E 测试覆盖范围

- ✅ 用户界面交互
- ✅ 完整的用户流程
- ✅ 跨浏览器兼容性
- ✅ 真实网络请求
- ✅ 错误场景处理

### 单元测试 + E2E 测试 = 完整覆盖

- **单元测试**: API 服务、业务逻辑
- **E2E 测试**: 用户界面、端到端流程

## 下一步

1. ✅ 安装 Playwright
2. ✅ 配置无界面模式
3. ✅ 编写测试用例
4. ⏳ 集成到 CI/CD
5. ⏳ 添加更多测试场景

## 参考资源

- [完整指南](PLAYWRIGHT_GUIDE.md)
- [Playwright 官方文档](https://playwright.dev)
- [测试最佳实践](https://playwright.dev/docs/best-practices)
