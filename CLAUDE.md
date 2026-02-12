# 项目开发指南

你需要按照以下描述进行本项目的开发。

## 项目概述

- 前端使用 pnpm包管理 + vue3 + element-plus + element-plus-x。
  - element-plus-x - 是基于 element-plus 的AI应用组件库。
- 后端使用 uv包管理 + python + fastapi + uvicorn + AgentScope + AKShare。
  - AgentScope - Agent框架。

### 目录结构

```text
OneDragon-Alpha/
├── src/ # Python后端代码主入口
├── frontend/ # Vue前端代码
├── docs/ # 项目文档
├── .env  # 存放了各种环境变量 包括数据库密码等
```

### 环境说明

- 当前项目没有区分开发和生产数据库，所有环境共用同一个数据库实例。因此测试数据清理尤为重要，必须确保测试后正确清理，避免影响开发和使用体验。
- 无论是使用工具还是测试代码，需要创建临时文件时，都在项目根目录下的 .temp 文件夹下创建。

### 环境变量设置

- 项目所需的环境变量都能在 `.env` 文件中找到。
- 使用 `uv run` 命令时，必须使用 `--env-file .env` 参数来加载环境变量。
- 不要手动设置 `PYTHONPATH`，使用 `.env` 来加载。

## 参考命令

```bash
uv sync --group dev # 安装依赖
uv run --env-file .env python ...  # 运行 python 相关命令（必须使用 --env-file .env）

pnpm -C frontend ... # 运行pnpm命令时 必须使用 -C 来指定运行目录
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

## 开发流程规范

### 需求开发流程

1. 当启动一个新的需求修改时，需要使用 opsx 草拟方案，并在后续过程按 opsx 规范进行。opsx相关命令必须在项目根目录下运行。
2. 在设计阶段，你应该:
  - 按最少的能满足需求的功能点来设计，不要过度设计。
  - 使用 context7 了解相关库的能力，特别是 AgentScope 和 element-plus-x 这两个比较新的库。了解后再进行设计。
  - 设计阶段，需要考虑测试过程产生脏数据和清理方案。
3. 在开发阶段，你需要先进行后端开发：
  3.1. 后端代码开发。
  3.2. 后端代码的端到端测试，仅做少量的核心场景。
  3.3. 后端代码的单元测试，使用全mock的方式。
  3.4. 进行详细的代码Review。
4. 完成后端开发后，再进行前端开发：
  4.1. 前端代码开发。
  4.2. 前端单元测试。
     - 使用 Vitest + Vue Test Utils。
     - 全 Mock 数据。
     - 快速验证组件逻辑。
     - 基于联调确认的正确接口编写。
  4.3. 制定前端 E2E 测试计划。
     - 确定需要 E2E 测试的关键流程。
     - 只保留少量核心场景。
  4.4. 使用 chrome-devtools 按计划联调。
     - 手动验证关键流程。
     - 快速对齐前后端接口。
     - 发现问题调整代码或测试计划。
  4.5. 编写 Playwright E2E 测试（新）。
     - 使用 Mock API 数据。
     - 只测试少量核心场景。
     - 验证 UI 和交互流程。
  4.6. 对于前端核心函数，进行单元测试。
  4.7. 进行详细的代码Review。
5. 开发测试完成后，使用 `opsx:verify` 进行验证。
6. 验证通过后，使用 `opsx:archive` 进行归档。归档时，禁止使用 `--no-validate`。

### 测试策略

#### 测试数据规范

所有测试数据必须使用明确的命名前缀，与正式数据隔离：

- E2E 测试数据：使用 `test_e2e_` 前缀
- 单元测试数据：使用 `test_` 前缀
- 便于清理接口识别和自动删除

#### 测试分层原则

*关键原则*：
- E2E 测试：只测试少量核心场景，使用 Mock API
- 单元测试：大量测试，全 Mock，快速验证逻辑
- 联调：先对齐接口，再基于正确接口编写测试
5. 如果开发、测试过程中，调整了实现方案，需要更新对应 opsx 的设计文档。
6. 进行 opsx 归档。
  - 禁止使用移动文件夹或者复制文件夹的方式进行归档。
  - 禁止使用 `--skip-specs` 。
7. 提交到 Github 并创建 PR。


### 后端开发规范

- 异步优先*: 所有操作均使用 async/await
- docstring/注释*: 所有函数必须具有 Google 风格的文档注释，代码中也需要对必要逻辑加入注释说明。所有的注释都必须使用中文编写。
- 类型提示*: 所有类成员变量和函数签名必须包含类型提示(Type Hinting)。
- 内置泛型*: 使用内置泛型类型（`list`, `dict`）而不是从 `typing` 模块导入（`List`, `Dict`）。
- 导入*：
  - 使用绝对路径导入*: 禁止使用相对路径导入。
  - 类型注解导入*: 仅用于类型注解的导入应使用`TYPE_CHECKING`。
- 显式父类构造函数调用*: 在所有子类的 `__init__` 方法中，调用父类构造函数时*必须显式传入所有必需参数*。
  - 允许使用 `super().__init__(...)`，但必须确保所有参数都显式传递
  - 示例：`super().__init__(arg1=value1, arg2=value2)` 而非依赖默认参数隐式传递
- 显式数据结构*: 你应该定义一个对象，而不是使用 dict。你必须适应类定义字段，不能使用 `getattr` 和 `setattr`。
- 不暴露任何模块*: 没有收到指示的情况下，不要在 `__init__.py` 中新增暴露任何模块。
- 编码规范*
  - 编码声明*: 所有 Python 文件必须在文件开头添加 UTF-8 编码声明：`# -*- coding: utf-8 -*-`
  - 禁止特殊字符*: 禁止在代码中使用表情符号和特殊 Unicode 符号（如 emoji、数学符号等），保持代码可读性和兼容性。
