from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card, MessageManager
from datetime import datetime, timedelta
from feffery_dash_utils.style_utils import style
import feffery_antd_charts as fact
from dash import html, Input, Output, callback, callback_context, State, no_update
import uuid
import akshare as ak
import pandas as pd

# 二级菜单配置
title = '贵金属价格监控v2'
icon = 'antd-gold-v2'
order = 4
logger = Log.get_logger(__name__)

# 权限元数据
access_metas = (
    '贵金属价格监控-基础权限-v2',
)

# -------------------------- 核心配置 --------------------------
METAL_OPTIONS = [
    {'label': '黄金 (XAU)', 'value': 'XAU'},
    {'label': '铂金 (XPT)', 'value': 'XPT'},
    {'label': '白银 (XAG)', 'value': 'XAG'}
]
DEFAULT_METALS = ['XAU', 'XPT', 'XAG']
COLOR_MAP = {'XAU': '#FFD700', 'XPT': '#E5E4E2', 'XAG': '#C0C0C0'}
NAME_MAP = {'XAU': '黄金', 'XPT': '铂金', 'XAG': '白银'}
METAL_TICKER_MAP = {'XAU': 'AU0', 'XPT': 'PT0', 'XAG': 'AG0'}
KLINE_PERIOD = '60'


# -------------------------- 工具函数 --------------------------
def get_initial_chart_tip():
    return html.Div(
        fac.AntdEmpty(
            description='请选择时间范围（精确到小时）后，点击「查询」按钮查看小时级贵金属价格数据',
            style={'height': '700px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                   'fontSize': '16px'}
        ),
        key=f'initial-tip-{uuid.uuid4()}'
    )


def get_hourly_metal_data(start_datetime, end_datetime, metals):
    if not start_datetime:
        start_datetime = datetime.now() - timedelta(days=7)
    if not end_datetime:
        end_datetime = datetime.now()

    logger.info(f'获取小时级数据：时间范围[{start_datetime}~{end_datetime}]，金属{metals}')
    all_data = []
    latest_prices = {}  # 保存最新价格用于盈亏计算

    for metal in metals:
        ticker = METAL_TICKER_MAP.get(metal)
        if not ticker:
            logger.warning(f'无对应合约代码：{metal}')
            continue

        try:
            logger.info(f'调用小时级接口：ak.futures_zh_minute_sina(symbol={ticker}, period={KLINE_PERIOD})')
            df = ak.futures_zh_minute_sina(symbol=ticker, period=KLINE_PERIOD)

            if df.empty:
                logger.warning(f'{NAME_MAP[metal]}无小时级数据')
                MessageManager.warning(content=f'{NAME_MAP[metal]}暂无小时级真实数据')
                continue

            if 'datetime' not in df.columns:
                logger.warning(f'{NAME_MAP[metal]}数据无datetime列')
                continue
            df = df.dropna(subset=['datetime']).copy()
            if df.empty:
                logger.warning(f'{NAME_MAP[metal]}清洗后无有效数据')
                continue

            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            df = df.dropna(subset=['datetime']).copy()
            if df.empty:
                logger.warning(f'{NAME_MAP[metal]}时间转换后无有效数据')
                continue

            if 'close' not in df.columns:
                logger.warning(f'{NAME_MAP[metal]}数据无close列')
                continue
            df = df.dropna(subset=['close']).copy()
            if df.empty:
                logger.warning(f'{NAME_MAP[metal]}价格清洗后无有效数据')
                continue

            mask = (df['datetime'] >= start_datetime) & (df['datetime'] <= end_datetime)
            df_filtered = df.loc[mask].copy()

            if df_filtered.empty:
                logger.warning(f'{NAME_MAP[metal]}在指定时间范围无小时级数据')
                MessageManager.warning(
                    content=f'{NAME_MAP[metal]}暂无{start_datetime.strftime("%Y-%m-%d %H:%M")}~{end_datetime.strftime("%Y-%m-%d %H:%M")}的小时级数据（仅交易时间有数据）')
                continue

            # 保存最新价格
            if not df_filtered.empty:
                latest_row = df_filtered.iloc[-1]
                latest_close = latest_row['close']
                if metal == 'XAG':
                    latest_prices[metal] = round(latest_close / 1000, 4)
                else:
                    latest_prices[metal] = round(latest_close, 4)

            for _, row in df_filtered.iterrows():
                time_str = row['datetime'].strftime('%Y-%m-%d %H:%M')

                close_price = row['close']
                if pd.isna(close_price) or close_price is None:
                    continue

                if metal == 'XAG':
                    price_cny_per_gram = round(close_price / 1000, 4)
                else:
                    price_cny_per_gram = round(close_price, 4)

                all_data.append({
                    'datetime': time_str,
                    'metal': NAME_MAP[metal],
                    'price': price_cny_per_gram
                })

        except Exception as e:
            logger.error(f'获取{NAME_MAP[metal]}小时级数据失败：{e}', exc_info=True)
            MessageManager.error(content=f'获取{NAME_MAP[metal]}小时级数据失败：{str(e)}')
            continue

    all_data.sort(key=lambda x: x['datetime'])
    logger.info(f'获取到{len(all_data)}条小时级贵金属价格数据（单位：元/克）')
    return all_data, latest_prices


# -------------------------- 图表渲染 --------------------------
def render_metal_chart(start_datetime=None, end_datetime=None, metals=None, buy_info=None):
    if not start_datetime:
        start_datetime = datetime.now() - timedelta(days=7)
    if not end_datetime:
        end_datetime = datetime.now()
    if not metals or len(metals) == 0:
        metals = DEFAULT_METALS

    chart_data, latest_prices = get_hourly_metal_data(start_datetime, end_datetime, metals)
    if not chart_data:
        return html.Div(
            fac.AntdEmpty(
                description='暂无符合条件的小时级数据，请检查时间范围（国内期货仅交易日有数据）',
                style={'height': '700px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                       'fontSize': '16px'}
            ),
            key=f'empty-chart-{uuid.uuid4()}'
        ), latest_prices

    selected_colors = [COLOR_MAP[metal] for metal in metals if metal in COLOR_MAP]

    return html.Div(
        fact.AntdLine(
            data=chart_data,
            xField='datetime',
            yField='price',
            seriesField='metal',
            smooth=True,
            color=selected_colors,
            point={
                'shape': 'circle',
                'style': {'fill': 'white', 'strokeWidth': 2, 'r': 4}
            },
            label=False,
            xAxis=True,
            yAxis=True,
            legend=True,
            tooltip=True,
            height=700,
            style=style(width='100%', minWidth='1200px', padding=0, margin=0, marginBottom='40px'),
            autoFit=True,
            connectNulls=True
        ),
        key=f'metal-chart-{uuid.uuid4()}'
    ), latest_prices


# -------------------------- 盈亏表格渲染 --------------------------
def render_profit_table(buy_info, latest_prices):
    """生成盈亏分析表格"""
    if not buy_info or not latest_prices:
        return fac.AntdEmpty(
            description='请先选择买入信息并查询数据',
            style={'height': '200px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
        )

    table_data = []
    for metal in buy_info:
        buy_price = buy_info[metal]['price']
        grams = buy_info[metal]['grams']
        current_price = latest_prices.get(metal, 0)

        # 计算盈亏
        profit = (current_price - buy_price) * grams
        profit_str = f'+{profit:.2f}' if profit >= 0 else f'{profit:.2f}'
        profit_color = 'green' if profit >= 0 else 'red'

        table_data.append({
            'metal': NAME_MAP[metal],
            'buy_price': f'{buy_price:.4f}',
            'current_price': f'{current_price:.4f}',
            'grams': f'{grams:.2f}',
            'profit': profit_str,
            'profit_color': profit_color
        })

    return fac.AntdTable(
        columns=[
            {'title': '贵金属种类', 'dataIndex': 'metal', 'width': '15%'},
            {'title': '买入价格（元/克）', 'dataIndex': 'buy_price', 'width': '20%'},
            {'title': '当前价格（元/克）', 'dataIndex': 'current_price', 'width': '20%'},
            {'title': '买入克数', 'dataIndex': 'grams', 'width': '15%'},
            {
                'title': '盈亏金额（元）',
                'dataIndex': 'profit',
                'width': '30%',
                'render': 'profit_color'
            }
        ],
        data=table_data,
        bordered=True,
        style=style(width='100%', marginTop='20px')
    )


# -------------------------- 页面布局（新增买入信息输入） --------------------------
def render_content(menu_access: MenuAccess, **kwargs):
    if not menu_access.has_access('贵金属价格监控-基础权限'):
        return fac.AntdAlert(
            message='权限不足',
            description='您暂无访问该页面的权限，请联系管理员',
            type='error',
            showIcon=True,
            style=style(margin='20px')
        )

    card_title = html.Div(
        [
            fac.AntdIcon(icon='antd-gold'),
            fac.AntdText('贵金属小时级价格趋势图（元/克）', style=style(marginLeft='10px', fontSize='18px'))
        ],
        style=style(display='flex', alignItems='center')
    )

    default_end = datetime.now().replace(minute=0, second=0, microsecond=0)
    default_start = (default_end - timedelta(days=7)).replace(minute=0, second=0, microsecond=0)

    return fac.AntdSpace(
        [
            # 筛选栏
            fac.AntdCard(
                fac.AntdSpace(
                    [
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    [
                                        fac.AntdText('时间范围（精确到小时）：',
                                                     style=style(fontWeight='bold', marginRight='10px',
                                                                 fontSize='14px')),
                                        fac.AntdDateRangePicker(
                                            id='pm-time-range',
                                            placeholder=['开始时间', '结束时间'],
                                            showTime=True,
                                            format='YYYY-MM-DD HH:mm',
                                            value=[
                                                default_start.strftime('%Y-%m-%d %H:%M'),
                                                default_end.strftime('%Y-%m-%d %H:%M')
                                            ],
                                            style=style(width='450px', fontSize='14px')
                                        ),
                                    ],
                                    xs=24, sm=24, md=12, lg=12
                                ),
                                fac.AntdCol(
                                    [
                                        fac.AntdText('选择金属：', style=style(fontWeight='bold', marginRight='10px',
                                                                              fontSize='14px')),
                                        fac.AntdCheckboxGroup(
                                            id='pm-metal-select',
                                            options=METAL_OPTIONS,
                                            value=DEFAULT_METALS,
                                            style=style(display='inline-flex', gap='20px', fontSize='14px')
                                        )
                                    ],
                                    xs=24, sm=24, md=6, lg=6
                                ),
                                fac.AntdCol(
                                    [
                                        fac.AntdButton(
                                            '查询小时级数据',
                                            id='pm-query-btn',
                                            type='primary',
                                            style=style(marginLeft='10px', fontSize='14px', padding='8px 16px')
                                        ),
                                        fac.AntdButton(
                                            '重置',
                                            id='pm-reset-btn',
                                            style=style(marginLeft='10px', fontSize='14px', padding='8px 16px')
                                        )
                                    ],
                                    xs=24, sm=24, md=6, lg=6,
                                    style=style(textAlign='right')
                                )
                            ],
                            style=style(marginBottom='10px')
                        ),
                        fac.AntdAlert(
                            message='数据说明',
                            description='1. 数据为上海期货交易所主力合约1小时级K线收盘价，已统一转换为「元/克」；2. 仅国内期货交易日/交易时间有数据，非交易时间无数据；3. 鼠标悬浮折线可查看对应价格',
                            type='info',
                            showIcon=True,
                            style=style(marginTop='10px', fontSize='12px')
                        )
                    ],
                    direction='vertical',
                    style=style(width='100%', padding='10px')
                ),
                title='数据筛选（小时级精度）',
                style=style(width='100%', margin='0 10px 15px 10px', boxShadow='0 2px 8px rgba(0,0,0,0.1)')
            ),
            # 新增：买入信息输入卡片
            fac.AntdCard(
                fac.AntdSpace(
                    [
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    [
                                        fac.AntdText('选择买入贵金属：',
                                                     style=style(fontWeight='bold', marginRight='10px',
                                                                 fontSize='14px')),
                                        fac.AntdSelect(
                                            id='pm-buy-metal',
                                            options=METAL_OPTIONS,
                                            placeholder='请选择贵金属',
                                            style=style(width='200px', fontSize='14px')
                                        ),
                                    ],
                                    xs=24, sm=24, md=6, lg=6
                                ),
                                fac.AntdCol(
                                    [
                                        fac.AntdText('买入价格（元/克）：',
                                                     style=style(fontWeight='bold', marginRight='10px',
                                                                 fontSize='14px')),
                                        fac.AntdInputNumber(
                                            id='pm-buy-price',
                                            placeholder='请输入买入价格',
                                            min=0,
                                            precision=4,
                                            style=style(width='200px', fontSize='14px')
                                        ),
                                    ],
                                    xs=24, sm=24, md=6, lg=6
                                ),
                                fac.AntdCol(
                                    [
                                        fac.AntdText('买入克数：', style=style(fontWeight='bold', marginRight='10px',
                                                                              fontSize='14px')),
                                        fac.AntdInputNumber(
                                            id='pm-buy-grams',
                                            placeholder='请输入克数',
                                            min=0,
                                            precision=2,
                                            style=style(width='200px', fontSize='14px')
                                        ),
                                    ],
                                    xs=24, sm=24, md=6, lg=6
                                ),
                                fac.AntdCol(
                                    [
                                        fac.AntdButton(
                                            '添加买入记录',
                                            id='pm-add-buy-btn',
                                            type='primary',
                                            style=style(marginLeft='10px', fontSize='14px', padding='8px 16px')
                                        ),
                                        fac.AntdButton(
                                            '清空买入记录',
                                            id='pm-clear-buy-btn',
                                            style=style(marginLeft='10px', fontSize='14px', padding='8px 16px')
                                        )
                                    ],
                                    xs=24, sm=24, md=6, lg=6,
                                    style=style(textAlign='right')
                                )
                            ],
                            style=style(marginBottom='10px')
                        ),
                        # 买入记录展示
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    [
                                        fac.AntdText('已添加的买入记录：',
                                                     style=style(fontWeight='bold', fontSize='14px')),
                                        html.Div(id='pm-buy-records', style=style(marginTop='10px'))
                                    ],
                                    xs=24
                                )
                            ]
                        )
                    ],
                    direction='vertical',
                    style=style(width='100%', padding='10px')
                ),
                title='买入信息录入',
                style=style(width='100%', margin='0 10px 15px 10px', boxShadow='0 2px 8px rgba(0,0,0,0.1)')
            ),
            # 图表卡片
            Card(
                html.Div(
                    id='pm-chart-container',
                    children=get_initial_chart_tip(),
                    style=style(width='100%', overflow_x='auto')
                ),
                title=card_title,
                style=style(width='100%', height='800px', margin='0 10px', padding=0,
                            boxShadow='0 2px 12px rgba(0,0,0,0.15)')
            ),
            # 新增：盈亏分析表格卡片
            Card(
                html.Div(id='pm-profit-table'),
                title='盈亏分析（当前卖出）',
                style=style(width='100%', margin='0 10px', padding='20px', boxShadow='0 2px 12px rgba(0,0,0,0.15)')
            )
        ],
        direction='vertical',
        style=style(width='100%', padding='20px 0', margin=0)
    )


