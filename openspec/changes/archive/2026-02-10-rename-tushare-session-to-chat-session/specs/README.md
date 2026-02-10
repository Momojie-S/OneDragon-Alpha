# Specs: 重命名 TushareSession 为 ChatSession

## 说明

这是一个纯粹的重命名变更，不涉及任何功能行为的变化。因此：

- **无新增需求** (No ADDED requirements)
- **无修改需求** (No MODIFIED requirements)
- **无移除需求** (No REMOVED requirements)

## 变更范围

本次变更仅限于：
- 类名重命名：`TushareSession` → `ChatSession`
- 文件路径移动：`src/one_dragon_alpha/agent/tushare/tushare_session.py` → `src/one_dragon_alpha/chat/chat_session.py`
- 所有导入语句和引用的更新

## 功能行为

所有功能行为保持不变，包括但不限于：
- 聊天消息处理
- 模型动态切换
- 代码分析功能（analyse_by_code）
- Agent 管理
- 流式响应处理

## 测试要求

虽然功能行为不变，但需要确保所有测试通过：
- 单元测试验证类的内部逻辑
- 端到端测试验证完整的聊天流程
- 模型切换测试验证动态模型配置功能