- 日志模块*: 统一使用 `one_dragon_agent.core.system.log` 中的 `get_logger()` 获取日志对象。
- MySQL: 优先使用ORM进行MySQL相关查询。


#### 后端测试规范

当你编写测试代码时，必须遵守以下规范：

- 无测试包*: 不得在测试目录中创建 python package。
- 测试类和Fixtures*: 测试文件必须使用测试类（以 `Test` 为前缀）来组织相关的测试方法。您必须使用 `pytest.fixture` 来管理测试依赖和状态（例如对象实例的创建和拆卸），以提高代码的可重用性和可维护性。
- 导入约定*: 由于项目使用 `src-layout`，测试文件中的导入路径不得包含 `src` 目录。
  - 正确*: `from one_dragon_agent.core.agent import Agent`
  - 错误*: `from src.one_dragon_agent.core.agent import Agent`
- 运行测试*: 运行测试时*必须*使用 `uv run --env-file .env pytest ...`，因为环境变量中包含 `PYTHONPATH` 指向 src 目录。不使用 `--env-file .env` 会导致导入失败。
- 按功能组组织测试*: 测试文件应按功能相关性组织。
  - 示例组织*:
    ```
    tests/one_dragon_agent/core/agent/
    ├── test_agent_lifecycle.py      # 生命周期相关：__init__, start, stop
    ├── test_agent_execution.py      # 执行相关：execute_main_loop, execute_step
    ├── test_agent_message.py        # 消息处理：send, receive, broadcast
    └── test_agent_state.py          # 状态管理：get_state, set_state
    ```
  - 对于特别复杂的方法，可以单独创建测试文件
  - 简单方法应合并到相关功能组的测试文件中
- 异步测试装饰器*: 所有异步测试方法必须同时包含 `@pytest.mark.asyncio` 和 `@pytest.mark.timeout` 装饰器。
- 临时文件*: 使用当前工作目录下的 `.temp` 目录来存储临时文件。
- 保证逻辑正确*: 除非源代码逻辑有错误，否则不能因为测试不通过而修改源代码。
- 诚实原则*: 当测试用例失败且您不知道原因或如何修复时，应停下来询问下一步该怎么做。
- 测试数据清理*: 后端测试也会产生数据库数据，必须在测试完成后清理所有测试数据。
  - 使用 pytest fixture 的 `yield` 和 `finalizer` 机制确保测试后清理。
  - 测试数据必须使用 `test_` 前缀标记（如 id 为 `test_user_123` 或 name 为 `test_session_abc`），便于识别和清理。
  - 端到端测试后必须调用清理接口，确保不留下脏数据。
- 大模型选用 - 测试时如果需要使用真实的大模型，必须要使用 `ModelScope-Free` 下的 `moonshotai/Kimi-K2.5` 模型。

## 前端开发规范

- 未有

### 前端测试规范

- 你可以先制定测试计划，或者只在测试文件上写注释说明需要测试的场景。
- 在编写具体测试代码前，你必须要先使用 chrome-devtools 工具进行调试，确保前端运作和测试预期一致。如果不一致，则可能是代码问题或者测试计划问题，进行修改。
- chrome-devtools工具需要先启动chrome实例，并固定连接9222端口。你需要先判断chrome实例是否在运行，如果没有，你必须使用 `chromium-browser --headless --remote-debugging-port=9222 --no-sandbox --disable-gpu > /dev/null 2>&1` 在后台启动一个chrome实例。
- 使用 chrome-devtools 调试成功后，再编写具体的测试代码。
- 测试过程遇到问题时，应积极使用 chrome-devtools 工具进行调试。
- 进行 Playwright 的 E2E 测试时，必须使用 headless 模式。
- 测试数据清理：E2E 测试会产生真实的数据库数据，必须确保测试后正确清理。
  - 后端提供测试数据清理接口，仅在非生产环境可用，通过请求头验证测试令牌。
  - 所有测试创建的数据使用 `test_` 前缀标记（如 id 为 `test_user_123` 或 name 为 `test_session_abc`），以便清理接口识别。
  - 在 Playwright 测试中使用 `beforeEach` 和 `afterEach` 钩子调用清理接口，确保测试前后数据库处于干净状态。
  - 测试令牌通过 `TEST_TOKEN` 环境变量配置，在 `.env.test` 和 Playwright 配置中设置。
- 仅操作测试数据: 编写测试流程时，必须只操作测试数据，不能操作真实数据，如果缺少测试数据，则测试流程中需要制造测试数据来完成测试。
- 大模型选用 - 测试时如果需要使用真实的大模型，必须要使用 `ModelScope-Free` 下的 `moonshotai/Kimi-K2.5` 模型。


## 工具说明

- opsx - 保持使用 opsx 工具，按 spec-driven 的方式进行开发。
- context7 - 积极使用 context7 工具搜索使用文档。例如，设计时需要了解依赖库的能力、开发测试时遇到调用方法不存在、参数个数不一致、参数类型不一致等场景。
- tushare-docs-mcp - 对于tushare库，是用 tushare-docs-mcp 工具进行搜索文档，而不是 context7。
- Bash:
  - 需要临时运行服务时，使用Bash工具原生的后台运行能力，而不是在命令中增加 `nohup` 或者 后缀 `&` 的方式运行。
  - 禁止调用Bash时传入多行命令，如果需要，先在临时文件夹生成复杂脚本，再运行。
  - 运行 openspec 命令时，必须要在项目根目录下。
- agent team - 启动 agent team 时，leader需要同步更新opsx状态。