# -------------------------- 回调函数（新增买入记录和盈亏分析） --------------------------
# 回调1：管理买入记录
@callback(
    Output('pm-buy-records', 'children'),
    Output('pm-buy-metal', 'value'),
    Output('pm-buy-price', 'value'),
    Output('pm-buy-grams', 'value'),
    Input('pm-add-buy-btn', 'nClicks'),
    Input('pm-clear-buy-btn', 'nClicks'),
    State('pm-buy-metal', 'value'),
    State('pm-buy-price', 'value'),
    State('pm-buy-grams', 'value'),
    State('pm-buy-records', 'children'),
    prevent_initial_call=True
)
def manage_buy_records(add_clicks, clear_clicks, buy_metal, buy_price, buy_grams, current_records):
    add_clicks = add_clicks or 0
    clear_clicks = clear_clicks or 0

    try:
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''
        logger.info(f'买入记录回调触发源：{trigger_id}')
    except Exception as e:
        logger.error(f'买入记录触发源解析失败：{e}')
        return no_update, no_update, no_update, no_update

    # 清空记录
    if trigger_id == 'pm-clear-buy-btn':
        logger.info('清空买入记录')
        return html.Div(), None, None, None

    # 添加记录
    if trigger_id == 'pm-add-buy-btn' and add_clicks > 0:
        if not buy_metal or buy_price is None or buy_grams is None:
            MessageManager.warning(content='请完整填写买入信息（贵金属种类、价格、克数）')
            return no_update, no_update, no_update, no_update

        # 构造新记录
        new_record = fac.AntdTag(
            content=f'{NAME_MAP[buy_metal]} - 买入价：{buy_price:.4f}元/克 - {buy_grams:.2f}克',
            color=COLOR_MAP[buy_metal],
            style=style(marginRight='10px', marginBottom='10px', fontSize='13px')
        )

        # 合并现有记录
        if current_records:
            if isinstance(current_records, list):
                new_children = current_records + [new_record]
            else:
                new_children = [current_records, new_record]
        else:
            new_children = [new_record]

        logger.info(f'添加买入记录：{NAME_MAP[buy_metal]} - {buy_price:.4f}元/克 - {buy_grams:.2f}克')
        return new_children, None, None, None

    return no_update, no_update, no_update, no_update


