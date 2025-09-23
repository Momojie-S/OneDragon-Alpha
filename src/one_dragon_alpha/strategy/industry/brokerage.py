import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import tushare as ts
from tushare.pro.client import DataApi


def _get_ts_client() -> DataApi:
    return ts.pro_api(os.getenv("TUSHARE_API_TOKEN"))


def _get_dt(day_delta: int = 0) -> str:
    """
    
    Args:
        day_delta: 天偏移量

    Returns:
        str: 日期的 YYYYMMDD 格式
    """
    target_date = datetime.now() + timedelta(days=day_delta)
    return target_date.strftime("%Y%m%d")


def _get_next_period(period: str) -> str:
    """
    根据当前周期计算下一个周期

    Args:
        period: 当前周期，格式为 YYYYMMDD（季度末日期）

    Returns:
        str: 下一个周期，格式为 YYYYMMDD
    """
    year = int(period[:4])
    month = int(period[4:6])

    if month == 3:  # 第一季度 -> 第二季度
        return f"{year}0630"
    elif month == 6:  # 第二季度 -> 第三季度
        return f"{year}0930"
    elif month == 9:  # 第三季度 -> 第四季度
        return f"{year}1231"
    elif month == 12:  # 第四季度 -> 下一年第一季度
        return f"{year + 1}0331"
    else:
        raise ValueError(f"无效的周期格式: {period}. 期望季度末日期 (0331, 0630, 0930, 1231)")


def _get_quarter_start_date(quarter_end_date: str) -> str:
    """
    根据季度最后一天获取季度第一天

    Args:
        quarter_end_date: 季度最后一天，格式为 YYYYMMDD

    Returns:
        str: 季度第一天，格式为 YYYYMMDD
    """
    year = int(quarter_end_date[:4])
    month = int(quarter_end_date[4:6])

    if month == 3:  # 第一季度 (1-3月)
        return f"{year}0101"
    elif month == 6:  # 第二季度 (4-6月)
        return f"{year}0401"
    elif month == 9:  # 第三季度 (7-9月)
        return f"{year}0701"
    elif month == 12:  # 第四季度 (10-12月)
        return f"{year}1001"
    else:
        raise ValueError(f"无效的季度末日期: {quarter_end_date}. 期望季度末日期 (0331, 0630, 0930, 1231)")


def trade_date_to_period(trade_date: str) -> str:
    """
    将交易日期转换为对应的季度周期（季度结束日期）

    Args:
        trade_date: 交易日期，格式为 YYYYMMDD

    Returns:
        str: 季度结束日期，格式为 YYYYMMDD
    """
    trade_dt = datetime.strptime(trade_date, '%Y%m%d')
    year = trade_dt.year
    month = trade_dt.month

    if month <= 3:
        return f"{year}0331"
    elif month <= 6:
        return f"{year}0630"
    elif month <= 9:
        return f"{year}0930"
    else:
        return f"{year}1231"


def _get_turnover(
    ts_code: str,
    quarter_start_date: str,
    quarter_end_date: str,
) -> pd.DataFrame:
    """
    获取某个指数在指定季度内的交易额

    Args:
        ts_code: 指数代码
        quarter_start_date: 季度开始日期 YYYYMMDD
        quarter_end_date: 季度结束日期 YYYYMMDD

    Returns:
        pd.DataFrame: 交易额数据 ["ts_code": 指数代码, "trade_date": 交易日期, "amount": 交易额(千元)]
    """
    client = _get_ts_client()
    return client.index_daily(
        ts_code=ts_code,
        start_date=quarter_start_date,
        end_date=quarter_end_date,
        fields=['ts_code', 'trade_date', 'amount']
    )


