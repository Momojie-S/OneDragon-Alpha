import json
import os
from typing import AsyncGenerator, Optional

from agentscope.agent import AgentBase, ReActAgent
from agentscope.formatter import OpenAIChatFormatter
from agentscope.mcp import HttpStatelessClient
from agentscope.memory import InMemoryMemory, MemoryBase
from agentscope.message import Msg, TextBlock
from agentscope.model import OpenAIChatModel
from agentscope.tool import (
    Toolkit,
    ToolResponse,
    insert_text_file,
    view_text_file,
    write_text_file,
)

from one_dragon_alpha.agent.tushare.tools.basic import tushare_stock_basic_by_name_like
from one_dragon_alpha.agent.tushare.tools.financial import tushare_income
from one_dragon_alpha.session.session import Session
from one_dragon_alpha.tool.code import execute_python_code_by_path
from one_dragon_agent.core.model.model_factory import ModelFactory
from one_dragon_agent.core.model.models import ModelConfigInternal


class TushareSession(Session):
    def __init__(
        self,
        session_id: str,
        memory: MemoryBase,
    ):
        # 创建占位符模型(不会真正使用,会在首次调用 set_model 时被替换)
        placeholder_model = OpenAIChatModel(
            model_name="placeholder",
            api_key="placeholder",
            client_args={"base_url": "https://placeholder.com"},
        )

        Session.__init__(
            self,
            agent=self._get_main_agent(memory, placeholder_model),
            session_id=session_id,
            memory=memory,
        )

        self._workspace_dir = os.getenv("WORKSPACE_DIR")
        self._analyse_by_code_map: dict[int, AgentBase] = {}
        self._current_analyse_id: int = 0

        # 模型配置缓存
        self._current_model_config_id: int | None = None
        self._current_model_id: str | None = None

    def _get_main_agent(self, memory: MemoryBase, model) -> AgentBase:
        """创建主 Agent.

        Args:
            memory: 记忆对象
            model: 模型实例

        Returns:
            AgentBase: Agent 实例
        """
        toolkit = Toolkit()

        toolkit.register_tool_function(tushare_stock_basic_by_name_like)
        toolkit.register_tool_function(tushare_income)
        toolkit.register_tool_function(self.analyse_by_code)
        toolkit.register_tool_function(self.display_analyse_by_code_result)

        agent = ReActAgent(
            name="OneDragon",
            sys_prompt=_MAIN_SYSTEM_PROMPT,
            model=model,
            memory=memory,
            formatter=OpenAIChatFormatter(),
            toolkit=toolkit,
            max_iters=100,
        )

        return agent

    def set_model(self, config: ModelConfigInternal, model_id: str):
        """设置模型配置并重建主 Agent.

        Args:
            config: 模型配置对象(包含 api_key)
            model_id: 要使用的模型 ID

        """
        # 检查是否需要切换
        if (
            self._current_model_config_id == config.id
            and self._current_model_id == model_id
        ):
            # 模型未变化，无需重建
            return

        # 使用 ModelFactory 创建模型
        model = ModelFactory.create_model(config, model_id)

        # 创建新的主 Agent(复用 _get_main_agent 方法)
        new_agent = self._get_main_agent(self.memory, model)

        # 替换 Agent
        self.agent = new_agent

        # 重新注册 hook 到新的 Agent
        self.agent.register_instance_hook(
            hook_type="pre_print",
            hook_name="chat_capture",
            hook=self._pre_print_hook,
        )

        # 更新缓存
        self._current_model_config_id = config.id
        self._current_model_id = model_id

        # 清空分析 Agent 缓存，强制重建
        self._analyse_by_code_map.clear()

    async def chat(
        self,
        user_input: str,
        model_config_id: int,
        model_id: str,
        config: ModelConfigInternal,
    ) -> AsyncGenerator:
        """处理聊天消息.

        Args:
            user_input: 用户消息内容
            model_config_id: 模型配置 ID
            model_id: 模型 ID
            config: 模型配置对象（已验证）

        Yields:
            SessionMessage 对象
        """
        # 检查是否需要切换模型
        if (
            self._current_model_config_id != model_config_id
            or self._current_model_id != model_id
        ):
            self.set_model(config, model_id)

        # 调用父类的 chat 方法（不传递 model_config_id 和 model_id）
        async for message in super().chat(user_input):
            yield message

    async def display_analyse_by_code_result(
        self,
        analyse_id: int,
    ) -> ToolResponse:
        """
        使用本工具，可以将analyse_by_code的结果显示到用户的前端。
        Args:
            analyse_id (int): 分析ID。
        """
        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=json.dumps(
                        {"analyse_id": analyse_id},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            ]
        )

    async def analyse_by_code(
        self,
        goal: str,
        analyse_id: Optional[int] = None,
    ) -> ToolResponse:
        """
        通过编写python代码，进行股票的数据分析

        Args:
            goal (str): 需要写代码进行分析的目标
            analyse_id (Optional[int]): 分析ID，传入后继续在原有分析基础上修改，否则开启一个新的分析。
        """
        if analyse_id is None:
            self._current_analyse_id += 1
            analyse_id = self._current_analyse_id

        agent = await self._get_analyse_by_code_agent(analyse_id)
        msg = await agent(Msg(name="user", content=goal, role="user"))

        return ToolResponse(
            content=[
                TextBlock(
                    type="text",
                    text=json.dumps(
                        {"analyse_id": analyse_id, "result": msg.to_dict()},
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                )
            ]
        )

    async def _get_analyse_by_code_agent(self, analyse_id: int) -> AgentBase:
        if analyse_id in self._analyse_by_code_map:
            return self._analyse_by_code_map[analyse_id]

        analyse_workspace = self._get_analyse_by_code_dir(analyse_id)

        toolkit = Toolkit()
        toolkit.register_tool_function(view_text_file)
        toolkit.register_tool_function(write_text_file)
        toolkit.register_tool_function(insert_text_file)
        toolkit.register_tool_function(execute_python_code_by_path)
        context7 = HttpStatelessClient(
            name="context7",
            transport="streamable_http",
            url="https://mcp.context7.com/mcp",
            headers={"Authorization": f"Bearer {os.getenv('CONTEXT7_API_KEY')}"},
        )
        await toolkit.register_mcp_client(context7)

        # 使用与主 Agent 相同的模型
        agent = ReActAgent(
            name=f"OdaAnalyseByCode{analyse_id}",
            sys_prompt=self._get_analyse_by_code_sys_prompt(analyse_workspace),
            model=self.agent.model,
            memory=InMemoryMemory(),
            formatter=OpenAIChatFormatter(),
            toolkit=toolkit,
            max_iters=100,
        )

        self._analyse_by_code_map[analyse_id] = agent
        return agent

    def _get_analyse_by_code_dir(self, analyse_id: int) -> str:
        base_dir = os.path.join(self._workspace_dir, "analyse_by_code")
        if not os.path.exists(base_dir):
            os.makedirs(base_dir)

        current_dir = os.path.join(base_dir, f"{self.session_id}-{analyse_id}")
        if not os.path.exists(current_dir):
            os.makedirs(current_dir)

        dotenv_file = os.path.join(current_dir, ".env")
        with open(dotenv_file, "w") as f:
            f.write(f"TUSHARE_API_TOKEN={os.getenv('TUSHARE_API_TOKEN')}")

        return current_dir

    def _get_analyse_by_code_sys_prompt(self, analyse_workspace: str) -> str:
        return _ANALYSE_BY_CODE_SYSTEM_PROMPT % (analyse_workspace)


_MAIN_SYSTEM_PROMPT = """
你是叫OneDragonAlpha的股票分析助手。

# 行为规范

- 对于提问涉及的股票，必须先使用tushare_stock_basic_by_name_like工具获取真实的股票代码和名称。
- 确定股票代码和名称后，必须先判断是否应该调用analyse_by_code工具。

# 工具使用规范

- 以下情况优先使用analyse_by_code工具：
    1. 需要多种数据组合分析的场景。
    2. 需要多个步骤，有数学运算或同级的场景。
    3. 使用图表展示更有利于呈现分析过程或者结果的场景。
- 使用analyse_by_code工具后，应该使用display_analyse_by_code_result工具将分析结果展示。
- 其他情况优先使用tushare相关工具来获取股票相关信息。

## tushare工具规范说明

- tushare工具使用的股票代码参数都叫ts_code，每种股票代码都有规范的后缀
    - 上海证券交易所: 后缀是 .SH 例如 600000.SH(股票) 000001.SH(0开头指数)
    - 深圳证券交易所: 后缀是 .SZ 例如 000001.SZ(股票) 399005.SZ(3开头指数)
    - 北京证券交易所: 后缀是 .BJ 例如 920819.BJ(9、8和4开头的股票)
    - 香港证券交易所: 后缀是 .HK 例如 00001.HK
- 必须先使用tushare_stock_basic_by_name_like工具来获取具体的ts_code，不能编造。
- 日期相关字段如无特殊说明都使用 YYYYMMDD 格式。
- 股票报告期使用的都是该季度最后一天的日期，例如，20170331=一季度，20170630=二季度，20170930=三季度 20171231=四季度。
"""


_ANALYSE_BY_CODE_SYSTEM_PROMPT = """
你是叫OneDragonAlpha的股票分析助手，通过编写python代码的方式进行股票分析。

# 核心任务

你需要按以下步骤，完成所需的股票分析：

1. 在当前工作目录下，编写 "main.py" 文件，完成所有分析逻辑并按输出规范输出。
2. 使用execute_python_code_by_path工具运行"main.py"，注意传入完整的绝对路径。
3. 运行"main.py"失败时，需要继续修改，直至运行成功。
4. 运行"main.py"成功后，只需回复查看"result.json"获取结果，无需输出分析结论。

# 代码规范

- 使用 python 3.11 的语法。
- 使用 tushare 库来获取股票相关信息。
- 使用 dotenv 来读取环境变量。
- 不需要捕捉异常，整个代码逻辑应该能正常运行，不应该出现异常。
- 定义一个存放当前工作目录的变量，不要使用 os.pwd()，使用系统提示的完整的绝对路径。
- 优先使用pandas相关函数处理数据，避免for遍历。
- 必须要有对结果数据的校验逻辑，校验不通过时，抛出异常。
- 不清楚依赖库的使用方法时，使用context7查询相关文档。
- 必须使用标准库获取当前时间，再计算其他对应的所需的时间字段。

## Tushare库使用规范

- 使用环境变量 TUSHARE_API_TOKEN 获取 token。
- tushare工具使用的股票代码参数都叫ts_code，每种股票代码都有规范的后缀
    - 上海证券交易所: 后缀是 .SH 例如 600000.SH(股票) 000001.SH(0开头指数)
    - 深圳证券交易所: 后缀是 .SZ 例如 000001.SZ(股票) 399005.SZ(3开头指数)
    - 北京证券交易所: 后缀是 .BJ 例如 920819.BJ(9、8和4开头的股票)
    - 香港证券交易所: 后缀是 .HK 例如 00001.HK
- 日期相关字段如无特殊说明都使用 YYYYMMDD 格式。
- 股票报告期使用的都是该季度最后一天的日期，例如，20170331=一季度，20170630=二季度，20170930=三季度 20171231=四季度。
- 使用context7查询tushare相关文档时，应该：
    - 选择Title="Tushare Pro"的库。
    - 不需要特殊说明中国股市，因为这个库主要就是服务中国股市的。

## 输出规范

"main.py" 的逻辑，必须要包含在当前工作目录下输出一个 "result.json"，存放分析结果。

"result.json" 中是一个object，包含以下字段:

- echarts_list: 一个数组，数组中每个元素代表一个图表的数据，使用标准的 ECharts 结构。

# 系统提示

- 当前的工作目录是 "%s"。禁止切换到任何其他目录。

"""
