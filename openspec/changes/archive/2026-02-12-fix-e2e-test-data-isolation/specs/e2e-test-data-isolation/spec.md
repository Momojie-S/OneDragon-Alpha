# E2E 测试数据隔离机制规范

## ADDED Requirements

### Requirement: 测试数据命名规范

系统必须确保所有测试数据使用统一的命名前缀，与正式数据明确隔离。

**理由**：
- 测试数据必须能够被自动识别和清理
- 避免误删正式环境的数据
- 确保测试可重复运行，不影响生产环境

#### Scenario: 创建测试配置

- **WHEN** 开发人员或测试脚本创建测试数据
- **THEN** 数据必须使用以下前缀之一：
  - E2E 测试数据：`test_e2e_` 前缀
  - 单元测试数据：`test_` 前缀
  - 不得使用正式数据的命名模式

#### Scenario: 测试数据识别

- **WHEN** 清理接口或工具扫描测试数据
- **THEN** 必须能够通过前缀唯一识别测试数据
- **MUST** 不依赖数据内容判断（因为正式数据可能包含相同关键词）

#### Scenario: 数据隔离验证

- **WHEN** 执行测试后检查数据库
- **THEN** 必须确认：
  - 所有测试数据已删除
  - 正式数据未受影响
  - 无遗留测试数据

---

### Requirement: E2E 测试 Mock 策略

前端 E2E 测试必须使用 Mock API 数据，不依赖真实后端状态。

**理由**：
- 确保测试快速且稳定
- 不受后端服务状态影响
- 后端 E2E 测试已覆盖真实数据场景

#### Scenario: API 请求 Mock

- **WHEN** E2E 测试发起 API 请求
- **THEN** 必须使用 Mock 数据响应
- **MUST NOT** 调用真实后端 API（除验证清理接口外）

#### Scenario: 测试数据准备

- **WHEN** E2E 测试需要测试数据
- **THEN** 必须通过 Mock 数据提供
- **MUST NOT** 从数据库读取或查询正式配置

#### Scenario: 测试独立性

- **WHEN** 多个 E2E 测试并发或顺序执行
- **THEN** 每个测试必须独立运行
- **MUST NOT** 依赖其他测试遗留的数据

---

### Requirement: 测试数据清理机制

系统必须提供安全的测试数据清理机制，仅在测试环境可用。

**理由**：
- 确保测试后数据不残留
- 防止生产环境误删数据
- 通过环境变量或令牌验证测试环境

#### Scenario: 清理接口调用

- **WHEN** E2E 测试完成后执行清理
- **THEN** 必须调用清理接口 `DELETE /api/models/configs/cleanup-test-data`
- **MUST** 在请求头中包含有效的测试令牌 `x-test-token`

#### Scenario: 令牌验证

- **WHEN** 清理接口收到请求
- **THEN** 必须验证 `x-test-token` 与环境变量 `TEST_TOKEN` 匹配
- **MUST** 拒绝无效令牌，返回 401 Unauthorized
- **MUST** 在令牌未配置时返回 403 Forbidden（"测试功能在生产环境中被禁用"）

#### Scenario: 数据删除范围

- **WHEN** 清理接口执行删除操作
- **THEN** 必须只删除匹配前缀的测试数据
- **MUST** 使用 LIKE 查询：`WHERE name LIKE 'test_e2e_%'`
- **MUST NOT** 删除任何不匹配前缀的正式数据

#### Scenario: 清理结果反馈

- **WHEN** 清理接口完成删除
- **THEN** 必须返回删除结果：
  - `success: true`
  - `deleted_count`: 删除的记录数
  - `message`: 描述信息

#### Scenario: E2E 测试 afterEach 清理

- **WHEN** Playwright 测试的 afterEach 钩子执行
- **THEN** 必须调用清理接口
- **SHOULD** 在测试开始前也清理（确保干净的初始状态）

---

### Requirement: 测试可重复性

测试系统必须支持多次重复执行，每次执行结果一致。

**理由**：
- 测试必须是确定性的，不依赖执行顺序
- 便于 CI/CD 自动化
- 快速发现和修复回归问题

#### Scenario: 独立测试执行

- **WHEN** 单个测试用例执行
- **THEN** 必须能够独立运行
- **MUST NOT** 依赖其他测试的状态或数据

#### Scenario: 并发测试执行

- **WHEN** 多个测试并发运行（Playwright workers）
- **THEN** 每个测试必须使用独立的测试数据
- **MUST** 通过唯一标识（如时间戳+随机数）避免冲突

#### Scenario: 测试前后清理

- **WHEN** 测试用例开始执行前
- **THEN** **SHOULD** 清理可能遗留的测试数据
- **THEN** 测试完成后必须清理本次创建的所有数据

---

### Requirement: Chrome DevTools 联调数据安全

使用 chrome-devtools 进行手动联调时，必须避免污染正式数据。

**理由**：
- 联调是真实的集成测试，会操作真实数据库
- 必须使用测试数据，不影响正式环境
- 与自动化测试保持一致的数据隔离原则

#### Scenario: 联调前数据准备

- **WHEN** 开始 chrome-devtools 联调前
- **THEN** 必须创建或确认测试数据存在
- **SHOULD** 使用 `test_e2e_` 前缀的配置
- **MUST NOT** 修改或删除正式配置

#### Scenario: 联调后数据清理

- **WHEN** chrome-devtools 联调完成
- **THEN** **SHOULD** 清理测试数据
- **MAY** 保留测试数据供后续使用（需明确标记）

#### Scenario: 联调与自动测试一致性

- **WHEN** 使用 chrome-devtools 手动测试
- **THEN** 测试数据和流程应与 E2E 测试保持一致
- **MUST** 遵循相同的数据命名规范
