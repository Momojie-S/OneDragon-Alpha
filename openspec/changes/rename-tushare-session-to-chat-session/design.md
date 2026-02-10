# Design: 重命名 TushareSession 为 ChatSession

## Context

### 当前状态

`TushareSession` 类位于 `src/one_dragon_alpha/agent/tushare/tushare_session.py`，继承自基础 `Session` 类。虽然名称暗示它是 Tushare 专用会话，但从架构设计上，它是一个通用金融数据分析会话，当前集成了 Tushare 工具，未来计划支持 AkShare 等其他数据源。

当前目录结构：
```
src/one_dragon_alpha/
├── agent/
│   └── tushare/
│       └── tushare_session.py  ← 需要移动
├── session/
│   ├── session.py              ← 基础 Session 类
│   └── session_service.py      ← 使用 TushareSession
```

### 约束条件

- 必须保持所有测试通过
- 不能改变任何公共 API 行为
- 遵循项目的开发规范（Python 后端规范）
- 必须更新所有导入语句和引用

## Goals / Non-Goals

**Goals:**
- 将 `TushareSession` 重命名为 `ChatSession`，体现其通用性质
- 将文件移动到更合理的位置：`src/one_dragon_alpha/chat/chat_session.py`
- 更新所有相关导入和引用
- 保持所有功能行为不变
- 所有测试通过

**Non-Goals:**
- 不修改类的功能实现
- 不改变 Session 的公共接口
- 不涉及前端代码修改
- 不涉及数据库结构变更
- 不添加新的数据源支持（留待未来）

## Decisions

### 决策 1: 新的类名 - `ChatSession`

**选择理由**:
- 简洁明了，易于理解
- 不限定数据源类型
- 与项目中其他命名风格一致（简洁、通用）
- 为未来多数据源支持预留空间

**考虑的替代方案**:
- `DataAnalysisSession`: 过于冗长，且限定了"分析"场景
- `FinancialAnalysisSession`: 过于具体，限定了金融领域
- `UniversalSession`: 过于抽象，不直观

### 决策 2: 新的文件路径 - `src/one_dragon_alpha/chat/chat_session.py`

**选择理由**:
- 创建独立的 `chat` 模块，与 `session` 模块区分开
- `session` 模块包含基础的会话管理（Session, SessionMessage, SessionService）
- `chat` 模块包含业务层的聊天会话实现
- 结构清晰，职责分离

**考虑的替代方案**:
- `src/one_dragon_alpha/session/chat_session.py`: 放在现有 session 模块中
  - 缺点：session 模块应该保持基础性，chat_session 是业务实现
- `src/one_dragon_alpha/agent/chat/chat_session.py`: 放在 agent 模块下
  - 缺点：chat_session 不是 agent，而是使用 agent 的会话管理器

### 决策 3: 模块结构

新的 `chat` 模块结构：
```
src/one_dragon_alpha/chat/
├── __init__.py
└── chat_session.py
```

**`__init__.py` 的内容**:
```python
# -*- coding: utf-8 -*-
"""聊天会话模块."""

from one_dragon_alpha.chat.chat_session import ChatSession

__all__ = ["ChatSession"]
```

### 决策 4: 测试文件路径调整

测试文件保持原有的组织结构，但更新导入路径：
```
tests/one_dragon_alpha/chat/
├── __init__.py
├── test_e2e.py
└── test_unit.py
```

**选择理由**:
- 测试路径与源代码路径保持镜像关系
- 便于测试发现和组织

## Risks / Trade-offs

### 风险 1: 导入路径变更可能导致运行时错误

**描述**: 如果某些导入语句未被正确更新，可能导致 `ImportError` 或 `AttributeError`。

**缓解措施**:
- 使用全局搜索替换确保所有导入都被更新
- 运行所有单元测试和端到端测试验证
- 在提交前进行完整的功能测试

### 风险 2: 文档字符串中的类名引用可能遗漏

**描述**: 代码中的文档字符串、注释可能包含 `TushareSession` 的引用。

**缓解措施**:
- 使用文本搜索工具搜索所有包含 "TushareSession" 的文件
- 逐个检查并更新相关引用
- 更新相关的 Markdown 文档

### 风险 3: 环境变量和配置文件中的引用

**描述**: 虽然当前配置中没有直接引用类名，但需要确认没有硬编码的类名字符串。

**缓解措施**:
- 搜索配置文件和环境变量设置
- 检查日志输出和错误消息中的类名引用

## Migration Plan

### 步骤 1: 准备工作
1. 创建新的目录结构 `src/one_dragon_alpha/chat/`
2. 创建新的测试目录结构 `tests/one_dragon_alpha/chat/`

### 步骤 2: 移动和重命名
1. 移动 `tushare_session.py` → `chat/chat_session.py`
2. 修改类名 `TushareSession` → `ChatSession`
3. 更新文档字符串中的类名引用

### 步骤 3: 更新导入语句
更新以下文件中的导入语句：
- `src/one_dragon_alpha/session/session_service.py`
- `tests/one_dragon_alpha/chat/test_e2e.py`
- `tests/one_dragon_alpha/chat/test_unit.py`
- 任何其他引用该类的文件

### 步骤 4: 更新模块导出
1. 创建 `src/one_dragon_alpha/chat/__init__.py`
2. 创建 `tests/one_dragon_alpha/chat/__init__.py`

### 步骤 5: 清理旧文件
1. 删除 `src/one_dragon_alpha/agent/tushare/` 目录（如果为空）
2. 删除旧的测试目录 `tests/one_dragon_alpha/agent/tushare/tushare_session/`

### 步骤 6: 验证
1. 运行所有单元测试：`uv run --env-file .env pytest tests/one_dragon_alpha/chat/`
2. 运行端到端测试
3. 检查代码格式：`uv run ruff check src/one_dragon_alpha/chat/`
4. 启动服务验证功能正常

### 回滚策略

如果出现问题，可以通过 Git 回滚所有变更：
```bash
git reset --hard HEAD
git clean -fd
```

## Open Questions

*无*

所有技术决策已经明确，可以在实施阶段直接执行。
