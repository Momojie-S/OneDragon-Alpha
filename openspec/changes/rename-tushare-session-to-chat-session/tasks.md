# Tasks: 重命名 TushareSession 为 ChatSession

## 1. 准备工作

- [ ] 1.1 创建新目录 `src/one_dragon_alpha/chat/`
- [ ] 1.2 创建测试目录 `tests/one_dragon_alpha/chat/`

## 2. 核心代码迁移

- [ ] 2.1 移动 `src/one_dragon_alpha/agent/tushare/tushare_session.py` 到 `src/one_dragon_alpha/chat/chat_session.py`
- [ ] 2.2 修改类名：`TushareSession` → `ChatSession`
- [ ] 2.3 更新文档字符串中的类名引用（docstrings 和注释）
- [ ] 2.4 创建 `src/one_dragon_alpha/chat/__init__.py` 并导出 `ChatSession`

## 3. 导入语句更新

- [ ] 3.1 更新 `src/one_dragon_alpha/session/session_service.py` 中的导入语句
- [ ] 3.2 搜索并更新所有其他 Python 文件中对 `TushareSession` 的导入
- [ ] 3.3 验证无遗漏的导入引用

## 4. 测试代码迁移

- [ ] 4.1 移动 `tests/one_dragon_alpha/agent/tushare/tushare_session/test_e2e.py` 到 `tests/one_dragon_alpha/chat/test_e2e.py`
- [ ] 4.2 移动 `tests/one_dragon_alpha/agent/tushare/tushare_session/test_unit.py` 到 `tests/one_dragon_alpha/chat/test_unit.py`
- [ ] 4.3 更新测试文件中的类名引用（`TushareSession` → `ChatSession`）
- [ ] 4.4 更新测试文件中的导入语句
- [ ] 4.5 创建 `tests/one_dragon_alpha/chat/__init__.py`

## 5. 文档和注释更新

- [ ] 5.1 搜索所有包含 "TushareSession" 的文档和注释
- [ ] 5.2 更新文档字符串中的类名引用
- [ ] 5.3 更新 Markdown 文档中的类名引用（如果有）

## 6. 代码质量检查

- [ ] 6.1 运行代码格式检查：`uv run ruff format src/one_dragon_alpha/chat/`
- [ ] 6.2 运行代码质量检查：`uv run ruff check src/one_dragon_alpha/chat/`
- [ ] 6.3 修复所有格式和质量问题

## 7. 测试验证

- [ ] 7.1 运行单元测试：`uv run --env-file .env pytest tests/one_dragon_alpha/chat/test_unit.py`
- [ ] 7.2 运行端到端测试：`uv run --env-file .env pytest tests/one_dragon_alpha/chat/test_e2e.py`
- [ ] 7.3 确保所有测试通过
- [ ] 7.4 如有测试失败，修复问题并重新测试

## 8. 清理工作

- [ ] 8.1 删除空的 `src/one_dragon_alpha/agent/tushare/` 目录
- [ ] 8.2 删除空的 `tests/one_dragon_alpha/agent/tushare/tushare_session/` 目录
- [ ] 8.3 验证无残留的旧文件引用

## 9. 功能验证

- [ ] 9.1 启动后端服务，验证无导入错误
- [ ] 9.2 测试聊天会话创建功能
- [ ] 9.3 测试模型动态切换功能
- [ ] 9.4 测试代码分析功能（analyse_by_code）

## 10. 提交准备

- [ ] 10.1 检查所有变更的文件：`git status`
- [ ] 10.2 确认无意外修改的文件
- [ ] 10.3 创建 Git commit（不包含 `.venv`、`__pycache__` 等临时文件）
