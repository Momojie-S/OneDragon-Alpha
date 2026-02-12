# 组件测试最佳实践

## ADDED Requirements

### Requirement: 组件测试工具链

组件测试必须使用 Vitest + Vue Test Utils，不使用 Playwright。

**理由**：
- 组件测试关注单个组件的行为
- 快速反馈，秒级执行
- 易于 Mock 和隔离

#### Scenario: 测试框架选择

- **WHEN** 编写 Vue 组件测试
- **THEN** 必须使用 Vitest 作为测试运行器
- **MUST USE** `@vue/test-utils` 的 `mount()` 函数
- **MUST NOT USE** Playwright 的 E2E 测试工具（如 `page.locator()`）

#### Scenario: 组件挂载

- **WHEN** 测试需要渲染组件
- **THEN** 必须使用 `mount()` 或 `shallowMount()`
- **MUST PROVIDE** 必要的 props 和全局插件
- **MAY** 提供 `slots` 测试子组件渲染

#### Scenario: 组件交互测试

- **WHEN** 测试组件交互（点击、输入等）
- **THEN** **SHOULD** 使用 Vue Test Utils 的交互方法：
  - `trigger()`: 触发事件
  - `setValue()`: 设置值
  - `vm.{prop/method}()`: 访问组件实例

---

### Requirement: 组件测试 E2E 测试职责划分

明确组件测试和 E2E 测试的职责边界，避免重复测试。

**理由**：
- 遵循测试金字塔原则
- 提高测试效率
- 各层测试专注不同目标

#### Scenario: 组件测试职责

- **WHEN** 编写组件测试
- **THEN** 必须专注以下方面：
  - 组件渲染逻辑
  - Props 响应
  - Events 发出
  - 用户交互反馈
  - 数据计算和转换
- **MUST NOT** 测试跨组件集成（由集成测试负责）
- **MUST NOT** 测试后端 API 集成（由 E2E 测试负责）

#### Scenario: E2E 测试职责

- **WHEN** 编写 E2E 测试
- **THEN** 必须专注以下方面：
  - 完整用户流程
  - 多组件协作
  - 页面导航和路由
  - 真实 API 集成（除非明确使用 Mock）
- **MAY USE** 组件测试已验证的交互逻辑

#### Scenario: 重复场景避免

- **WHEN** 组件测试已覆盖某功能
- **THEN** E2E 测试 **SHOULD NOT** 重复测试相同功能
- **FOCUS ON** 端到端业务流程和集成场景

---

### Requirement: Mock 策略

组件测试必须使用一致的 Mock 策略。

**理由**：
- 确保测试隔离
- 避免隐藏的真实 API 调用
- 提高测试稳定性

#### Scenario: API 服务 Mock

- **WHEN** 组件依赖 API 服务
- **THEN** 必须 Mock 整个服务模块
- **USE**: `vi.mock('@/services/api', ...)`
- **MUST NOT** 只 Mock 部分函数

#### Scenario: 第三方库 Mock

- **WHEN** 组件使用第三方库（Element Plus、Vue Router 等）
- **THEN** 必须 Mock 相关模块
- **EXAMPLE**: `vi.mock('element-plus', ...)`

#### Scenario: Mock 数据验证

- **WHEN** 测试需要特定的 Mock 数据状态
- **THEN** **MUST** 在测试中设置 Mock 返回值
- **MUST VERIFY** Mock 数据被正确使用
- **SHOULD NOT** 依赖默认的 Mock 行为

---

### Requirement: 测试覆盖和可维护性

组件测试必须保持良好的覆盖和可维护性。

**理由**：
- 确保核心逻辑被测试
- 便于重构和维护
- 防止回归

#### Scenario: 关键路径覆盖

- **WHEN** 组件有多个功能
- **THEN** **MUST** 测试所有关键用户路径：
  - 主功能流程
  - 边界情况
  - 错误处理
  - 默认行为
- **SHOULD** 达到至少 80% 代码覆盖率

#### Scenario: 测试可读性

- **WHEN** 编写测试用例
- **THEN** **MUST** 使用清晰的描述：
  - `it('should {verb} {expected outcome}', ...)`
  - Bad: `it('测试按钮')`
  - Good: `it('should emit click event when button is clicked')`

#### Scenario: 测试组织

- **WHEN** 组件有多个测试场景
- **THEN** **SHOULD** 使用 `describe` 分组：
  - 按功能分组（如"数据获取"、"用户交互"）
  - 按状态分组（如"loading 状态"、"错误状态"）
- **MUST** 每个 `describe` 包含相关的测试

#### Scenario: beforeEach 和 afterEach

- **WHEN** 测试需要设置或清理
- **THEN** **MUST** 使用：
  - `beforeEach()`: 每个测试前准备（如 Mock 重置）
  - `afterEach()`: 每个测试后清理（如 wrapper.unmount()）
- **MUST** 确保测试隔离，不相互影响

---

### Requirement: 性能和快照测试

组件测试应当关注性能和防止意外变更。

**理由**：
- 及时发现性能问题
- 防止 UI 意外修改
- 保持组件契约稳定

#### Scenario: 快照测试

- **WHEN** 组件渲染复杂 UI
- **THEN** **MAY USE** 快照测试验证输出：
  - 使用 `toMatchSnapshot()` 或 `toMatchInlineSnapshot()`
  - **CAUTION**: 快照应审查变更，避免盲目更新
  - **PURPOSE**: 检测意外的 UI 变更

#### Scenario: 性能测试

- **WHEN** 组件涉及大量数据或复杂计算
- **THEN** **MAY** 添加性能测试：
  - 使用 `performance.mark()` 测量渲染时间
  - 验证大数据集下的响应性
  - **THRESHOLD**: 建议渲染时间 < 16ms（60 FPS）

---

### Requirement: 类型安全

组件测试必须利用 TypeScript 的类型检查。

**理由**：
- 编译时发现类型错误
- 提高代码质量
- 减少运行时错误

#### Scenario: 类型定义使用

- **WHEN** 编写测试
- **THEN** **SHOULD** 使用导入的类型：
  - `import type { ModelConfig } from '@/types/model'`
  - `import type { VueWrapper } from '@vue/test-utils'`
- **MUST NOT** 使用 `any` 类型绕过检查

#### Scenario: Mock 数据类型

- **WHEN** 创建 Mock 数据
- **THEN** **MUST** 符合真实类型定义
- **USE**: `as Mocked<typeof modelApi>` 或直接类型断言
- **BENEFIT**: 测试在编译时验证类型正确性