def _get_all_turnover_by_period(
    start_period: str,
    end_period: str
) -> pd.DataFrame:
    """
    通过指数来获取整个A股的单个季度的交易额(元)

    Args:
        start_period: 开始季度，传入要查询的季度的最后一天的日期，比如，20170331一季度，20170630二季度，20170930三季度 20171231四季度
        end_period: 结束季度，传入要查询的季度的最后一天的日期

    Returns:
        pd.DataFrame: 每个季度的交易额 ["period": 季度结束日期, "total_turnover": 总交易额(元)]
    """
    index_ts_code_list = ['000001.SH', '399107.SZ']  # 上证指数、深圳A股指数

    # 生成所有需要查询的周期
    periods = []
    current_period = start_period
    while current_period <= end_period:
        periods.append(current_period)
        current_period = _get_next_period(current_period)

    # 获取每个指数在所有周期内的交易额数据
    all_index_data = []
    for ts_code in index_ts_code_list:
        # 获取该指数最早周期的开始日期
        earliest_start_date = _get_quarter_start_date(start_period)
        latest_end_date = end_period

        # 一次性获取该指数在所有周期内的数据
        index_data = _get_turnover(ts_code, earliest_start_date, latest_end_date)
        if not index_data.empty:
            index_data['index_code'] = ts_code  # 添加指数代码标识
            all_index_data.append(index_data)

    if not all_index_data:
        # 如果没有数据，返回空的DataFrame
        return pd.DataFrame({
            'period': periods,
            'total_turnover': [0] * len(periods)
        })

    # 合并所有指数数据
    combined_index_data = pd.concat(all_index_data, ignore_index=True)

    # 将交易日期转换为period（季度结束日期）
    combined_index_data['period'] = combined_index_data['trade_date'].apply(trade_date_to_period)

    # 按period和指数代码分组，计算每个季度的总交易额
    period_turnover = combined_index_data.groupby(['period', 'index_code'])['amount'].sum().reset_index()

    # 按period分组，计算所有指数的总交易额
    total_turnover_by_period = period_turnover.groupby('period')['amount'].sum().reset_index()
    total_turnover_by_period = total_turnover_by_period.rename(columns={'amount': 'total_turnover'})

    # 确保所有周期都有数据，没有数据的周期填充0
    all_periods_df = pd.DataFrame({'period': periods})
    result_df = pd.merge(all_periods_df, total_turnover_by_period, on='period', how='left')
    result_df['total_turnover'] = result_df['total_turnover'].fillna(0)

    # 将交易额从千元转换为元
    result_df['total_turnover'] = result_df['total_turnover'] * 1000

    return result_df


def _get_dc_member(
    ts_code: str,
    trade_date: str
) -> pd.DataFrame:
    """
    获取某天的东财概念成分股
    只有2025年数据

    Args:
        ts_code: 板块指数代码
        trade_date: 交易日期（YYYYMMDD格式）

    Returns:
        pd.DataFrame: 板块成员数据 ["ts_code": 成分股票代码, "name": 股票名称]
    """
    client = _get_ts_client()
    latest_trade_date = _get_latest_trade_date(trade_date)
    df = client.dc_member(
        ts_code=ts_code,
        trade_date=latest_trade_date,
        fields=["trade_date", 'con_code', 'name']
    )
    df = df.rename(columns={"con_code": "ts_code"})
    return df


def _get_latest_trade_date(date_str: str) -> str:
    """
    Args:
        date_str: 日期 YYYYMMDD格式

    Returns:
        str: 指定日期之前(包含)的最后一个交易日
    """
    client = _get_ts_client()
    is_current_trade_date = False
    pretrade_date = '19000101'
    for exchange in ['SSE', 'SZSE']:  # 上交所, 深交所
        df = client.trade_cal(
            exchange=exchange,
            start_date=date_str,
            end_date=date_str,
            fields=['cal_date', 'is_open', 'pretrade_date']
        )
        if len(df) == 0:
            continue

        # 如果当前是交易日 就取当日 否则取上一个交易日
        if df.iloc[0]['is_open'] == 1:
            is_current_trade_date = True
        else:
            pretrade_date = max(df.iloc[0]['pretrade_date'], pretrade_date)

    if is_current_trade_date:
        return date_str
    else:
        return pretrade_date


def _get_income(
    ts_code: str,
    end_date_from: str,
    end_date_to: str,
) -> pd.DataFrame:
    """
    获取某个股票的单个季度的净利润

    Args:
        ts_code: 股票代码 (证券)
        end_date_from: 起始报告期(每个季度最后一天的日期，比如，20170331一季报，20170630半年报，20170930三季报 20171231年报)
        end_date_to: 结束报告期

    Returns:
        pd.DataFrame: 利润数据 ["ts_code": 股票代码, "end_date": 季度最后一天, "n_income_attr_p": 净利润(不含少数股东损益)(元)]
    """
    client = _get_ts_client()
    df = client.income(
        ts_code=ts_code,
        report_type='2',  # 单季合并
        fields=['ts_code', 'end_date', 'n_income_attr_p']
    )
    return df[(df['end_date'] >= end_date_from) & (df['end_date'] <= end_date_to)]


def get_brokerage_profits_by_period(
    start_period: str,
    end_period: str
) -> pd.DataFrame:
    """
    获取券商上市公司在指定时间范围内的利润数据

    Args:
        start_period: 开始季度，传入要查询的季度的最后一天的日期，比如，20170331一季度，20170630二季度，20170930三季度 20171231四季度
        end_period: 结束季度，传入要查询的季度的最后一天的日期

    Returns:
        pd.DataFrame: 券商公司的利润数据
                     ["end_date": 季度结束日期, "ts_code": 股票代码, "name": 股票名称, "n_income_attr_p": 净利润(元)]
    """
    brokerage_index_ts_code = 'BK0711.DC'  # 东财的券商概念版块
    # 获取最新的券商板块成分股
    dc_member_df = _get_dc_member(brokerage_index_ts_code, _get_dt(-1))

    if dc_member_df.empty:
        return pd.DataFrame(columns=['end_date', 'ts_code', 'name', 'n_income_attr_p'])

    all_dfs = []

    # 获取每个券商公司在指定时间范围内的利润数据
    for _, row in dc_member_df.iterrows():
        ts_code = row['ts_code']
        name = row['name']

        # 获取该公司在时间范围内的所有季度利润数据
        income_df = _get_income(ts_code, start_period, end_period)

        if not income_df.empty:
            # 直接添加name列
            income_df['name'] = name
            all_dfs.append(income_df)

    if not all_dfs:
        return pd.DataFrame(columns=['end_date', 'ts_code', 'name', 'n_income_attr_p'])

    # 合并所有DataFrame
    return pd.concat(all_dfs, ignore_index=True)


