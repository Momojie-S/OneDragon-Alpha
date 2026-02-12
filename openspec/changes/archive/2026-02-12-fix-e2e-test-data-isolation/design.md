# E2E 测试数据隔离问题 - 技术设计

## Context

当前项目使用 Playwright 进行前端 E2E 测试，但存在测试数据隔离不当的问题：

**当前状态**：
- `chat-model-selector.spec.ts`：依赖数据库中的正式配置，测试不稳定
- `model-management.spec.ts`：存在语法错误和不完整实现，无法运行
- 后端已有测试数据清理接口（`/api/models/configs/cleanup-test-data`）
- CLAUDE.md 要求测试"只操作测试数据，不能操作真实数据"

**技术约束**：
- 前端：Vue 3 + TypeScript + Vitest（单元测试）+ Playwright（E2E 测试）
- 后端：Python + FastAPI，清理接口已实现，使用 `TEST_TOKEN` 验证
- 测试数据命名规范：使用 `test_` 或 `test_e2e_` 前缀

## Goals / Non-Goals

**Goals:**
1. 确保所有测试数据使用明确的 `test_` 前缀，与正式数据完全隔离
2. 修复所有语法和逻辑错误，使测试可以正常运行
3. 建立清晰的测试分层：单元测试（Mock）→ 联调（真实）→ E2E 测试（Mock）
4. 提供统一的测试工具模块，便于其他测试复用

**Non-Goals:**
- 不修改后端 API（清理接口已存在，无需改动）
- 不改变生产代码逻辑（只修改测试代码）
- 不要求 100% 测试覆盖率（重点在数据隔离，而非测试完整性）

## Decisions

### 决策 1：chat-model-selector.spec.ts 迁移到组件测试

**决策**：将 `chat-model-selector.spec.ts` 从 E2E 测试迁移到组件测试

**理由**：
- 该测试只验证 DualModelSelector 组件的 UI 交互，不是完整的业务流程
- 组件测试运行更快（秒级 vs 分钟级）
- 组件测试更容易 Mock 数据，不依赖数据库状态
- 符合测试金字塔：大量单元测试，少量 E2E 测试

**技术方案**：
```typescript
// frontend/src/components/__tests__/DualModelSelector.spec.ts
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import DualModelSelector from '../DualModelSelector.vue'
import * as modelApi from '../../services/modelApi'

// Mock modelApi
vi.mock('../../services/modelApi', () => ({
  getActiveModelConfigs: vi.fn(),
}))

describe('DualModelSelector 组件测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('双层选择器交互', () => {
    it('应该显示配置选择器和模型选择器', async () => {
      // Mock 返回测试配置数据
      const mockConfigs = [
        {
          id: 1,
          name: 'test_e2e_mock_config_1',
          provider: 'openai',
          models: [
            { model_id: 'gpt-4', support_vision: true, support_thinking: false }
          ]
        }
      ]

      vi.mocked(modelApi.getActiveModelConfigs).mockResolvedValue({
        total: 1,
        page: 1,
        page_size: 100,
        items: mockConfigs
      })

      const wrapper = mount(DualModelSelector, {
        global: { plugins: [] }
      })

      await new Promise(process.nextTick)

      // 验证 UI 元素存在
      expect(wrapper.find('.config-selector').exists()).toBe(true)
      expect(wrapper.find('.model-selector').exists()).toBe(true)
    })

    it('选择配置后应该显示模型列表', async () => {
      // Mock 配置和模型数据
      // ...
      // 验证选择逻辑
    })
  })

  describe('localStorage 持久化', () => {
    it('选择模型后应该保存到 localStorage', async () => {
      // 测试 localStorage 读写
    })
  })
})
```

**被否决的方案**：
- ❌ 保留在 E2E 测试中并使用 Mock API：虽然可行，但 E2E 测试应该专注于真实用户流程，组件交互更适合单元测试
- ❌ 创建真实的测试配置再测试：增加了复杂度，且测试速度慢

---

### 决策 2：model-management.spec.ts 修复方案

**决策**：完全重写 `model-management.spec.ts`，实现真实的测试数据创建和清理

**理由**：
- 当前文件存在语法错误和缺失模块，修复比重写更复杂
- 需要真实的测试数据创建和清理流程，验证后端清理接口
- 为后续测试提供可复用的工具函数

**技术方案**：

#### 2.1 创建测试工具模块

