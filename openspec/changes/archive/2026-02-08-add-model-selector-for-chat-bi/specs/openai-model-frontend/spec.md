# OpenAI 模型前端管理界面规范（Delta）

此文档是对 `openspec/specs/openai-model-frontend/spec.md` 的增量修改。

## MODIFIED Requirements

### Requirement: 模型配置数据获取
系统 SHALL 通过后端 API 获取模型配置列表，并支持在不同场景下筛选配置。

#### Scenario: 获取所有配置
- **WHEN** 用户访问模型配置管理页面
- **THEN** 系统 SHALL 调用 `/api/models/configs` 接口
- **AND** 不传递任何筛选参数
- **AND** 接口 SHALL 返回所有模型配置（包括已启用和已禁用的）

#### Scenario: 获取已启用的配置（聊天场景）
- **WHEN** 用户访问 ChatAnalysis 页面
- **THEN** 系统 SHALL 调用 `/api/models/configs?is_active=true` 接口
- **AND** 接口 SHALL 仅返回已启用的模型配置
- **AND** 返回的配置 SHALL 用于填充模型选择器

#### Scenario: 获取成功
- **WHEN** API 调用成功
- **THEN** 系统 SHALL 解析返回的分页响应数据
- **AND** 从响应中提取 `items` 数组作为配置列表
- **AND** 每个配置 SHALL 包含：id、name、provider、base_url、models、is_active、created_at、updated_at

#### Scenario: 获取失败
- **WHEN** API 调用失败
- **THEN** 系统 SHALL 捕获错误并返回空数组
- **AND** 调用方 SHALL 根据返回的空数组显示相应的提示信息

## ADDED Requirements

### Requirement: 获取已启用模型配置的便捷方法
系统 SHALL 提供便捷函数用于在聊天场景下获取已启用的模型配置。

#### Scenario: 调用便捷函数
- **WHEN** 组件需要获取已启用的模型配置
- **THEN** 系统 SHALL 提供 `getActiveModelConfigs()` 便捷函数
- **AND** 该函数 SHALL 自动设置 `is_active=true` 参数
- **AND** 该函数 SHALL 返回 `PaginatedResponse<ModelConfig>` 类型的数据

#### Scenario: 便捷函数实现
- **WHEN** `getActiveModelConfigs()` 被调用
- **THEN** 系统 SHALL 内部调用 `getModelConfigs({ is_active: true })`
- **AND** 返回所有已启用的配置（不限制分页）
- **AND** 传递 `page_size` 参数为最大值（如 100）以获取所有配置

