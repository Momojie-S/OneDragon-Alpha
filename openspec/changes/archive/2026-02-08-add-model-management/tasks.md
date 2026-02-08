# 模型配置管理系统实现任务清单

## 1. 后端数据模型定义

- [x] 1.1 创建 `src/one_dragon_agent/core/model/` 模块目录结构
- [x] 1.2 创建 `models.py` - 定义 Pydantic 数据模型
  - `ModelConfigCreate` - 创建配置请求模型
  - `ModelConfigUpdate` - 更新请求模型
  - `ModelConfigResponse` - 配置响应模型（不包含 api_key）
  - `ModelConfigListResponse` - 配置列表响应模型（包含分页信息）
  - `TestConnectionRequest` - 测试连接请求模型
  - `TestConnectionResponse` - 测试连接响应模型
- [x] 1.3 定义字段验证规则（provider 仅允许 "openai"，models 数组非空等）
- [x] 1.4 编写数据模型的单元测试（10个测试用例全部通过）

## 2. 数据库层开发

- [x] 2.1 创建数据库表迁移脚本
  - 表名：`model_configs`
  - 字段：id, name, provider, base_url, api_key, models, is_active, created_at, updated_at
  - 添加索引：idx_name, idx_provider, idx_is_active
- [x] 2.2 创建 `repository.py` - 实现 Repository 类
  - `create_config()` - 创建配置
  - `get_config_by_id()` - 根据 ID 查询配置
  - `get_configs()` - 分页查询配置列表（支持过滤）
  - `update_config()` - 更新配置
  - `delete_config()` - 删除配置
  - `toggle_config_status()` - 切换启用状态
- [x] 2.3 实现分页查询逻辑
  - 解析 page 和 page_size 参数
  - 计算 offset 和 limit
  - 返回 total、page、page_size、items
- [x] 2.4 编写数据库操作的单元测试（已创建 test_repository.py）

## 3. 服务层开发

- [x] 3.1 创建 `service.py` - 实现 Service 类
  - `validate_config_unique()` - 验证配置名称唯一性
  - `validate_base_url()` - 验证 base_url 格式
  - `create_model_config()` - 创建配置业务逻辑
  - `get_model_config()` - 获取单个配置
  - `list_model_configs()` - 获取配置列表（分页和过滤）
  - `update_model_config()` - 更新配置
  - `delete_model_config()` - 删除配置
  - `toggle_config_status()` - 切换启用状态
- [x] 3.2 实现 provider 字段验证（仅允许 "openai"）
- [x] 3.3 实现乐观锁机制（使用 updated_at 字段）
- [x] 3.4 编写服务层的单元测试（已创建 test_service.py）

## 4. 测试连接功能开发

- [x] 4.1 在 Service 类中实现 `test_connection()` 方法
  - 调用目标 API 的 `GET /models` 端点
  - 设置 10 秒超时
  - 捕获并返回服务商的原始错误信息
- [x] 4.2 处理网络异常、超时、认证失败等场景
- [x] 4.3 编写测试连接功能的单元测试（包含在 test_service.py 中）

## 5. API 路由开发

- [x] 5.1 创建 `router.py` - 实现 FastAPI 路由
  - `POST /api/models/configs` - 创建配置
  - `GET /api/models/configs` - 获取配置列表（分页和过滤）
  - `GET /api/models/configs/{id}` - 获取单个配置
  - `PUT /api/models/configs/{id}` - 更新配置
  - `DELETE /api/models/configs/{id}` - 删除配置
  - `PATCH /api/models/configs/{id}/status` - 切换启用状态
  - `POST /api/models/configs/test-connection` - 测试连接
- [x] 5.2 实现分页参数处理（page、page_size，最大值 100）
- [x] 5.3 实现过滤参数处理（active、provider）
- [x] 5.4 添加错误处理中间件
  - 统一错误响应格式：`{ "code": "ERROR_CODE", "message": "错误描述", "details": {} }`
  - 处理 404、400、422、500 等错误
- [x] 5.5 确保 GET 接口不返回 api_key 字段
- [x] 5.6 编写 API 集成测试（已创建 test_api.py）

## 6. 后端集成和测试

- [x] 6.1 将路由注册到主应用
- [x] 6.2 端到端测试完整的数据流（创建 → 查询 → 更新 → 删除）
- [x] 6.3 测试分页功能
- [x] 6.4 测试过滤功能（active、provider）
- [x] 6.5 测试并发操作和乐观锁
- [x] 6.6 测试错误场景（名称重复、ID 不存在、无效参数等）

## 7. 前端 API 封装

- [x] 7.1 创建 `frontend/src/services/modelApi.ts` (使用 TypeScript)
  - `createModelConfig(data)` - 创建配置
  - `getModelConfigs(params)` - 获取配置列表（支持分页和过滤）
  - `getModelConfig(id)` - 获取单个配置
  - `updateModelConfig(id, data)` - 更新配置
  - `deleteModelConfig(id)` - 删除配置
  - `toggleConfigStatus(id, isActive)` - 切换启用状态
  - `testConnection(data)` - 测试连接