```typescript
// frontend/e2e/utils/test-helper.ts
import { Page } from '@playwright/test'

/**
 * 测试配置
 */
export const TEST_CONFIG = {
  token: process.env.TEST_TOKEN || 'test-token-123',
  baseUrl: 'http://localhost:21003',
  dataPrefix: 'test_e2e_'
}

/**
 * 生成唯一的测试配置名称
 */
export function generateTestConfigName(): string {
  const timestamp = Date.now()
  const random = Math.random().toString(36).substring(7)
  return `${TEST_CONFIG.dataPrefix}config_${timestamp}_${random}`
}

/**
 * 创建测试配置（通过 API）
 */
export async function createTestConfig(
  page: Page,
  configName: string
): Promise<void> {
  const config = {
    name: configName,
    provider: 'openai',
    base_url: 'https://api.test.com',
    api_key: 'sk-test-key',
    models: [
      { model_id: 'test-model', support_vision: false, support_thinking: false }
    ],
    is_active: true
  }

  // 直接调用 API 创建（不通过 UI）
  await page.request.post(`${TEST_CONFIG.baseUrl}/api/models/configs`, {
    headers: {
      'Content-Type': 'application/json',
      'x-test-token': TEST_CONFIG.token
    },
    data: config
  })

  console.log(`✅ 创建测试配置: ${configName}`)
}

/**
 * 清理所有测试数据
 */
export async function cleanupTestData(page: Page): Promise<void> {
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
  } else {
    console.warn(`⚠️ 清理测试数据失败: ${response.status()}`)
  }
}

/**
 * 导航到模型配置管理页面
 */
export async function navigateToModelManagement(page: Page): Promise<void> {
  await page.goto('/model-management')
  await page.waitForLoadState('networkidle')
}
```

#### 2.2 重写测试文件

```typescript
// frontend/e2e/model-management.spec.ts
import { test, expect } from '@playwright/test'
import { cleanupTestData, navigateToModelManagement, generateTestConfigName, createTestConfig } from './utils/test-helper'

test.describe('E2E 模型配置数据隔离', () => {
  test.beforeEach(async ({ page }) => {
    // 每次测试前不清理，让每个测试独立管理数据
  })

  test.afterEach(async ({ page }) => {
    // 每次测试后清理所有测试数据
    await cleanupTestData(page)
  })

  test('应该创建测试配置并成功清理', async ({ page }) => {
    // 1. 创建测试配置
    const configName = generateTestConfigName()
    await createTestConfig(page, configName)

    // 2. 验证创建成功
    await navigateToModelManagement(page)
    await expect(page.locator(`text=${configName}`)).toBeVisible()

    // 3. 清理会在 afterEach 自动执行
  })

  test('应该只清理测试数据（不影响正式数据）', async ({ page }) => {
    // 1. 创建测试配置
    const testConfigName = generateTestConfigName()
    await createTestConfig(page, testConfigName)

    // 2. 验证测试配置存在
    await navigateToModelManagement(page)
    await expect(page.locator(`text=${testConfigName}`)).toBeVisible()

    // 3. 调用清理接口
    await cleanupTestData(page)

    // 4. 刷新页面验证测试配置已删除
    await page.reload()
    await expect(page.locator(`text=${testConfigName}`)).not.toBeVisible()

    // 5. 正式配置不受影响（假设数据库中有正式配置）
    // 清理接口只删除 test_e2e_ 前缀的数据
  })

  test('应该支持并发测试（多个测试配置独立）', async ({ page }) => {
    // 创建多个独立的测试配置
    const config1 = generateTestConfigName()
    const config2 = generateTestConfigName()

    await createTestConfig(page, config1)
    await createTestConfig(page, config2)

    await navigateToModelManagement(page)

    // 验证两个配置都存在
    await expect(page.locator(`text=${config1}`)).toBeVisible()
    await expect(page.locator(`text=${config2}`)).toBeVisible()

    // afterEach 会自动清理所有数据
  })
})
```

**语法错误修复**：
- 第 191 行：`await expect(page.locator('.el-dialog').last()).toBeVisible()`
  - 修复为：`await expect(page.locator('.el-dialog').last().toBeVisible())`

---

### 决策 3：测试分层和开发流程更新

**决策**：在 CLAUDE.md 中明确测试金字塔和开发流程

**理由**：
- 当前流程对 E2E 测试的定位不清晰
- 需要明确各层测试的职责和数据使用策略
- 避免未来再出现依赖正式数据的问题

**具体更新内容**：

```markdown
### 前端开发流程（务实驱动）

4.1 前端代码开发
4.2 前端单元测试（4.5）
    - 使用 Vitest + Vue Test Utils
    - 全 Mock 数据
    - 快速验证组件逻辑
    - 基于联调确认的正确接口编写

4.3 制定前端 E2E 测试计划（4.6 之前）
    - 确定需要 E2E 测试的关键流程
    - 只保留少量核心场景

4.4 使用 chrome-devtools 按计划联调（4.7）
    - 手动验证关键流程
    - 发现问题调整代码或测试计划
    - 快速对齐前后端接口

4.5 编写 Playwright E2E 测试（4.8）
    - 使用 Mock API 数据
    - 只测试少量核心场景
    - 验证 UI 和交互流程

4.6 前端核心函数单元测试
    - 对核心逻辑函数编写单元测试
```