def _get_analyse_df(
    start_period: str,
    end_period: str,
) -> pd.DataFrame:
    # 获取券商利润数据
    brokerage_df = get_brokerage_profits_by_period(start_period, end_period)
    # 获取A股市场交易额数据
    turnover_df = _get_all_turnover_by_period(start_period, end_period)

    if brokerage_df.empty or turnover_df.empty:
        return pd.DataFrame()

    # 将brokerage_df的end_date重命名为period以匹配turnover_df的列名
    brokerage_df = brokerage_df.rename(columns={'end_date': 'period'})

    merged_df = pd.merge(
        brokerage_df,
        turnover_df,
        on="period",
        how="inner",
    )

    return merged_df


def analyse(start_period: str = "20150331", end_period: str = "20250630"):
    """
    分析券商利润与市场交易额的关系并绘制图表

    Args:
        start_period: 开始季度，格式为 YYYYMMDD
        end_period: 结束季度，格式为 YYYYMMDD
    """
    # 获取合并后的数据
    merged_df = _get_analyse_df(start_period, end_period)

    if merged_df.empty:
        print("没有获取到数据，请检查参数和网络连接")
        return

    import matplotlib.pyplot as plt
    # 设置中文字体支持
    plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'SimSun', 'Arial Unicode MS']
    plt.rcParams['axes.unicode_minus'] = False

    # 创建图表
    fig, ax1 = plt.subplots(figsize=(14, 8))

    # 将period转换为日期格式
    merged_df['period_date'] = pd.to_datetime(merged_df['period'], format='%Y%m%d')

    # 获取所有券商列表
    brokers = merged_df['name'].unique()

    # 计算每个券商的总利润，选择前N个最大的券商显示
    broker_total_profit = merged_df.groupby('name')['n_income_attr_p'].sum().sort_values(ascending=False)
    top_n = 6  # 显示前6个最大的券商（堆叠面积图适合显示较少的类别）
    top_brokers = broker_total_profit.head(top_n).index.tolist()

    # 其他券商合并为"其他券商"
    other_brokers = [broker for broker in brokers if broker not in top_brokers]

    # 准备堆叠面积图数据
    area_data = []
    area_labels = []

    # 添加前N个券商的数据
    for broker in top_brokers:
        broker_data = merged_df[merged_df['name'] == broker]
        broker_summary = broker_data.groupby('period_date')['n_income_attr_p'].sum().reset_index()
        area_data.append(broker_summary['n_income_attr_p'].values)
        area_labels.append(broker)

    # 添加其他券商的数据
    if other_brokers:
        other_data = merged_df[merged_df['name'].isin(other_brokers)]
        other_summary = other_data.groupby('period_date')['n_income_attr_p'].sum().reset_index()
        area_data.append(other_summary['n_income_attr_p'].values)
        area_labels.append('其他券商')

    # 创建堆叠面积图
    period_dates = merged_df['period_date'].unique()
    period_dates = np.sort(period_dates)

    # 确保所有数据按日期对齐
    aligned_data = []
    for i, broker_data in enumerate(area_data):
        broker_series = pd.Series(broker_data, index=period_dates[:len(broker_data)])
        aligned_broker = broker_series.reindex(period_dates, fill_value=0)
        aligned_data.append(aligned_broker.values)

    # 绘制堆叠面积图
    ax1.stackplot(period_dates, aligned_data, labels=area_labels, alpha=0.8)
    ax1.set_xlabel('季度')
    ax1.set_ylabel('净利润 (元)', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    ax1.grid(True, alpha=0.3)

    # 创建第二个Y轴（交易额）
    ax2 = ax1.twinx()

    # 获取交易额数据并按日期排序
    turnover_data = merged_df[['period_date', 'total_turnover']].drop_duplicates()
    turnover_data = turnover_data.sort_values('period_date')
    ax2.plot(turnover_data['period_date'], turnover_data['total_turnover'],
             color='red', marker='s', linewidth=3, label='市场交易额')

    # 设置第二个Y轴（交易额）
    ax2.set_ylabel('市场交易额 (元)', color='r')
    ax2.tick_params(axis='y', labelcolor='r')

    # 合并图例
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

    # 设置标题
    plt.title('券商利润与市场交易额关系分析', fontsize=16, pad=20)

    # 调整X轴标签
    plt.xticks(rotation=45)
    plt.tight_layout()

    # 显示图表
    plt.show()


if __name__ == "__main__":
    analyse()