- [x] 7.2 封装分页参数处理
- [x] 7.3 添加统一的错误处理

## 8. 前端页面开发

- [x] 8.1 创建 `frontend/src/views/model-management/ModelConfigList.vue`
  - 配置列表表格（显示：配置名称、Provider、Base URL、模型数量、启用状态）
  - 分页组件（Element-Plus Pagination）
  - 过滤器（启用状态、Provider）
  - 操作按钮（新建、刷新）
  - 每行的操作按钮（编辑、删除、启用/禁用）
  - 空状态提示
  - 加载状态
- [x] 8.2 实现"新建配置"功能
  - 打开创建对话框
  - 表单验证
  - 调用 API 创建
  - 刷新列表
- [x] 8.3 实现"编辑配置"功能
  - 打开编辑对话框
  - 预填充现有数据（API key 字段为空）
  - 表单验证
  - 调用 API 更新
  - 刷新列表
- [x] 8.4 实现"删除配置"功能
  - 显示删除确认对话框
  - 调用 API 删除
  - 刷新列表
- [x] 8.5 实现"启用/禁用"开关
  - 调用 API 切换状态
  - 更新显示

## 9. 前端组件开发

- [x] 9.1 创建 `frontend/src/views/model-management/components/ModelConfigDialog.vue`
  - 创建/编辑配置对话框
  - 表单字段：配置名称、Provider（下拉框，仅 openai）、Base URL、API Key
  - 模型列表管理区域
    - 添加模型按钮
    - 模型列表展示（卡片形式）
    - 每个模型显示：模型 ID、支持视觉（复选框）、支持思考（复选框）
    - 编辑/删除模型按钮
  - 表单验证（必填字段、URL 格式、至少一个模型）
  - 测试连接按钮
  - 保存/取消按钮
- [x] 9.2 模型卡片组件（内嵌在 ModelConfigDialog 中）
  - 模型卡片组件
  - 显示模型 ID 和能力标签（视觉、思考）
  - 编辑和删除按钮

## 10. 前端交互优化

- [x] 10.1 实现测试连接功能
  - 点击"测试连接"按钮
  - 发送请求到后端 API
  - 显示加载状态
  - 显示成功/失败提示（直接显示服务商返回的错误信息）
- [x] 10.2 实现模型列表管理
  - 添加模型：弹出对话框
  - 编辑模型：修改能力标识
  - 删除模型：从列表中移除
  - 验证至少有一个模型
- [x] 10.3 实现加载状态和骨架屏
- [x] 10.4 实现错误提示和重试机制
- [x] 10.5 实现乐观锁错误提示（"配置已被其他用户修改，请刷新"）

## 11. 前端路由和菜单

- [x] 11.1 添加前端路由：`/model-management`
- [x] 11.2 在导航菜单中添加"模型配置"菜单项
- [x] 11.3 测试路由跳转和菜单高亮

## 12. 样式和响应式设计

- [x] 12.1 调整表格样式（大屏幕）
- [x] 12.2 调整卡片样式（小屏幕）
- [x] 12.3 添加动画和过渡效果
- [x] 12.4 优化对话框布局
- [x] 12.5 测试不同屏幕尺寸的显示效果

## 13. 前端集成测试

- [x] 13.1 API 服务单元测试（11个测试用例全部通过）
- [x] 13.2 测试分页功能
- [x] 13.3 测试过滤功能
- [x] 13.4 测试表单验证
- [x] 13.5 测试错误场景（网络错误、服务器错误等）
- [x] 13.6 测试并发编辑冲突（乐观锁）
- [x] 13.7 Playwright E2E 测试（支持无界面服务器运行）

## 14. 数据库迁移和部署

- [x] 14.1 在测试环境执行数据库迁移脚本
- [x] 14.2 验证表结构正确性
- [x] 14.3 配置数据库内网访问权限
- [x] 14.4 更新部署文档，说明数据库安全要求

## 15. 系统集成和上线

- [x] 15.1 部署后端代码到测试环境
- [x] 15.2 部署前端代码到测试环境
- [x] 15.3 在测试环境验证所有功能
- [x] 15.4 进行性能测试（大量配置的加载、并发请求）
- [x] 15.5 部署到生产环境
- [x] 15.6 在生产环境验证功能正常

## 16. 文档更新

- [x] 16.1 更新 `docs/develop/modules/` 中的模块文档
- [x] 16.2 编写数据库表设计文档
- [x] 16.3 编写 API 使用文档
- [x] 16.5 编写用户使用手册

## 17. 清理和收尾

- [x] 17.1 代码审查和重构
- [x] 17.2 运行所有测试确保通过
- [x] 17.3 更新 CHANGELOG
- [x] 17.4 清理临时文件和测试代码
- [ ] 17.5 提交代码并创建 Pull Request
