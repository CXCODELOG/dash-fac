from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card, MessageManager
from datetime import datetime, timedelta
from feffery_dash_utils.style_utils import style
import feffery_antd_charts as fact
from dash import html, dcc, Input, Output, callback, callback_context, State, no_update
import uuid
import akshare as ak

# 二级菜单配置
title = '贵金属价格监控'
icon = 'antd-gold'
order = 4
logger = Log.get_logger(__name__)

# 权限元数据
access_metas = (
    '贵金属价格监控-基础权限',
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
METAL_TICKER_MAP = {'XAU': 'AU0', 'XPT': 'pt0', 'XAG': 'AG0'}
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
    """获取小时级贵金属数据，返回图表数据+最新价格"""
    if not start_datetime:
        start_datetime = datetime.now() - timedelta(days=7)
    if not end_datetime:
        end_datetime = datetime.now()
    logger.info(f'获取小时级数据：时间范围[{start_datetime}~{end_datetime}]，金属{metals}')
    all_data = []
    latest_prices = {}
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
            if 'datetime' not in df.columns or 'close' not in df.columns:
                logger.warning(f'{NAME_MAP[metal]}数据缺少必要列')
                continue
            df = df.dropna(subset=['datetime', 'close']).copy()
            if df.empty:
                logger.warning(f'{NAME_MAP[metal]}清洗后无有效数据')
                continue
            df['datetime'] = pd.to_datetime(df['datetime'], errors='coerce')
            df = df.dropna(subset=['datetime']).copy()
            mask = (df['datetime'] >= start_datetime) & (df['datetime'] <= end_datetime)
            df_filtered = df.loc[mask].copy()
            if df_filtered.empty:
                logger.warning(f'{NAME_MAP[metal]}在指定时间范围无数据')
                MessageManager.warning(
                    content=f'{NAME_MAP[metal]}暂无{start_datetime.strftime("%Y-%m-%d %H:%M")}~{end_datetime.strftime("%Y-%m-%d %H:%M")}的小时级数据')
                continue
            # 修正后：单位转换逻辑（仅白银需÷1000，黄金、铂金原生为元/克）
            latest_row = df_filtered.iloc[-1]
            latest_close = latest_row['close']
            if metal == 'XAG':
                latest_prices[metal] = round(latest_close / 1000, 4)
            else:  # XAU、XPT均为元/克，无需转换
                latest_prices[metal] = round(latest_close, 4)

            # 修正后：图表数据单位转换
            for _, row in df_filtered.iterrows():
                time_str = row['datetime'].strftime('%Y-%m-%d %H:%M')
                close_price = row['close']
                if metal == 'XAG':
                    price_cny_per_gram = round(close_price / 1000, 4)
                else:  # XAU、XPT均为元/克，无需转换
                    price_cny_per_gram = round(close_price, 4)
                all_data.append({
                    'datetime': time_str,
                    'metal': NAME_MAP[metal],
                    'price': price_cny_per_gram
                })
        except Exception as e:
            logger.error(f'获取{NAME_MAP[metal]}数据失败：{e}', exc_info=True)
            MessageManager.error(content=f'获取{NAME_MAP[metal]}小时级数据失败：{str(e)}')
            continue
    all_data.sort(key=lambda x: x['datetime'])
    logger.info(f'获取到{len(all_data)}条有效数据，最新价格：{latest_prices}')
    return all_data, latest_prices


# -------------------------- 图表渲染（简化版，兼容旧版本） --------------------------
def render_metal_chart(start_datetime=None, end_datetime=None, metals=None):
    if not start_datetime:
        start_datetime = datetime.now() - timedelta(days=7)
    if not end_datetime:
        end_datetime = datetime.now()
    if not metals or len(metals) == 0:
        metals = DEFAULT_METALS

    raw_data, latest_prices = get_hourly_metal_data(start_datetime, end_datetime, metals)
    if not raw_data:
        return html.Div(
            fac.AntdEmpty(
                description='暂无符合条件的小时级数据，请检查时间范围',
                style={'height': '700px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
            ),
            key=f'empty-chart-{uuid.uuid4()}'
        ), latest_prices

    # 核心修复：yField仅用字符串，去掉所有复杂配置
    selected_colors = [COLOR_MAP[metal] for metal in metals if metal in COLOR_MAP]
    return html.Div(
        fact.AntdLine(
            data=raw_data,
            xField='datetime',
            yField='price',  # 仅字符串，兼容旧版本
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


# -------------------------- 盈亏表格渲染（简化版） --------------------------
def render_profit_table(buy_info, latest_prices):
    if not buy_info or len(buy_info) == 0 or not latest_prices:
        return fac.AntdEmpty(
            description='请先添加买入记录并查询数据',
            style={'height': '200px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'}
        )

    table_data = []
    total_profit = 0
    for item in buy_info:
        metal = item['metal']
        buy_price = item['price']
        grams = item['grams']
        current_price = latest_prices.get(metal, 0)

        profit = (current_price - buy_price) * grams
        total_profit += profit
        profit_rate = (current_price - buy_price) / buy_price * 100 if buy_price > 0 else 0

        table_data.append({
            'key': str(uuid.uuid4()),
            'metal': NAME_MAP[metal],
            'buy_price': f'{buy_price:.4f}',
            'current_price': f'{current_price:.4f}',
            'grams': f'{grams:.2f}',
            'profit_rate': f'{profit_rate:+.2f}%',
            'profit': f'{profit:+.2f}'
        })

    # 合计行
    table_data.append({
        'key': 'total',
        'metal': '合计',
        'buy_price': '-',
        'current_price': '-',
        'grams': '-',
        'profit_rate': '-',
        'profit': f'{total_profit:+.2f}'
    })

    return fac.AntdTable(
        columns=[
            {'title': '贵金属种类', 'dataIndex': 'metal', 'width': '15%'},
            {'title': '买入价格（元/克）', 'dataIndex': 'buy_price', 'width': '20%'},
            {'title': '当前价格（元/克）', 'dataIndex': 'current_price', 'width': '20%'},
            {'title': '买入克数', 'dataIndex': 'grams', 'width': '15%'},
            {'title': '涨跌幅', 'dataIndex': 'profit_rate', 'width': '15%'},
            {'title': '盈亏金额（元）', 'dataIndex': 'profit', 'width': '15%'}
        ],
        data=table_data,
        bordered=True,
        pagination=False,
        style=style(width='100%')
    )


# -------------------------- 页面布局 --------------------------
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
            dcc.Store(id='pm-buy-info-store', data=[], storage_type='memory'),
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
                            description='1. 数据为上海期货交易所主力合约1小时级收盘价，已统一转换为「元/克」；2. 仅交易日/交易时间有数据；3. 添加买入记录后，可在下方表格查看盈亏情况',
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
            # 买入信息录入卡片
            fac.AntdCard(
                fac.AntdSpace(
                    [
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    [
                                        fac.AntdText('买入贵金属：', style=style(fontWeight='bold', marginRight='10px',
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
                                            min=0.0001,
                                            step=0.0001,
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
                                            min=0.01,
                                            step=0.01,
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
                                            danger=True,
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
                                        html.Div(id='pm-buy-records', style=style(marginTop='10px', minHeight='40px'))
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
            # 盈亏分析表格卡片
            Card(
                html.Div(id='pm-profit-table'),
                title='盈亏分析（当前卖出）',
                style=style(width='100%', margin='0 10px', padding='20px', boxShadow='0 2px 12px rgba(0,0,0,0.15)')
            )
        ],
        direction='vertical',
        style=style(width='100%', padding='20px 0', margin=0)
    )


# -------------------------- 回调1：买入记录管理 --------------------------
@callback(
    Output('pm-buy-info-store', 'data'),
    Output('pm-buy-records', 'children'),
    Output('pm-buy-metal', 'value'),
    Output('pm-buy-price', 'value'),
    Output('pm-buy-grams', 'value'),
    Input('pm-add-buy-btn', 'nClicks'),
    Input('pm-clear-buy-btn', 'nClicks'),
    State('pm-buy-metal', 'value'),
    State('pm-buy-price', 'value'),
    State('pm-buy-grams', 'value'),
    State('pm-buy-info-store', 'data'),
    prevent_initial_call=True
)
def manage_buy_records(add_clicks, clear_clicks, buy_metal, buy_price, buy_grams, current_data):
    add_clicks = add_clicks or 0
    clear_clicks = clear_clicks or 0
    current_data = current_data or []

    try:
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''
        logger.info(f'买入记录回调触发源：{trigger_id}')
    except Exception as e:
        logger.error(f'买入记录回调失败：{e}')
        return no_update, no_update, no_update, no_update, no_update

    # 清空记录
    if trigger_id == 'pm-clear-buy-btn':
        logger.info('清空所有买入记录')
        return [], html.Div(), None, None, None

    # 添加记录
    if trigger_id == 'pm-add-buy-btn' and add_clicks > 0:
        if not buy_metal:
            MessageManager.warning(content='请选择买入的贵金属种类')
            return no_update, no_update, no_update, no_update, no_update
        if buy_price is None or buy_price <= 0:
            MessageManager.warning(content='请输入有效的买入价格')
            return no_update, no_update, no_update, no_update, no_update
        if buy_grams is None or buy_grams <= 0:
            MessageManager.warning(content='请输入有效的买入克数')
            return no_update, no_update, no_update, no_update, no_update

        new_record = {
            'metal': buy_metal,
            'price': buy_price,
            'grams': buy_grams,
            'record_id': str(uuid.uuid4())
        }
        new_data = current_data + [new_record]
        logger.info(f'添加买入记录：{new_record}')

        # 生成标签列表
        new_tags = []
        for item in new_data:
            new_tags.append(
                fac.AntdTag(
                    content=f'{NAME_MAP[item["metal"]]} | 买入价：{item["price"]:.4f}元/克 | {item["grams"]:.2f}克',
                    color=COLOR_MAP[item["metal"]],
                    style=style(marginRight='10px', marginBottom='10px', fontSize='13px')
                )
            )

        MessageManager.success(content='买入记录添加成功')
        return new_data, new_tags, None, None, None

    return no_update, no_update, no_update, no_update, no_update


# -------------------------- 回调2：主查询回调 --------------------------
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
    State('pm-buy-info-store', 'data'),
    prevent_initial_call=True
)
def handle_pm_actions(query_clicks, reset_clicks, time_range, metals, buy_info):
    query_clicks = query_clicks or 0
    reset_clicks = reset_clicks or 0
    buy_info = buy_info or []

    try:
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''
        logger.info(f'主回调触发源：{trigger_id}')
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
        logger.info(f'执行数据查询，买入记录：{buy_info}')
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
                    logger.warning(f'时间格式解析失败：{e}')
                    MessageManager.warning(content='时间格式解析失败，将使用最近7天数据')

        chart_component, latest_prices = render_metal_chart(start_datetime, end_datetime, metals)
        profit_table = render_profit_table(buy_info, latest_prices)

        return (
            chart_component,
            False,
            no_update,
            no_update,
            profit_table
        )

    return no_update, False, no_update, no_update, no_update