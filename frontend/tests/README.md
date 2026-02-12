# 前端测试指南

本文档提供前端测试的快速参考和常用模式。

## 目录

- [测试分层](#测试分层)
- [测试数据规范](#测试数据规范)
- [编写测试](#编写测试)
  - [单元测试](#单元测试)
  - [组件测试](#组件测试)
  - [E2E 测试](#e2e-测试)
- [常用测试模式](#常用测试模式)
- [调试测试](#调试测试)

## 测试分层

### 测试金字塔

```
         少量 E2E 测试（快速反馈）
        /           \
       /------------- \  前端 E2E（Mock API）
      /---------------- \  后端 E2E（真实数据）
     /---------------------- \
    /------------------------------ \  大量单元测试（全 Mock）
----------------------------------------> 开发成本
```

### 各层测试职责

| 测试类型 | 数据策略 | 职责 | 工具 |
|---------|---------|------|------|
| 后端 E2E 测试 | 真实数据库 | 验证后端 API 正确性 | pytest + 真实数据库 |
| 前端 chrome-devtools 联调 | 真实集成 | 快速对齐前后端接口 | chrome-devtools 手动测试 |
| 前端单元/组件测试 | 全 Mock | 快速验证组件逻辑 | Vitest + Vue Test Utils |
| 前端 Playwright E2E 测试 | Mock API | 测试 UI 和交互流程 | Playwright + Mock API |

### 开发流程顺序

1. chrome-devtools 联调（4.7） - 快速对齐接口
2. 前端单元测试（4.5） - 基于正确接口编写
3. 前端 E2E 测试（4.8） - 少量核心场景验证

**为什么先联调再写测试？**
- 快速发现前后端接口不匹配
- 立即调整，避免写错测试
- 确保"接口理解"是正确的

## 测试数据规范

### 命名前缀

所有测试数据必须使用明确的命名前缀，与正式数据隔离：

- **E2E 测试数据**：使用 `test_e2e_` 前缀
- **单元测试数据**：使用 `test_` 前缀

### 示例

```typescript
// 正确：使用 test_ 前缀
const testConfig = {
  name: 'test_config_openai',
  provider: 'openai',
  models: [{ model_id: 'gpt-4', support_vision: true, support_thinking: false }]
}

// 错误：使用正式配置名
const formalConfig = {
  name: 'DeepSeek 官方',
  provider: 'deepseek',
  models: [...]
}

// 错误：不够明确
const unclearConfig = {
  name: 'Test Config',
  provider: 'openai',
  models: [...]
}
```

### 数据清理

- 后端提供清理接口：`DELETE /api/models/configs/cleanup-test-data`
- 只删除匹配前缀的测试数据
- E2E 测试在 `afterEach` 钩子中调用清理

## 编写测试

### 单元测试

使用 Vitest + Vue Test Utils，全 Mock 数据。

```typescript
import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import MyComponent from './MyComponent.vue'
import * as api from '../services/api'

// Mock 外部依赖
vi.mock('../services/api', () => ({
  fetchData: vi.fn(),
}))

describe('MyComponent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('应该正确渲染', async () => {
    // Given: 准备 Mock 数据
    const mockData = { name: 'test_config_1' }
    vi.mocked(api.fetchData).mockResolvedValue(mockData)

    // When: 挂载组件
    const wrapper = mount(MyComponent)

    // Then: 验证结果
    expect(wrapper.text()).toContain('test_config_1')
  })
})
```

### 组件测试

测试组件交互和状态管理。

```typescript
describe('DualModelSelector', () => {
  it('选择配置后应该显示模型列表', async () => {
    const mockConfigs = [{
      id: 1,
      name: 'test_config_openai',
      models: [{ model_id: 'gpt-4', support_vision: true, support_thinking: false }]
    }]

    vi.mocked(modelApi.getActiveModelConfigs).mockResolvedValue({
      items: mockConfigs,
      total: 1
    })

    const wrapper = mount(DualModelSelector)
    await wrapper.vm.handleConfigChange(1)

    expect(wrapper.vm.currentModels).toEqual(mockConfigs[0].models)
  })
})
```

### E2E 测试

使用 Playwright，少量核心场景，使用 Mock API。

```typescript
import { test, expect } from '@playwright/test'

test.describe('核心用户流程', () => {
  test('应该能够创建模型配置', async ({ page }) => {
    // 设置 Mock API
    await page.route('**/api/models/configs*', async (route) => {
      if (route.request().method() === 'POST') {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 1,
            name: 'test_e2e_config_new',
            provider: 'openai'
          })
        })
      }
    })

    // 执行测试
    await page.goto('/model-management')
    await page.click('button:has-text("新建配置")')
    await page.fill('input[name="name"]', 'test_e2e_config_new')
    await page.click('button:has-text("确定")')

    // 验证结果
    await expect(page.locator('text=test_e2e_config_new')).toBeVisible()
  })
})
```

## 常用测试模式

### Mock API 响应

```typescript
// 成功响应
mockFetch.mockResolvedValueOnce({
  ok: true,
  json: async () => ({ success: true, data: [...] })
} as Response)

// 失败响应
mockFetch.mockResolvedValueOnce({
  ok: false,
  status: 400,
  json: async () => ({ message: '参数错误' })
} as Response)
```

### 测试异步操作

```typescript
it('应该处理异步加载', async () => {
  const wrapper = mount(AsyncComponent)

  // 等待下一个 tick
  await wrapper.vm.$nextTick()

  // 或等待 Promise
  await new Promise(resolve => setTimeout(resolve, 0))

  expect(wrapper.vm.data).toBeDefined()
})
```

### 测试用户交互

```typescript
it('应该响应点击事件', async () => {
  const wrapper = mount(ButtonComponent)

  await wrapper.find('button').trigger('click')

  expect(wrapper.vm.clicked).toBe(true)
})
```

### 测试表单

```typescript
it('应该验证表单输入', async () => {
  const wrapper = mount(FormComponent)

  await wrapper.find('input[name="email"]').setValue('test@example.com')
  await wrapper.find('form').trigger('submit')

  expect(wrapper.emitted('submit')[0]).toEqual([{ email: 'test@example.com' }])
})
```

## 调试测试

### 使用 chrome-devtools

1. 启动 Chrome 实例：
   ```bash
   chromium-browser --headless --remote-debugging-port=9222 --no-sandbox --disable-gpu > /dev/null 2>&1 &
   ```

2. 在测试中连接：
   ```typescript
   // Playwright 会自动连接到运行的 Chrome
   ```

### 常用调试技巧

- 使用 `console.log` 或 `wrapper.vm` 查看组件状态
- 使用 `page.pause()` 暂停 Playwright 测试
- 使用 `--debug` 模式运行 Vitest
- 截图保存：`await page.screenshot({ path: 'debug.png' })`

## 参考资源

- [Vitest 文档](https://vitest.dev/)
- [Vue Test Utils 文档](https://test-utils.vuejs.org/)
- [Playwright 文档](https://playwright.dev/)
- [项目 CLAUDE.md](../../CLAUDE.md) - 完整开发规范
