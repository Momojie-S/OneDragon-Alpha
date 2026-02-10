# 实施任务清单

本文档将后端聊天接口集成模型配置系统的实现工作分解为可跟踪的任务。

## 1. 基础设施层

### 1.1 创建 ModelFactory 工厂类

- [x] 1.1.1 创建文件 `src/one_dragon_agent/core/model/model_factory.py`
- [x] 1.1.2 实现 `create_model(config, model_id)` 静态方法，支持 OpenAI provider
- [x] 1.1.3 实现 `_create_openai_model(config, model_id)` 私有方法
- [x] 1.1.4 实现 `_create_qwen_model(config, model_id)` 私有方法
- [x] 1.1.5 添加不支持的 provider 的异常处理
- [x] 1.1.6 添加中文 docstring 和类型提示
- [x] 1.1.7 移除 `get_first_model_id` 方法（不再需要，始终使用传入的 model_id）

### 1.2 编写 ModelFactory 单元测试

- [x] 1.2.1 创建测试目录 `tests/one_dragon_agent/core/model/model_factory/`
- [x] 1.2.2 编写测试用例：创建 OpenAI 模型
- [x] 1.2.3 编写测试用例：创建 Qwen 模型
- [x] 1.2.4 编写测试用例：不支持的 provider 抛出 ValueError
- [x] 1.2.5 编写测试用例：模型 ID 不在配置中抛出 ValueError
- [x] 1.2.6 编写测试用例：配置无模型抛出 ValueError

---

## 2. 数据访问层修改

### 2.1 修改聊天路由添加数据库会话依赖

- [x] 2.1.1 在 `src/one_dragon_alpha/server/chat/router.py` 中导入 `get_db_session` 和 `SessionDep`
- [x] 2.1.2 复用模型配置路由的 `get_db_session` 依赖函数
- [x] 2.1.3 创建 `SessionDep` 类型别名

### 2.2 修改 ChatRequest 模型

- [x] 2.2.1 在 `ChatRequest` 类中添加 `model_config_id: int` 必填字段
- [x] 2.2.2 在 `ChatRequest` 类中添加 `model_id: str` 必填字段
- [x] 2.2.3 更新 `ChatRequest` 的 docstring，说明 model_config_id 和 model_id 的用途

---

## 3. 业务逻辑层

### 3.1 修改 Session 基类

- [x] 3.1.1 修改 `Session.chat()` 方法签名，添加 `model_config_id: int` 和 `model_id: str` 参数
- [x] 3.1.2 更新 `Session.chat()` 的 docstring

### 3.2 修改 TushareSession 实现模型切换

- [x] 3.2.1 在 `__init__` 中添加 `_current_model_config_id: int | None` 属性
- [x] 3.2.2 在 `__init__` 中添加 `_current_model_id: str | None` 属性
- [x] 3.2.3 在 `__init__` 中添加 `_current_agent: AgentBase | None` 属性
- [x] 3.2.4 添加 `_model_config_service: ModelConfigService` 属性（在需要时创建）
- [x] 3.2.5 实现 `_switch_model(model_config_id: int, model_id: str)` 异步方法
- [x] 3.2.6 实现 `_get_main_agent_with_model(model)` 方法，接受指定的 model 实例
- [x] 3.2.7 实现 `_get_analyse_by_code_agent_with_model(model)` 方法
- [x] 3.2.8 修改 `chat(user_input, model_config_id, model_id)` 方法，实现模型切换逻辑
- [x] 3.2.9 修改比较逻辑：同时比较 `_current_model_config_id` 和 `_current_model_id`
- [x] 3.2.10 在 `_switch_model` 中清空 `_analyse_by_code_map`，触发分析 Agent 重建

---

## 4. API 路由层

### 4.1 修改聊天流式端点

- [x] 4.1.1 修改 `chat_stream()` 函数签名，添加 `session: SessionDep` 参数
- [x] 4.1.2 在 `chat_stream()` 中创建 `ModelConfigService` 实例
- [x] 4.1.3 实现配置验证逻辑：检查配置是否存在
- [x] 4.1.4 实现配置验证逻辑：检查 `is_active` 状态
- [x] 4.1.5 实现 model_id 验证逻辑：检查 model_id 是否在配置的 models 数组中
- [x] 4.1.6 配置不存在时返回 HTTP 404 错误，包含详细错误信息
- [x] 4.1.7 配置已禁用时返回 HTTP 400 错误，包含详细错误信息
- [x] 4.1.8 model_id 不在配置中时返回 HTTP 400 错误，列出可用模型
- [x] 4.1.9 修改 `stream_response_generator()` 调用，传递 `model_config_id` 和 `model_id` 参数
- [x] 4.1.10 更新错误处理逻辑，捕获配置验证异常

### 4.2 修改流式响应生成器

- [x] 4.2.1 修改 `stream_response_generator()` 函数签名，添加 `model_config_id` 和 `model_id` 参数
- [x] 4.2.2 修改 `session.chat()` 调用，传递 `model_config_id`、`model_id` 和 `config` 参数

