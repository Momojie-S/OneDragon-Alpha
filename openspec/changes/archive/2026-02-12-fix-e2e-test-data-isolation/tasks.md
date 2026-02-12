# 实施任务清单

## 1. E2E 测试修复

### chat-model-selector 迁移到组件测试
- [x] 1.1 创建 `frontend/src/components/__tests__/DualModelSelector.spec.ts`
  - 参考现有 E2E 测试的测试用例
  - 使用 Vitest + Vue Test Utils 重写
  - 所有 Mock 数据使用 `test_` 前缀
- [x] 1.2 实现基础组件测试用例
  - 双层选择器显示测试
  - 选择配置后模型列表更新测试
  - 选择模型后状态持久化测试
  - localStorage 读写测试
- [x] 1.3 实现交互逻辑测试
  - 切换配置时模型列表重置测试
  - 响应式布局测试（移动端）
  - 模型能力标签显示测试
- [x] 1.4 运行组件测试验证通过
  - `pnpm test:unit DualModelSelector`
  - 确保所有测试通过
- [x] 1.5 删除 `frontend/e2e/chat-model-selector.spec.ts`
  - 确认组件测试覆盖原 E2E 测试场景
  - 删除旧文件
- [x] 1.6 提交组件测试代码
  - git add 和 commit
  - commit message: "refactor: 迁移 chat-model-selector 测试到组件测试"

### model-management.spec.ts 全面修复
- [x] 2.1 创建 `frontend/e2e/utils/test-helper.ts`
  - 实现 `generateTestConfigName()` 函数
  - 实现 `createTestConfig()` 函数（通过 API 创建）
  - 实现 `cleanupTestData()` 函数（调用清理接口）
  - 实现 `navigateToModelManagement()` 函数
  - 添加完善的 TypeScript 类型定义和 JSDoc 注释
- [x] 2.2 重写 `frontend/e2e/model-management.spec.ts`
  - 修复第 191 行语法错误（缺少闭合括号）
  - 移除不存在的模块导入 `./utils/test-helper`
  - 导入新的 test-helper.ts 工具函数
  - 实现真实的测试数据创建和清理逻辑
  - 测试用例：
    - 创建测试配置并验证
    - 清理接口验证（只删除 test_e2e_ 数据）
    - 并发测试独立性验证
    - 清理前后验证数据已删除
- [x] 2.3 运行 E2E 测试验证通过
  - `pnpm test:e2e model-management`
  - 确保测试数据正确创建和清理
  - 确保不影响正式数据
- [ ] 2.4 提交 E2E 测试修复代码
  - git add 和 commit
  - commit message: "fix: 全面修复 model-management E2E 测试（数据隔离、语法错误）"

### smoke.spec.ts 审查
- [x] 3.1 审查 `frontend/e2e/smoke.spec.ts`
  - 确认测试只访问页面，无数据操作
  - 验证不依赖正式数据
  - 检查是否有需要添加 Mock 的地方
- [x] 3.2 确认 smoke.spec.ts 符合规范
  - 如无需修改，在文档中说明
  - 如需要修改，更新测试（保持简单）

## 2. 单元/组件测试规范化

### 创建共享测试工具
- [x] 4.1 创建 `frontend/src/__tests__/utils/test-data-factory.ts`
  - 实现 `createTestModelConfig()` 工厂函数
  - 实现 `createTestUser()` 函数（如需要）
  - 实现 `generateUniqueId()` 函数（时间戳+随机数）
  - 所有生成数据使用 `test_` 前缀
  - 添加完整的 JSDoc 注释和使用示例
- [x] 4.2 运行工具模块测试验证
  - 创建 `frontend/src/__tests__/utils/test-data-factory.spec.ts`
  - 测试所有工厂函数
  - 验证命名规范正确性

### 规范化测试数据命名
- [x] 5.1 审查和修复 `frontend/src/services/__tests__/modelApi.spec.ts`
  - 将 "Test Config" 改为 `test_config_openai`
  - 将正式配置名改为测试命名
  - 确保所有 Mock 数据使用 `test_` 前缀
  - 运行测试验证：`pnpm test:unit modelApi`
- [x] 5.2 审查和修复 `frontend/src/views/model-management/__tests__/ModelConfigList.spec.ts`
  - 将 "DeepSeek 官方" 改为 `test_config_deepseek`
  - 将 "OpenAI GPT-4" 改为测试命名
  - 使用 test-data-factory 工厂函数生成数据
  - 运行测试验证：`pnpm test:unit ModelConfigList`