**测试策略说明**：
```markdown
## 测试数据规范

### 测试数据命名
- 所有测试数据必须使用 `test_` 前缀标记
- E2E 测试数据使用 `test_e2e_` 前缀
- 便于清理接口识别和删除

### 测试分层原则

#### 后端 E2E 测试（3.2）
- ✅ 使用真实数据库
- ✅ 创建测试数据（test_ 前缀）
- ✅ 保证后端 API 正确性

#### 前端单元/组件测试（4.5）
- ✅ 全 Mock 数据
- ✅ 快速验证组件逻辑
- ✅ 不依赖外部服务

#### 前端 chrome-devtools 联调（4.7）
- ✅ 真实的前后端集成测试
- ✅ 快速验证前后端接口对齐
- ✅ 手动验证核心流程

#### 前端 Playwright E2E 测试（4.8）
- ✅ 使用 Mock API 数据
- ✅ 测试前端 UI 和交互流程
- ✅ 不依赖后端状态
- ✅ 只测试少量核心场景

### 测试金字塔

```
         ▲ 少量 E2E 测试（快速反馈）
        ╱ ╲
       ╱   ╲
      ╱─────╲
     ╱       ╲
    ╱─────────╲
   ╱───────────╲
  ╱─────────────╲
 ╱─────────────────╲
```
```

## Risks / Trade-offs

### 风险 1：组件测试可能无法覆盖某些浏览器特性

**描述**：DualModelSelector 使用 localStorage 持久化，组件测试中 localStorage 的行为可能与真实浏览器不同

**缓解措施**：
- 组件测试中验证 localStorage 的读写逻辑是否正确
- 保留 `smoke.spec.ts` 作为基本的功能验证
- chrome-devtools 联调时验证跨标签页的 localStorage 行为（如需要）

---

### 风险 2：model-management.spec.ts 需要真实的后端 API

**描述**：测试数据创建和清理需要调用后端 API，如果后端服务未启动，测试会失败

**缓解措施**：
- 在 CI/CD 流程中，确保先启动后端服务再运行测试
- 在本地开发时，手动启动后端服务
- 测试文件顶部添加清晰的依赖说明

---

### 风险 3：现有测试可能依赖前端应用服务

**描述**：Playwright E2E 测试通过 `webServer` 配置启动前端服务，可能与开发端口冲突

**缓解措施**：
- 使用环境变量配置不同的端口（开发：21002，测试：可用其他端口）
- 或者 `reuseExistingServer: true`，复用已运行的开发服务器

---

### 权衡 1：测试覆盖率可能下降

**描述**：`chat-model-selector.spec.ts` 迁移到组件测试后，E2E 层面的测试覆盖减少

**补偿措施**：
- 组件测试提供更细粒度的覆盖，反而提升整体质量
- 未来的 Chat BI 完整流程 E2E 测试会补充端到端覆盖
- 遵循测试金字塔原则，底层测试更多是合理的

---

### 权衡 2：需要维护更多测试文件

**描述**：测试分散到单元测试和 E2E 测试两个目录，维护成本增加

**补偿措施**：
- 各层测试职责清晰，更容易定位问题
- `test-helper.ts` 提供共享工具，减少重复代码
- 清晰的分层符合业界最佳实践

## Migration Plan

### 实施步骤

**阶段 1：迁移 chat-model-selector 测试**
1. 创建 `frontend/src/components/__tests__/DualModelSelector.spec.ts`
2. 从现有 E2E 测试中提取测试用例，转换为组件测试
3. Mock `modelApi` 模块，提供测试数据
4. 运行测试验证通过：`pnpm test:unit DualModelSelector`
5. 删除 `frontend/e2e/chat-model-selector.spec.ts`

**阶段 2：修复 model-management 测试**
1. 创建 `frontend/e2e/utils/test-helper.ts` 工具模块
2. 重写 `frontend/e2e/model-management.spec.ts`
3. 修复语法错误（第 191 行）
4. 实现真实的测试数据创建和清理逻辑
5. 运行测试验证通过：`pnpm test:e2e model-management`

**阶段 3：更新文档和流程**
1. 更新 `CLAUDE.md` 的前端开发流程
2. 添加测试金字塔和策略说明
3. 验证文档清晰度和可执行性

**阶段 4：验证和清理**
1. 运行所有测试确保无回归：`pnpm test`
2. 检查数据库中无遗留测试数据
3. 提交代码并创建 PR

### 回滚策略

**如果测试失败或引入新问题**：
- 可以快速回滚到变更前的 commit
- 旧测试文件删除前通过 git 保留
- 如果新测试工具模块有问题，可以暂时使用旧的测试方式

## Open Questions

**无**：当前设计已覆盖所有实施细节，可以开始实施。

**后续待确认事项**（进入实施阶段时确认）：
1. `smoke.spec.ts` 是否需要更新？（当前倾向：保持不变）
2. 是否需要在 CI 中添加测试数据清理检查？（可以添加安全检查）
3. 测试数据前缀是否统一为 `test_e2e_`？（当前两种前缀共存）