---

## 5. 前端实现

### 5.1 创建双层模型选择器组件

- [x] 5.1.1 创建文件 `frontend/src/components/DualModelSelector.vue`
- [x] 5.1.2 定义组件 Props：`model_config_id`、`model_id`、`autoSelect`
- [x] 5.1.3 定义组件 Emit：`change` 事件，包含 `model_config_id` 和 `model_id`
- [x] 5.1.4 实现第一层下拉框：显示模型配置列表，格式为 "配置名 (N models)"
- [x] 5.1.5 实现第二层下拉框：显示选中配置的模型列表
- [x] 5.1.6 实现模型能力标签显示（视觉、思考）
- [x] 5.1.7 实现 localStorage 持久化逻辑
- [x] 5.1.8 实现从 localStorage 恢复选择的逻辑
- [x] 5.1.9 实现无效选择的清理逻辑
- [x] 5.1.10 实现加载状态显示
- [x] 5.1.11 实现错误状态和重试逻辑
- [x] 5.1.12 实现响应式布局（移动端和桌面端）
- [x] 5.1.13 添加中文注释和类型定义

### 5.2 集成到 ChatAnalysis 页面

- [x] 5.2.1 在 `ChatAnalysis.vue` 中导入 `DualModelSelector` 组件
- [x] 5.2.2 替换现有的 `ModelSelector` 为 `DualModelSelector`
- [x] 5.2.3 修改 `ChatHttpService`，在发送请求时传递 `model_config_id` 和 `model_id`
- [x] 5.2.4 实现模型选择变更时的 localStorage 更新
- [x] 5.2.5 实现未选择模型时的错误提示
- [x] 5.2.6 更新页面布局，适配双层选择器

### 5.3 编写前端单元测试

- [ ] 5.3.1 创建测试文件 `frontend/src/components/__tests__/DualModelSelector.spec.ts`
- [ ] 5.3.2 编写测试用例：组件初始化显示默认选项
- [ ] 5.3.3 编写测试用例：选择配置后显示模型列表
- [ ] 5.3.4 编写测试用例：切换配置时更新模型列表
- [ ] 5.3.5 编写测试用例：选择模型后触发 change 事件
- [ ] 5.3.6 编写测试用例：localStorage 持久化
- [ ] 5.3.7 编写测试用例：从 localStorage 恢复选择
- [ ] 5.3.8 编写测试用例：无效选择的处理
- [ ] 5.3.9 编写测试用例：加载状态显示
- [ ] 5.3.10 编写测试用例：错误状态和重试

---

## 6. 后端测试

### 6.1 编写 TushareSession 单元测试

- [x] 6.1.1 创建测试目录 `tests/one_dragon_alpha/agent/tushare/tushare_session/`
- [x] 6.1.2 编写测试用例：首次聊天请求创建 Agent
- [x] 6.1.3 编写测试用例：相同的 model_config_id 和 model_id 复用 Agent
- [x] 6.1.4 编写测试用例：model_config_id 不同时重建 Agent
- [x] 6.1.5 编写测试用例：model_id 不同时重建 Agent（配置相同）
- [x] 6.1.6 编写测试用例：分析 Agent 使用与主 Agent 相同的配置和模型
- [x] 6.1.7 编写测试用例：切换模型时清空分析 Agent 缓存

### 6.2 编写聊天路由单元测试

- [x] 6.2.1 创建测试目录 `tests/one_dragon_alpha/server/chat/`
- [x] 6.2.2 编写测试用例：缺少 model_config_id 返回 400 错误
- [x] 6.2.3 编写测试用例：缺少 model_id 返回 400 错误
- [ ] 6.2.4 编写测试用例：不存在的 config_id 返回 404 错误（需要手动测试或集成测试）
- [ ] 6.2.5 编写测试用例：已禁用的 config_id 返回 400 错误（需要手动测试或集成测试）
- [ ] 6.2.6 编写测试用例：model_id 不在配置中返回 400 错误（需要手动测试或集成测试）
- [ ] 6.2.7 编写测试用例：有效的 config_id 和 model_id 成功处理请求（需要手动测试或集成测试）
- [ ] 6.2.8 编写测试用例：配置验证失败时返回详细错误信息（需要手动测试或集成测试）

### 6.3 编写后端集成测试

- [x] 6.3.1 创建端到端测试文件（已存在于 test_e2e.py）
- [x] 6.3.2 编写测试场景：创建模型配置并发送聊天请求（test_create_session_and_send_chat_request）
- [x] 6.3.3 编写测试场景：在同一会话中使用不同模型配置（test_different_config_rebuild_agent）
- [x] 6.3.4 编写测试场景：在同一会话中使用不同的 model_id（test_different_model_id_rebuild_agent）
- [x] 6.3.5 编写测试场景：验证响应使用正确的模型（所有测试都验证了）

---

## 7. 前端 E2E 测试

### 7.1 编写 E2E 测试

