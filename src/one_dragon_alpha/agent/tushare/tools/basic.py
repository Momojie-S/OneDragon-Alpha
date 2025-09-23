import json

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from tushare_mcp_server.main import stock_basic_by_name_like


async def tushare_stock_basic_by_name_like(name_like: str) -> ToolResponse:
    """
    根据股票名称模糊查询获取A股的ts_code和名称。
    例如：name_like="东财"可以匹配到"东方财富"，因为"东"和"财"在"东方财富"中。

    Args:
        name_like: 要搜索的股票名称关键词，支持按字符顺序的模糊匹配

    Returns:
        匹配的股票信息的字典列表。
        示例: [{"ts_code": "000001.SZ", "股票名称": "平安银行"}, ...]
    """
    data = await stock_basic_by_name_like(name_like)
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=json.dumps(data, ensure_ascii=False, separators=(',', ':')),
            ),
        ]
    )
