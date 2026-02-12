# 测试统一化和规范化

## ADDED Requirements

### Requirement: 测试数据命名统一规范

所有测试（单元、组件、E2E）中的 Mock 数据必须使用统一的命名规范。

**理由**：
- 便于识别测试数据
- 提高代码可读性
- 避免混淆测试数据和真实数据

#### Scenario: Mock 数据命名

- **WHEN** 编写测试并创建 Mock 数据
- **THEN** Mock 数据必须使用以下规范：
  - 配置名称：`test_config_` + 描述（如 `test_config_openai`）
  - 用户名：`test_user_` + 描述（如 `test_user_alice`）
  - 其他实体：`test_` + 类型 + 描述（如 `test_model_deepseek`）
- **MUST NOT** 使用：
  - "Test Config"（不够明确）
  - "DeepSeek 官方"（真实的正式配置名）
  - "ModelScope-Free"（真实的正式配置名）

#### Scenario: 时间戳和随机数

- **WHEN** 测试需要唯一标识
- **THEN** **SHOULD** 使用格式：`test_{类型}_{timestamp}_{random}`
- **EXAMPLE**: `test_config_123456789_abc4f`
- **PURPOSE**: 确保并发测试不会冲突

#### Scenario: 测试数据描述

- **WHEN** Mock 数据需要描述信息
- **THEN** 描述应当：
  - 简洁明了（如 `test_openai_config`）
  - 使用英文（避免编码问题）
  - 长度适中（建议 < 30 字符）

---

### Requirement: 共享测试工具

系统必须提供统一的测试工具模块，供所有测试复用。

**理由**：
- 避免代码重复
- 统一数据生成逻辑
- 便于维护和更新

#### Scenario: 测试数据工厂

- **WHEN** 测试需要创建 Mock 数据
- **THEN** **SHOULD** 使用共享的 `test-data-factory.ts` 工具
- **MUST PROVIDE** 以下函数：
  - `createTestModelConfig()`: 生成测试模型配置
  - `createTestUser()`: 生成测试用户数据
  - `generateUniqueId()`: 生成唯一标识

#### Scenario: E2E 测试辅助函数

- **WHEN** E2E 测试需要测试数据管理
- **THEN** **MUST** 使用 `test-helper.ts` 工具
- **MUST PROVIDE** 以下函数：
  - `generateTestConfigName()`: 生成测试配置名
  - `createTestConfig()`: 通过 API 创建配置
  - `cleanupTestData()`: 调用清理接口
  - `navigateToModelManagement()`: 导航到页面

#### Scenario: 工具模块位置

- **WHEN** 导入测试工具
- **THEN** E2E 测试使用：`frontend/e2e/utils/test-helper.ts`
- **THEN** 单元测试使用：`frontend/src/__tests__/utils/test-data-factory.ts`

---

### Requirement: 单元测试 Mock 完整性

所有单元测试必须完全 Mock 外部依赖，无真实 API 调用。

**理由**：
- 确保测试快速且隔离
- 不依赖外部服务状态
- 测试失败时易于定位问题

#### Scenario: API 服务 Mock

- **WHEN** 单元测试导入 API 服务模块
- **THEN** 必须 Mock 整个模块
- **MUST USE** `vi.mock()` 替代模块导出
- **MUST NOT** 部分函数真实，部分函数 Mock

#### Scenario: 第三方库 Mock

- **WHEN** 测试依赖 Element Plus 或其他库
- **THEN** 必须 Mock 相关模块
- **EXAMPLE**: `vi.mock('element-plus', ...)`

#### Scenario: Fetch 和全局对象 Mock

- **WHEN** 测试涉及网络请求
- **THEN** 必须 Mock `global.fetch` 或 `window.fetch`
- **MUST NOT** 调用真实的 fetch API

#### Scenario: LocalStorage Mock

- **WHEN** 测试涉及浏览器存储
- **THEN** **MAY** 使用真实 localStorage（快速且安全）
- **SHOULD** 在 beforeEach 中清理：`localStorage.clear()`

---

### Requirement: 测试数据前缀验证

系统必须能够验证和强制测试数据前缀规范。

**理由**：
- 通过代码审查确保规范执行
- 在 CI/CD 中自动检查
- 防止不规范的数据进入代码库

#### Scenario: E2E 测试审查

- **WHEN** 审查 E2E 测试代码
- **THEN** 必须检查所有数据是否有 `test_` 前缀
- **MUST NOT** 发现使用真实配置名、用户名等

#### Scenario: 单元测试审查

- **WHEN** 审查单元测试代码
- **THEN** 必须检查所有 Mock 数据命名
- **SHOULD** 使用工具函数生成数据，而非硬编码

#### Scenario: CI 自动检查

- **WHEN** 代码提交到仓库
- **THEN** CI **SHOULD** 运行检查脚本
- **MUST VERIFY**：
  - 所有新增测试使用 `test_` 前缀
  - 没有硬编码的真实数据名称

---

### Requirement: 测试文档和注释

所有测试必须包含清晰的文档说明 Mock 数据和测试意图。

**理由**：
- 便于理解测试目的
- 明确测试范围
- 帮助后续维护

#### Scenario: 测试文件注释

- **WHEN** 创建测试文件
- **THEN** **SHOULD** 在文件顶部添加注释：
  - 测试目的
  - Mock 策略说明
  - 数据来源（Mock 工厂或真实 API）

#### Scenario: 测试用例注释

- **WHEN** 编写测试用例（it/test）
- **THEN** **MUST** 使用描述性名称：
  - Good: `应该正确处理测试配置创建`
  - Bad: `测试创建`
- **SHOULD** 说明测试的业务场景

#### Scenario: Mock 数据注释

- **WHEN** 测试使用复杂的 Mock 数据
- **THEN** **SHOULD** 添加注释说明数据结构
- **EXAMPLE**: `// Mock: 包含 2 个模型的测试配置`