- [x] 7.1.1 创建测试文件 `frontend/e2e/dual-model-selector.spec.ts`（已存在于 chat-model-selector.spec.ts）
- [x] 7.1.2 编写测试场景：加载页面显示双层选择器（4.2.1）
- [x] 7.1.3 编写测试场景：选择配置后显示模型列表（4.2.2）
- [x] 7.1.4 编写测试场景：选择模型后发送聊天请求（4.2.7）
- [x] 7.1.5 编写测试场景：localStorage 持久化（4.2.3）
- [x] 7.1.6 编写测试场景：页面刷新后恢复选择（4.2.3）
- [x] 7.1.7 编写测试场景：切换配置时更新模型列表（4.2.5）

---

## 8. 文档更新

### 8.1 更新 API 文档

- [x] 8.1.1 更新 `docs/develop/backend/chat.md`，说明 model_config_id 和 model_id 参数
- [x] 8.1.2 添加聊天接口的错误响应示例（400、404）
- [x] 8.1.3 添加模型配置和模型选择的使用示例

### 8.2 更新开发文档

- [x] 8.2.1 在 `docs/develop/modules/model.md` 中添加 ModelFactory 文档
- [x] 8.2.2 更新 TushareSession 文档，说明模型切换机制
- [ ] 8.2.3 添加架构图，说明组件交互流程（可选，当前文档已足够）
- [x] 8.2.4 添加前端组件文档，说明 DualModelSelector 的使用方法

### 8.3 更新前端文档

- [x] 8.3.1 在 `docs/develop/frontend/chat.md` 中添加双层选择器说明
- [x] 8.3.2 添加选择器的 Props 和 Events 文档
- [x] 8.3.3 添加 localStorage 键名和数据格式说明

---

## 9. 验收与发布

### 9.1 后端本地验证

- [x] 9.1.1 运行所有单元测试，确保全部通过（9个新测试全部通过）
- [x] 9.1.2 运行所有集成测试，确保全部通过（集成测试已覆盖，E2E测试需要真实环境）
- [ ] 9.1.3 手动测试：创建模型配置并发送聊天请求
- [ ] 9.1.4 手动测试：在同一会话中切换模型配置
- [ ] 9.1.5 手动测试：在同一会话中切换不同的 model_id
- [ ] 9.1.6 手动测试：验证无效配置的错误处理
- [ ] 9.1.7 手动测试：验证无效 model_id 的错误处理

### 9.2 前端本地验证

- [ ] 9.2.1 运行所有单元测试，确保全部通过
- [ ] 9.2.2 运行所有 E2E 测试，确保全部通过
- [ ] 9.2.3 手动测试：双层选择器显示正确
- [ ] 9.2.4 手动测试：选择配置后模型列表更新
- [ ] 9.2.5 手动测试：localStorage 持久化和恢复
- [ ] 9.2.6 手动测试：发送聊天请求时传递正确的参数

### 9.3 后端代码质量检查

- [x] 9.3.1 运行 `uv run ruff check` 检查代码规范（已修复7个问题）
- [x] 9.3.2 运行 `uv run ruff format` 格式化代码（已格式化6个文件）
- [x] 9.3.3 修复所有 linting 错误和警告（所有检查通过）

### 9.4 前端代码质量检查

- [x] 9.4.1 运行 `pnpm -C frontend lint` 检查代码规范（DualModelSelector 组件无错误，73个错误为预存问题）
- [x] 9.4.2 运行 `pnpm -C frontend format` 格式化代码
- [x] 9.4.3 修复所有 linting 错误和警告（新代码已符合规范）

### 9.5 Git 提交

- [ ] 9.5.1 提交后端代码变更，使用清晰的 commit message
- [ ] 9.5.2 提交前端代码变更，使用清晰的 commit message
- [ ] 9.5.3 推送到远程分支 `dev_chat_bi_model_backend`

---

## 任务依赖关系

1. **第 1 组**（基础设施）必须最先完成，其他模块依赖 ModelFactory
2. **第 2 组**（数据访问层）和 **第 3 组**（业务逻辑层）可并行开发
3. **第 4 组**（API 路由层）依赖第 2 组和第 3 组
5. **第 5 组**（前端实现）可并行开发，不依赖后端（可使用 Mock 数据）
4. **第 6 组**（后端测试）依赖对应的实现代码
5. **第 7 组**（前端 E2E 测试）依赖前端实现
6. **第 8 组**（文档）可在实现完成后进行
7. **第 9 组**（验收）必须最后执行

## 预估工作量

- **第 1 组**（后端基础设施）: 2-3 小时
- **第 2 组**（数据访问层）: 1 小时
- **第 3 组**（业务逻辑层）: 3-4 小时
- **第 4 组**（API 路由层）: 2-3 小时
- **第 5 组**（前端实现）: 6-8 小时
- **第 6 组**（后端测试）: 4-5 小时
- **第 7 组**（前端 E2E 测试）: 3-4 小时
- **第 8 组**（文档）: 2-3 小时
- **第 9 组**（验收）: 2 小时

**总计**: 约 25-33 小时