- [x] 5.3 审查和修复 `frontend/src/components/__tests__/ModelSelector.spec.ts`
  - 确保所有测试配置使用 `test_` 前缀
  - 替换真实的配置名称
  - 验证 Mock 策略完整
  - 运行测试验证：`pnpm test:unit ModelSelector`
- [x] 5.4 审查 `frontend/src/__tests__/App.spec.ts`
  - 确认测试数据符合规范
  - 验证 Mock 策略
  - 如符合规范，无需修改

### 验证 Mock 策略
- [x] 5.5 检查所有单元测试的 Mock 配置
  - 搜索所有 `.spec.ts` 和 `.test.ts` 文件
  - 确保所有外部依赖已 Mock
  - 确保 `global.fetch` 和第三方库已 Mock
  - 记录审查结果到文档

## 3. 文档更新

### 更新 CLAUDE.md
- [x] 6.1 更新前端开发流程顺序
  - 调整章节编号：4.4 → 4.5 → 4.6 → 4.7 → 4.8
  - 添加务实验证说明（为什么先联调再写测试）
  - 更新 4.5 节为"前端单元测试"
  - 更新 4.6 节为"制定 E2E 测试计划"
  - 更新 4.7 节为"chrome-devtools 联调"
  - 更新 4.8 节为"编写 Playwright E2E 测试"
- [x] 6.2 添加测试策略说明章节
  - 添加"测试数据规范"小节
  - 添加"测试金字塔"图示说明
  - 明确数据命名规范（`test_` 和 `test_e2e_` 前缀）
  - 添加测试分层原则表：
    - 后端 E2E：真实数据
    - 前端单元测试：全 Mock
    - 前端 chrome-devtools 联调：真实集成
    - 前端 Playwright E2E：Mock 数据
- [x] 6.3 更新测试数据前缀说明
  - 在测试规范中明确 E2E 测试使用 `test_e2e_` 前缀
  - 单元测试使用 `test_` 前缀
  - 提供清晰的示例
  - 删除文档中所有不必要的加粗符号（`**` 和 `*` 格式）
- [x] 6.4 运行所有测试验证文档正确性
  - `pnpm test` 确保测试可正常运行
  - 检查是否有遗漏或错误的引用
  - 验证新添加的测试策略清晰易懂

### 创建测试规范文档（可选）
- [x] 6.5 创建 `frontend/tests/README.md`（如需要）
  - 汇总测试策略和规范
  - 提供测试编写快速参考
  - 包含常用测试模式和示例
  - 链接到 CLAUDE.md 相关章节

## 4. 验证和清理

### 代码质量检查
- [x] 7.1 运行所有测试确保无回归
  - `pnpm test` 运行完整测试套件
  - 确保所有测试通过
  - 检查测试覆盖率
- [x] 7.2 代码格式化和 Lint 检查
  - `pnpm lint` 检查代码规范
  - `pnpm format` 格式化代码
  - 修复所有 Lint 错误
- [x] 7.3 TypeScript 类型检查
  - 确保无类型错误
  - 所有测试工具函数有完整类型定义

### 数据清理验证
- [x] 7.4 检查数据库无遗留测试数据
  - 查询 model_configs 表中是否有 `test_e2e_` 前缀的数据
  - 验证所有测试清理接口正常工作
  - 确保正式数据未受影响
- [x] 7.5 清理所有遗留测试数据
  - 手动调用清理接口（如有需要）
  - 验证清理结果
  - 记录清理的数据数量

## 5. 提交和归档

### Git 提交
- [x] 8.1 提交所有变更到 Git
  - git add 所有修改的文件
  - 分批提交，按功能分组：
    - E2E 测试修复（task 1-3）
    - 单元测试规范化（task 4-5）
    - 文档更新（task 6）
  - 使用清晰的 commit messages
- [ ] 8.2 创建 Pull Request
  - 推送到远程仓库
  - 创建详细的 PR 描述：
    - 关联此 OpenSpec 变更
    - 列出所有主要改动
    - 附上测试报告截图
- [ ] 8.3 代码 Review
  - 自查或请求团队 Review 代码
  - 确保符合项目规范
  - 修复 Review 发现的问题

### OpenSpec 归档
- [x] 9.1 验证所有任务完成
  - 检查 tasks.md 中所有任务已勾选
  - 确认所有测试通过
  - 确认文档已更新
- [ ] 9.2 运行 `/opsx:verify` 验证实现
  - 验证实现与设计文档一致
  - 验证所有 spec 需求已满足
  - 检查是否有遗漏的改动
- [ ] 9.3 运行 `/opsx:archive` 归档变更
  - 将变更移至归档目录
  - 同步 delta specs 到主 specs 目录
  - 清理 change 目录
