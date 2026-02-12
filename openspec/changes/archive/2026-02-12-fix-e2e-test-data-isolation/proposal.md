# 修复 E2E 测试数据隔离问题

## Why

经过全面审查，当前测试存在多个违反数据隔离规范的问题：

### E2E 测试问题（3个文件）

1. **依赖正式数据**：`chat-model-selector.spec.ts` 从数据库读取正式配置
   - 测试结果依赖于正式数据状态，导致不稳定
   - 违反测试规范："仅操作测试数据，不能操作真实数据"

2. **语法和逻辑错误**：`model-management.spec.ts` 存在严重问题
   - 第 191 行缺少闭合括号
   - 引用不存在的模块 `./utils/test-helper.ts`
   - 测试逻辑不完整（createTestConfig 函数未真正创建数据）

3. **未审查的问题**：`smoke.spec.ts` 未确认是否符合数据隔离规范
   - 可能隐含依赖正式数据的问题
   - 需要审查确认

### 单元/组件测试问题（5个文件）

4. **测试数据命名不规范**：部分测试使用的数据无 `test_` 前缀
   - `modelApi.spec.ts`：使用 "Test Config" 等命名
   - `ModelConfigList.spec.ts`：使用 "DeepSeek 官方" 等正式配置名
   - `ModelSelector.spec.ts`：使用真实的配置名称
   - 虽然是单元测试（全 Mock），但命名不规范

5. **缺少统一测试工具**：
   - 没有共享的测试辅助函数
   - 测试数据生成逻辑分散
   - 清理逻辑不统一
   - 代码示例（第 97 行）：
     ```typescript
     return text && !text.includes('Integration Test') && text.includes('models')
     ```
     直接从数据库读取正式配置，过滤掉测试数据，只保留正式配置进行测试
   - 风险：如果数据库中没有符合条件（不包含 "Integration Test" 且包含 "models"）的正式配置，测试会跳过
   - **数据污染风险**：测试会修改 `localStorage`，可能影响后续使用

2. **语法和逻辑错误**：`model-management.spec.ts` 存在语法错误、引用不存在的模块、测试逻辑不完整

3. **测试分层不清晰**：前端 E2E 测试与后端测试耦合，无法独立运行，违反了测试金字塔原则

4. **违反测试规范**：按照 CLAUDE.md 规范，"仅操作测试数据: 编写测试流程时，必须只操作测试数据，不能操作真实数据"

这些问题会导致：
- 测试运行不稳定，经常因为正式数据变化而失败
- 测试运行缓慢，依赖真实数据库和网络
- 无法快速验证前端逻辑的正确性
- **可能污染正式环境或影响正式数据**

### 修复保证

本次变更将：

✅ **完全避免操作真实数据**
- `chat-model-selector.spec.ts`：迁移到组件测试，使用全 Mock 数据
- `model-management.spec.ts`：创建的测试数据使用 `test_e2e_` 前缀
- 所有测试数据在测试完成后通过清理接口删除

✅ **提供明确的数据隔离机制**
- 测试数据命名规范：使用 `test_` 或 `test_e2e_` 前缀
- 后端清理接口：只删除带前缀的测试数据，不影响正式数据
- 前端 E2E 测试：使用 Mock API，不访问真实数据库

✅ **确保测试可重复运行**
- 不依赖数据库中的正式数据状态
- 每次测试运行都使用独立的测试数据
- 测试后自动清理，不影响环境

## What Changes

### 测试策略调整

**明确测试分层策略**，符合测试金字塔原则和务实开发流程：

#### 测试金字塔

```
         ▲ 少量 E2E 测试（快速反馈）
        ╱ ╲
       ╱   ╲  前端 E2E（4.6）后端 E2E（3.2）
      ╱─────╲  少量核心场景
     ╱       ╲  真实数据/真实集成
    ╱─────────╲
   ╱───────────╲ 组件/单元测试（4.5）
  ╱─────────────╲ 适量，快速反馈
 ╱─────────────────╲
╱───────────────────╲ 大量单元测试
                      全 Mock
                      快速验证
```

#### 开发流程依据

```
为什么按这个顺序：
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. chrome-devtools 联调（4.4）                           │
│     - 快速发现前后端接口不匹配                              │
│     - 立即调整，避免写错测试                                │
│     - 确保"接口理解"是正确的                                  │
│                                                             │
│  2. 单元测试（4.5）                                        │
│     - 基于正确的接口编写                                     │
│     - 快速验证组件逻辑                                        │
│     - 无需返工                                               │
│                                                             │
│  3. E2E 测试（4.6）                                        │
│     - 只测试少量关键场景                                      │
│     - 验证 UI 和交互流程                                     │
│     - 使用 Mock，运行快速                                       │
│                                                             │
│  后端 E2E 测试（3.2）已覆盖真实数据场景                   │
│  - 前端无需重复测试                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### 具体分层原则

```
┌─────────────────────────────────────────────────────────────┐
│  测试分层（按 CLAUDE.md 开发流程）                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  后端 E2E 测试（3.2）                                    │
│  ✅ 使用真实数据库                                          │
│  ✅ 创建测试数据（test_ 前缀）                              │
│  ✅ 保证后端 API 正确性                                     │
│                                                             │
│  前端 chrome-devtools 联调（4.4）                         │
│  ✅ 真实的前后端集成测试                                    │
│  ✅ 快速验证前后端接口对齐                                 │
│  ✅ 手动验证核心流程                                        │
│                                                             │
│  前端单元测试（4.5）                                     │
│  ✅ 全 Mock                                                │
│  ✅ 快速验证组件逻辑                                        │
│  ✅ 基于联调确认的正确接口编写                           │
│                                                             │
│  前端 Playwright E2E 测试（4.6）                         │
│  ✅ 使用 Mock API 数据                                      │
│  ✅ 测试前端 UI 和交互逻辑                                  │
│  ✅ 不依赖后端状态                                          │
│  ✅ 只测试少量核心场景                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 具体改动

