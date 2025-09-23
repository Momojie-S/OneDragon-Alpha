import json
from typing import Optional

from agentscope.message import TextBlock
from agentscope.tool import ToolResponse

from tushare_mcp_server.main import income


async def tushare_income(
    ts_code: str,
    report_type: str,
    start_ann_date: Optional[str] = None,
    end_ann_date: Optional[str] = None,
    period: Optional[str] = None,
) -> ToolResponse:
    """
    根据 ts_code 获取某个上市公司的财务利润表数据。

    Args:
        ts_code (str): 股票代码
        report_type (str): 报告类型: "1"=合并报表, "2"=单季合并报表
        start_ann_date (str): 发布公告日期 开始(包含)
        end_ann_date (str): 发布公告日期 结束(包含)
        period (str): 报告期

    Returns:
        匹配的股票信息的字典列表。
        示例: [{"ts_code": "000001.SZ", "净利润(不含少数股东损益)": 10000}, ...]
    """

    data = await income(
        ts_code=ts_code,
        report_type=report_type,
        start_ann_date=start_ann_date,
        end_ann_date=end_ann_date,
        period=period,
    )
    return ToolResponse(
        content=[
            TextBlock(
                type="text",
                text=json.dumps(data, ensure_ascii=False, separators=(',', ':')),
            ),
        ]
    )