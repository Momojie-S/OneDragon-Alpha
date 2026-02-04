# OneDragon Alpha

基于 AgentScope 的智能交易系统，集成 Qwen 大模型和 AKShare 数据源。

## 特性

- 🤖 **AgentScope 集成** - 使用 AgentScope 框架构建多智能体系统
- 🧠 **Qwen 模型支持** - 集成 Qwen 大模型，支持 OAuth 2.0 自动认证
- 📊 **数据源集成** - 集成 AKShare 和 Tushare 获取金融数据
- 💾 **数据持久化** - MySQL 存储历史数据和分析结果
- 🚀 **FastAPI 后端** - 高性能异步 API 服务

## 快速开始

### 环境要求

- Python >= 3.11
- uv (Python 包管理工具)

### 安装

```bash
# 安装依赖
uv sync --group dev

# 安装 one_dragon_agent 包
uv pip install -e .
```

### 配置

复制环境变量示例文件并配置：

```bash
cp .env.example .env
# 编辑 .env 文件，配置必要的参数
```

### 使用 Qwen 模型

首次使用需要通过 OAuth 2.0 进行认证：

```python
import asyncio
from one_dragon_agent.core.model.qwen import QwenChatModel, login_qwen_oauth, QwenTokenManager

async def main():
    # 1. 进行 OAuth 认证
    await login_qwen_oauth()

    # 2. 创建模型实例
    model = QwenChatModel(model_name="coder-model")

    # 3. 使用模型
    response = model("你好！")
    print(response)

    # 4. 关闭 token 管理器
    await QwenTokenManager.get_instance().shutdown()

asyncio.run(main())
```

详细文档请参考：[Qwen 模型集成文档](docs/develop/modules/qwen-model.md)

## 项目结构

```text
OneDragon-Alpha/
├── src/one_dragon_agent/      # 源代码
│   └── core/
│       ├── model/             # 模型相关（包括 Qwen 模型）
│       ├── system/            # 系统工具（日志等）
│       └── ...                # 其他核心模块
├── tests/                     # 测试代码
├── docs/                      # 文档
├── examples/                  # 示例代码
└── frontend/                  # Vue 前端
```

## 开发

### 运行测试

```bash
# 运行所有测试
uv run --env-file .env pytest tests/

# 运行特定模块测试
uv run --env-file .env pytest tests/one_dragon_agent/core/model/qwen/
```

### 代码质量检查

```bash
# 代码检查
uv run ruff check src/ tests/

# 代码格式化
uv run ruff format src/ tests/
```

## 技术栈

### 后端
- **FastAPI** - 异步 Web 框架
- **AgentScope** - 多智能体框架
- **SQLAlchemy** - ORM
- **aiomysql** - 异步 MySQL 驱动

### 数据源
- **AKShare** - 金融数据接口
- **Tushare** - 股票数据接口

### 前端
- **Vue 3** - 前端框架
- **Element Plus** - UI 组件库
- **Element Plus X** - 扩展组件

## 许可证

[待添加]

## 贡献

欢迎提交 Issue 和 Pull Request！