#### 1. E2E 测试修复

**1.1 删除 `chat-model-selector.spec.ts`，迁移到组件测试**
- 删除：`frontend/e2e/chat-model-selector.spec.ts`
- 创建：`frontend/src/components/__tests__/DualModelSelector.spec.ts`
- 使用 Vitest + Vue Test Utils，全 Mock 数据
- 测试 DualModelSelector 组件的交互逻辑
- **关键改进**：不再依赖数据库中的正式配置，完全使用 Mock 数据

**1.2 全面修复 `model-management.spec.ts`**
- 修复语法错误（第 191 行缺少闭合括号）
- 创建测试工具模块 `frontend/e2e/utils/test-helper.ts`
- 实现真实的测试数据创建逻辑（通过 API 创建 test_e2e_ 前缀的配置）
- 实现登录和令牌获取逻辑
- 测试后端的清理接口是否正常工作
- **关键改进**：所有创建的测试数据都有 `test_e2e_` 前缀，确保与正式数据隔离

**1.3 审查和更新 `smoke.spec.ts`**
- 审查测试是否依赖正式数据
- 如需要，添加 Mock 或测试数据隔离逻辑
- **当前评估**：该测试只验证页面可访问性，预计无需修改

#### 2. 单元/组件测试规范化（5个文件）

**2.1 统一测试数据命名规范**
- 所有测试 Mock 数据使用 `test_` 前缀
- 修复文件：
  - `frontend/src/services/__tests__/modelApi.spec.ts`
  - `frontend/src/views/model-management/__tests__/ModelConfigList.spec.ts`
  - `frontend/src/components/__tests__/ModelSelector.spec.ts`

**2.2 创建共享测试工具**
- 创建 `frontend/src/__tests__/utils/test-data-factory.ts`
- 提供统一的测试数据生成函数
- 确保所有测试使用一致的命名格式

**2.3 审查所有测试的 Mock 策略**
- 确保所有单元测试全 Mock
- 确保没有隐式的真实 API 调用

#### 3. 文档和流程更新
   - 调整 CLAUDE.md 中前端开发阶段的编号和顺序
   - 新顺序：chrome-devtools 联调（4.4）→ 单元测试（4.5）→ E2E 测试（4.6）
   - 添加理由说明：先联调对齐接口，再基于正确接口编写单元测试，最后用少量 E2E 测试验证关键流程

4. **更新 `smoke.spec.ts`**
   - 保持现状（只测试页面可访问性，无需修改）

5. **更新 CLAUDE.md 测试策略说明**
   - 在 4.6 节明确说明前端 E2E 测试使用 Mock API
   - 明确后端 E2E 测试和前端 E2E 测试的职责分工
   - 添加测试金字塔图示说明

## Capabilities

### New Capabilities

- **e2e-test-data-isolation**: E2E 测试数据隔离和清理机制
  - 确保所有测试数据使用 `test_` 前缀标记
  - 提供测试数据清理接口，仅在测试环境可用
  - 前端 E2E 测试使用 Mock API，不依赖真实数据库

- **test-unification**: 测试统一化和规范化
  - 统一所有测试的数据命名规范（test_ 前缀）
  - 创建共享的测试工具和数据工厂
  - 确保单元测试、组件测试、E2E 测试遵循一致的原则
  - 审查和修复所有现有测试的数据隔离问题

- **component-testing-best-practices**: 组件测试最佳实践
  - 组件级测试使用 Vitest + Vue Test Utils
  - E2E 测试只用于关键用户流程验证
  - 遵循测试金字塔，大量单元测试，少量 E2E 测试

### Modified Capabilities

无（现有功能需求未变更，只是测试实现方式的调整）

## Impact

### 受影响的代码

#### E2E 测试（3个文件）
- `frontend/e2e/chat-model-selector.spec.ts` - **删除**（迁移到组件测试）
- `frontend/e2e/model-management.spec.ts` - **全面修复**
- `frontend/e2e/smoke.spec.ts` - **审查**（可能无需修改）
- `frontend/e2e/utils/test-helper.ts` - **新建**（共享测试工具）

#### 单元/组件测试（5个文件）
- `frontend/src/components/__tests__/DualModelSelector.spec.ts` - **新建**（从 E2E 迁移）
- `frontend/src/services/__tests__/modelApi.spec.ts` - **规范化**（测试数据命名）
- `frontend/src/views/model-management/__tests__/ModelConfigList.spec.ts` - **规范化**（测试数据命名）
- `frontend/src/components/__tests__/ModelSelector.spec.ts` - **规范化**（测试数据命名）
- `frontend/src/__tests__/utils/test-data-factory.ts` - **新建**（共享测试数据工厂）
- `frontend/src/__tests__/App.spec.ts` - **审查**（确认符合规范）

#### 文档更新
- `CLAUDE.md` - **更新**（测试策略和规范说明）

### 依赖变化

- 前端测试不再依赖后端数据库状态
- 前端测试运行速度提升
- 前后端测试可以并行开发和运行

### 向后兼容性

- **无破坏性变更**：这只是测试层面的改进，不影响生产代码
- 后端 API 清理接口已存在，无需修改
