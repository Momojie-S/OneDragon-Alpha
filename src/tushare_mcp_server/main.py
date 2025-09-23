import os
from typing import Any, Optional

import tushare as ts
from mcp.server.fastmcp import FastMCP

from tushare_mcp_server import str_utils

# 创建主MCP服务器实例
mcp = FastMCP("AKShare-MCP")
_ts_token = os.getenv("TUSHARE_API_TOKEN")

### 基础数据 ###
@mcp.tool(name="tushare_stock_basic_by_name_like")
async def stock_basic_by_name_like(
    name_like: str,
) -> list[dict[str, Any]]:
    """
    根据股票名称模糊查询获取A股的ts_code和名称。
    例如：name_like="东财"可以匹配到"东方财富"，因为"东"和"财"在"东方财富"中。

    Args:
        name_like: 要搜索的股票名称关键词，支持按字符顺序的模糊匹配

    Returns:
        匹配的股票信息的字典列表。
        示例: [{"ts_code": "000001.SZ", "股票名称": "平安银行"}, ...]
    """
    pro = ts.pro_api(_ts_token)
    df = pro.stock_basic(fields="ts_code,name")
    mask = df["name"].apply(lambda x: str_utils.is_subsequence(name_like, x))
    df = df[mask]
    df = df.rename(columns={"name": "股票名称"})
    return df.to_dict('records')


### 财务数据 ###
async def income(
    ts_code: str,
    report_type: str,
    start_ann_date: Optional[str] = None,
    end_ann_date: Optional[str] = None,
    period: Optional[str] = None,
) -> list[dict[str, Any]]:
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
    pro = ts.pro_api(_ts_token)
    df = pro.income(
        ts_code=ts_code,
        report_type=report_type,
        start_date=start_ann_date,
        end_date=end_ann_date,
        period=period,
    )

    # 定义字段映射关系
    field_mapping = {
        "ann_date": "公告日期",
        "end_date": "报告期",
        "basic_eps": "基本每股收益",
        "diluted_eps": "稀释每股收益",
        "total_revenue": "营业总收入",
        "revenue": "营业收入",
        "int_income": "利息收入",
        "prem_earned": "已赚保费",
        "comm_income": "手续费及佣金收入",
        "n_commis_income": "手续费及佣金净收入",
        "n_oth_income": "其他经营净收益",
        "n_oth_b_income": "其他业务净收益",
        "prem_income": "保险业务收入",
        "out_prem": "分出保费",
        "une_prem_reser": "提取未到期责任准备金",
        "reins_income": "分保费收入",
        "n_sec_tb_income": "代理买卖证券业务净收入",
        "n_sec_uw_income": "证券承销业务净收入",
        "n_asset_mg_income": "受托客户资产管理业务净收入",
        "oth_b_income": "其他业务收入",
        "fv_value_chg_gain": "公允价值变动净收益",
        "invest_income": "投资净收益",
        "ass_invest_income": "对联营企业和合营企业的投资收益",
        "forex_gain": "汇兑净收益",
        "total_cogs": "营业总成本",
        "oper_cost": "营业成本",
        "int_exp": "利息支出",
        "comm_exp": "手续费及佣金支出",
        "biz_tax_surchg": "营业税金及附加",
        "sell_exp": "销售费用",
        "admin_exp": "管理费用",
        "fin_exp": "财务费用",
        "assets_impair_loss": "资产减值损失",
        "prem_refund": "退保金",
        "compens_payout": "赔付总支出",
        "reser_insur_liab": "提取保险责任准备金",
        "div_payt": "保户红利支出",
        "reins_exp": "分保费用",
        "oper_exp": "营业支出",
        "compens_payout_refu": "摊回赔付支出",
        "insur_reser_refu": "摊回保险责任准备金",
        "reins_cost_refund": "摊回分保费用",
        "other_bus_cost": "其他业务成本",
        "operate_profit": "营业利润",
        "non_oper_income": "营业外收入",
        "non_oper_exp": "营业外支出",
        "nca_disploss": "非流动资产处置净损失",
        "total_profit": "利润总额",
        "income_tax": "所得税费用",
        "n_income": "净利润(含少数股东损益)",
        "n_income_attr_p": "净利润(不含少数股东损益)",
        "minority_gain": "少数股东损益",
        "oth_compr_income": "其他综合收益",
        "t_compr_income": "综合收益总额",
        "compr_inc_attr_p": "归属于母公司(或股东)的综合收益总额",
        "compr_inc_attr_m_s": "归属于少数股东的综合收益总额",
        "ebit": "息税前利润",
        "ebitda": "息税折旧摊销前利润",
        "insurance_exp": "保险业务支出",
        "undist_profit": "年初未分配利润",
        "distable_profit": "可分配利润",
        "rd_exp": "研发费用",
        "fin_exp_int_exp": "财务费用:利息费用",
        "fin_exp_int_inc": "财务费用:利息收入",
        "transfer_surplus_rese": "盈余公积转入",
        "transfer_housing_imprest": "住房周转金转入",
        "transfer_oth": "其他转入",
        "adj_lossgain": "调整以前年度损益",
        "withdra_legal_surplus": "提取法定盈余公积",
        "withdra_legal_pubfund": "提取法定公益金",
        "withdra_biz_devfund": "提取企业发展基金",
        "withdra_rese_fund": "提取储备基金",
        "withdra_oth_ersu": "提取任意盈余公积金",
        "workers_welfare": "职工奖金福利",
        "distr_profit_shrhder": "可供股东分配的利润",
        "prfshare_payable_dvd": "应付优先股股利",
        "comshare_payable_dvd": "应付普通股股利",
        "capit_comstock_div": "转作股本的普通股股利",
        "net_after_nr_lp_correct": "扣除非经常性损益后的净利润（更正前）",
        "credit_impa_loss": "信用减值损失",
        "net_expo_hedging_benefits": "净敞口套期收益",
        "oth_impair_loss_assets": "其他资产减值损失",
        "total_opcost": "营业总成本（二）",
        "amodcost_fin_assets": "以摊余成本计量的金融资产终止确认收益",
        "oth_income": "其他收益",
        "asset_disp_income": "资产处置收益",
        "continued_net_profit": "持续经营净利润",
        "end_net_profit": "终止经营净利润",
    }

    # 过滤掉不在field_mapping中的列
    df = df[[col for col in df.columns if col in field_mapping]]

    # 重命名列
    df = df.rename(columns=field_mapping)

    # 返回记录列表
    return df.to_dict('records')


async def forcast(ts_code: str) -> list[dict[str, Any]]:
    pass


if __name__ == "__main__":
    _pro = ts.pro_api(_ts_token)
    print(_pro.stock_basic(fields='ts_code,name'))