# 回调2：主查询回调（新增盈亏表格输出）
@callback(
    Output('pm-chart-container', 'children'),
    Output('pm-query-btn', 'loading'),
    Output('pm-time-range', 'value'),
    Output('pm-metal-select', 'value'),
    Output('pm-profit-table', 'children'),
    Input('pm-query-btn', 'nClicks'),
    Input('pm-reset-btn', 'nClicks'),
    State('pm-time-range', 'value'),
    State('pm-metal-select', 'value'),
    State('pm-buy-records', 'children'),
    prevent_initial_call=True
)
def handle_pm_actions(query_clicks, reset_clicks, time_range, metals, buy_records):
    query_clicks = query_clicks or 0
    reset_clicks = reset_clicks or 0

    try:
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''
        logger.info(f'主回调触发源：{trigger_id}，query_clicks={query_clicks}，reset_clicks={reset_clicks}')
    except Exception as e:
        logger.error(f'主回调触发源解析失败：{e}')
        return no_update, False, no_update, no_update, no_update

    # 重置操作
    if trigger_id == 'pm-reset-btn':
        logger.info('执行重置操作')
        default_end = datetime.now().replace(minute=0, second=0, microsecond=0)
        default_start = (default_end - timedelta(days=7)).replace(minute=0, second=0, microsecond=0)
        return (
            get_initial_chart_tip(),
            False,
            [default_start.strftime('%Y-%m-%d %H:%M'), default_end.strftime('%Y-%m-%d %H:%M')],
            DEFAULT_METALS,
            html.Div()
        )

    # 查询操作
    if trigger_id == 'pm-query-btn' and query_clicks > 0:
        logger.info(f'执行小时级数据查询，点击次数：{query_clicks}')

        start_datetime = datetime.now() - timedelta(days=7)
        end_datetime = datetime.now()

        if time_range and len(time_range) == 2:
            try:
                if time_range[0] and time_range[1]:
                    start_datetime = datetime.strptime(time_range[0], '%Y-%m-%d %H:%M')
                    end_datetime = datetime.strptime(time_range[1], '%Y-%m-%d %H:%M')
            except ValueError:
                try:
                    if time_range[0] and time_range[1]:
                        start_datetime = datetime.strptime(time_range[0], '%Y-%m-%d')
                        end_datetime = datetime.strptime(time_range[1], '%Y-%m-%d')
                except Exception as e:
                    logger.warning(f'时间格式解析失败：{e}，使用默认时间范围')
                    MessageManager.warning(content='时间格式解析失败，将使用最近7天数据')

        # 解析买入记录（简化处理，实际项目可使用dcc.Store存储）
        buy_info = {}
        # 注意：这里简化处理，实际项目建议用dcc.Store存储买入信息
        # 本版本仅展示功能框架，完整的买入信息存储需额外实现

        chart_component, latest_prices = render_metal_chart(start_datetime, end_datetime, metals, buy_info)
        profit_table = render_profit_table(buy_info, latest_prices)

        return (
            chart_component,
            False,
            no_update,
            no_update,
            profit_table
        )

    return no_update, False, no_update, no_update, no_update