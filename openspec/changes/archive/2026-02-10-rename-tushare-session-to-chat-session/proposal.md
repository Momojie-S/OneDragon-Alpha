# Proposal: 重命名 TushareSession 为 ChatSession

## Why

当前的 `TushareSession` 命名限制了系统的扩展性。虽然目前只集成了 Tushare 数据源，但系统架构设计上支持未来添加 AkShare 等其他数据源。使用具体数据源名称作为类名会造成概念混淆，也不符合"全能"数据会话的设计理念。现在进行重命名可以为未来的多数据源支持打下良好的基础。

## What Changes

- **类名重命名**: `TushareSession` → `ChatSession`
- **文件路径调整**: `src/one_dragon_alpha/agent/tushare/tushare_session.py` → `src/one_dragon_alpha/chat/chat_session.py`
- **导入语句更新**: 更新所有引用该类的导入语句
- **测试文件调整**: 相应的测试文件路径和类名引用
- **SessionService 更新**: 更新创建会话时的类引用
- **文档和注释更新**: 更新相关的文档字符串和注释

## Capabilities

### New Capabilities
*无*

### Modified Capabilities
*无*

> **说明**: 这是一个纯粹的重命名变更，不涉及任何功能行为的变化，因此不需要创建或修改任何规格文档。

## Impact

**受影响的代码模块**:
- `src/one_dragon_alpha/agent/tushare/tushare_session.py` - 主类定义
- `src/one_dragon_alpha/session/session_service.py` - Session 创建逻辑
- `src/one_dragon_alpha/agent/tushare/__init__.py` - 模块导出
- `tests/one_dragon_alpha/agent/tushare/tushare_session/test_e2e.py` - 端到端测试
- `tests/one_dragon_alpha/agent/tushare/tushare_session/test_unit.py` - 单元测试

**API 变更**:
- 无 API 接口变更（仅内部类名变化）

**依赖影响**:
- 无外部依赖变更

**数据库影响**:
- 无数据库结构变更

**前端影响**:
- 无前端代码变更（后端内部重构）
