# 项目开发指南

你需要按照以下描述进行本项目的开发。

## 项目概述

- 前端使用 pnpm包管理 + vue3 + element-plus + element-plus-x
- 后端使用 uv包管理 + python + fastapi + uvicorn + AgentScope + AKShare

### 目录结构

```text
OneDragon-Alpha/
├── src/ # Python后端代码主入口
├── frontend/ # Vue前端代码
├── docs/ # 项目文档
```

## 参考命令

### 开发环境设置
```bash
uv sync --group dev # 安装依赖
uv pip install -e . # 安装 one_dragon_agent 包
uv run python ...  # 运行 python 相关命令
uv run --env-file .env python ...  # 使用环境变量文件进行运行
```

### 测试
```bash
uv run --env-file .env pytest tests/ # 运行所有测试
uv run --env-file .env pytest tests/one_dragon_agent/core/agent/ # 运行特定模块
```

### 代码质量
```bash
uv run ruff check src/ tests/     # 代码检查和格式化
uv run ruff format src/ tests/    # 代码格式化
```


## 开发规范
- **字符编码**: 所有输出必须使用 UTF-8 编码。
- **保持测试同步**: 修改任何模块后，您必须更新 `tests/` 中的测试文件。确保修改后的代码已被覆盖且所有测试都通过。
- **保持文档同步**: 修改任何模块后，您必须更新 `docs/develop/modules/` 中对应的文档文件。确保文档准确反映更改。
- **Git 工作流**: 你的职责是根据用户请求编写和修改代码。不要执行任何 `git` 操作，如 `commit` 或 `push`。用户将处理所有版本控制操作。
- **使用 context7**: 当你写代码时遇到使用库的问题时，请使用 `context7` 搜索库的文档。
  - 对于tushare库，需要查询的是 Tushare Pro 文档。

## Markdown 指南
- **Mermaid 图表**: 使用标准的流程图/状态图语法，避免循环结构和 "loop" 作为变量名
  - **节点文本引号**: 节点文本必须用双引号 (`"`) 包裹，以避免解析错误。例如，使用 `I["用户界面 (CLI)"]` 而不是 `I[用户界面 (CLI)]`。
- **语言编码**: 使用中文和utf-8编码进行文档编写。
- **文档代码**: 文档中禁止写具体的代码，只需要定义类和核心方法，有详细注释即可。

## 后端Python代码规范
- **异步优先**: 所有操作均使用 async/await
- **docstring/注释**: 所有函数必须具有 Google 风格的文档注释，代码中也需要对必要逻辑加入注释说明。所有的注释都必须使用英文编写。
- **类型提示**: 所有类成员变量和函数签名必须包含类型提示(Type Hinting)。
- **内置泛型**: 使用内置泛型类型（`list`, `dict`）而不是从 `typing` 模块导入（`List`, `Dict`）。
  - **正确**: `my_list: list[str] = []`
  - **错误**: 
    ```python
    from typing import List
    my_list: List[str] = []
    ```
- **导入**：
  - **使用绝对路径导入**: 禁止使用相对路径导入。
  - **类型注解导入**: 仅用于类型注解的导入应使用`TYPE_CHECKING`。
- **显式父类构造函数调用**: 在所有子类的 `__init__` 方法中，您**必须**直接调用父类构造函数（例如，`ParentClass.__init__(self, ...)`）。禁止使用 `super().__init__()`。
- **显式数据结构**: 你应该定义一个对象，而不是使用 dict。你必须适应类定义字段，不能使用 `getattr` 和 `setattr`。
- **不暴露任何模块**: 没有收到指示的情况下，不要在 `__init__.py` 中新增暴露任何模块。
- **编码规范**
  - **编码声明**: 所有 Python 文件必须在文件开头添加 UTF-8 编码声明：
  - **禁止Unicode字符**: 禁止在代码中使用 Unicode 字符（如表情符号、特殊符号等）。
- **日志模块**: 统一使用 `one_dragon_agent.core.system.log` 中的 `get_logger()` 获取日志对象。

## 前端代码规范
- 

## 测试代码规范

当你编写测试代码时，必须遵守以下规范：

- **无测试包**: 不得在测试目录中创建 python package。
- **测试类和Fixtures**: 测试文件必须使用测试类（以 `Test` 为前缀）来组织相关的测试方法。您必须使用 `pytest.fixture` 来管理测试依赖和状态（例如对象实例的创建和拆卸），以提高代码的可重用性和可维护性。
- **导入约定**: 由于项目使用 `src-layout`，测试文件中的导入路径不得包含 `src` 目录。
  - **正确**: `from one_dragon_agent.core.agent import Agent`
  - **错误**: `from src.one_dragon_agent.core.agent import Agent`
- **单方法测试文件**: 每个 Python 测试文件应专门针对单个方法在各种场景下进行测试。
  - **示例**: 要测试 `src/one_dragon_agent/core/agent/agent.py`，请创建一个文件夹 `tests/one_dragon_agent/core/agent/agent/` 来存储所有测试文件。
  - **示例**: 要测试 `agent.py` 的 `execute_main_loop` 方法，请在 `agent` 文件夹中创建一个名为 `test_execute_main_loop.py` 的文件。该文件应包含专门针对 `execute_main_loop` 方法的所有测试用例。
- **异步测试装饰器**: 所有异步测试方法必须同时包含 `@pytest.mark.asyncio` 和 `@pytest.mark.timeout` 装饰器。
- **临时文件**: 使用当前工作目录下的 `.temp` 目录来存储临时文件。
- **保证逻辑正确**: 除非源代码逻辑有错误，否则不能因为测试不通过而修改源代码。
- **诚实原则**: 当测试用例失败且您不知道原因或如何修复时，应停下来询问下一步该怎么做。
