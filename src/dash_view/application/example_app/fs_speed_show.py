from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash_components import Card, MessageManager
from datetime import datetime
from feffery_dash_utils.style_utils import style
import feffery_antd_charts as fact
from dash import html, Input, Output, callback, callback_context, State, no_update
import pyodbc
import uuid  # 保留唯一key，强制图表刷新

# 二级菜单的标题、图标和显示顺序
title = '发射速度展示'
icon = 'antd-line-chart'
order = 3
logger = Log.get_logger(__name__)

# 权限元数据
access_metas = (
    '发射速度展示-基础权限',
)

# SQL Server 连接配置
SQL_SERVER_CONFIG = {
    'SERVER': '10.97.65.197',
    'DATABASE': 'bigdata',
    'USER': 'sa',
    'PASSWORD': 'CXdata@197',
    'DRIVER': '{SQL Server Native Client 11.0}'
}

# 发射管选项（供多选框使用）
TUBE_OPTIONS = [
    {'label': f'发射管{i}', 'value': str(i)} for i in range(1, 11)
]
# 默认选中所有发射管
DEFAULT_SELECTED_TUBES = [str(i) for i in range(1, 11)]


# 初始页面提示（带唯一key）
def get_initial_chart_tip():
    """生成初始提示，每次刷新唯一key"""
    return html.Div(
        fac.AntdEmpty(
            description='请选择筛选条件后，点击「查询」按钮查看数据',
            style={'height': '800px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                   'fontSize': '16px'}
        ),
        key=f'initial-tip-{uuid.uuid4()}'
    )


# 原生pyodbc读取数据
def get_fs_speed_data(start_time=None, end_time=None, tube_list=None):
    """读取发射速度数据"""
    if not tube_list or len(tube_list) == 0:
        tube_list = DEFAULT_SELECTED_TUBES

    logger.info(f'数据查询参数：时间范围[{start_time} ~ {end_time}]，选中发射管{tube_list}')

    chart_data = []
    conn = None
    cursor = None
    try:
        conn_str = (
            f"DRIVER={SQL_SERVER_CONFIG['DRIVER']};"
            f"SERVER={SQL_SERVER_CONFIG['SERVER']};"
            f"DATABASE={SQL_SERVER_CONFIG['DATABASE']};"
            f"UID={SQL_SERVER_CONFIG['USER']};"
            f"PWD={SQL_SERVER_CONFIG['PASSWORD']};"
        )
        conn = pyodbc.connect(conn_str, autocommit=True)
        cursor = conn.cursor()

        sql_base = """
            SELECT id, speed_1, speed_2, speed_3, speed_4, speed_5,
                   speed_6, speed_7, speed_8, speed_9, speed_10, time
            FROM dbo.CX_fs_speed
        """
        sql_conditions = []
        sql_params = []

        if start_time and end_time:
            sql_conditions.append("time BETWEEN ? AND ?")
            sql_params.extend([start_time, end_time])
        elif start_time:
            sql_conditions.append("time >= ?")
            sql_params.append(start_time)
        elif end_time:
            sql_conditions.append("time <= ?")
            sql_params.append(end_time)

        if sql_conditions:
            sql = f"{sql_base} WHERE {' AND '.join(sql_conditions)} ORDER BY time ASC"
        else:
            sql = f"{sql_base} ORDER BY time ASC"

        cursor.execute(sql, sql_params)
        columns = [col[0] for col in cursor.description]
        raw_data = cursor.fetchall()
        logger.info(f'查询到原始数据行数：{len(raw_data)}')

        for row in raw_data:
            row_dict = dict(zip(columns, row))
            time_str = row_dict['time'].strftime('%Y-%m-%d %H:%M:%S')

            for tube_num in tube_list:
                speed_key = f'speed_{tube_num}'
                if speed_key in row_dict:
                    chart_data.append({
                        'time': time_str,
                        'tube': f'发射管{tube_num}',
                        'speed': row_dict[speed_key] or 0
                    })

        logger.info(f'格式化后图表数据行数：{len(chart_data)}')

    except Exception as e:
        logger.error(f'读取发射速度数据失败: {e}', exc_info=True)
        MessageManager.error(content=f'数据加载失败：{str(e)}')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

    return chart_data


# 渲染折线图（带唯一key）
def render_fs_speed_chart(start_time=None, end_time=None, tube_list=None):
    """生成带唯一key的折线图，强制刷新"""
    chart_data = get_fs_speed_data(start_time, end_time, tube_list)

    if not chart_data:
        return html.Div(
            fac.AntdEmpty(
                description='暂无符合条件的发射速度数据',
                style={'height': '800px', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center',
                       'fontSize': '16px'}
            ),
            key=f'empty-chart-{uuid.uuid4()}'
        )

    color_map = {
        f'发射管{i}': [
            '#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1',
            '#13c2c2', '#eb2f96', '#f7ba1e', '#91d5ff', '#b7eb8f'
        ][i - 1] for i in range(1, 11)
    }
    selected_colors = [color_map[f'发射管{num}'] for num in (tube_list or DEFAULT_SELECTED_TUBES) if
                       f'发射管{num}' in color_map]

    return html.Div(
        fact.AntdLine(
            data=chart_data,
            xField='time',
            yField='speed',
            seriesField='tube',
            smooth=True,
            color=selected_colors,
            point={
                'shape': 'circle',
                'style': {
                    'fill': 'white',
                    'strokeWidth': 2.5,
                    'r': 4
                }
            },
            label=True,
            xAxis=True,
            yAxis=True,
            legend=True,
            tooltip=True,
            height=800,
            style=style(
                width='100%',
                minWidth='1200px',
                padding=0,
                margin=0,
                marginBottom='50px'
            ),
            autoFit=True,
            connectNulls=True
        ),
        key=f'line-chart-{uuid.uuid4()}'
    )


# 子应用核心渲染函数
def render_content(menu_access: MenuAccess, **kwargs):
    """渲染发射速度展示页面"""
    if not menu_access.has_access('发射速度展示-基础权限'):
        return fac.AntdAlert(
            message='权限不足',
            description='您暂无访问该页面的权限，请联系管理员',
            type='error',
            showIcon=True,
            style=style(margin='20px')
        )

    card_title = html.Div(
        [
            fac.AntdIcon(icon='antd-line-chart'),
            fac.AntdText('发射速度趋势图', style=style(marginLeft='10px', fontSize='18px'))
        ],
        style=style(display='flex', alignItems='center')
    )

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
                                        fac.AntdText('时间范围：', style=style(fontWeight='bold', marginRight='10px',
                                                                              fontSize='14px')),
                                        fac.AntdDateRangePicker(
                                            id='fs-speed-time-range',
                                            placeholder=['开始时间', '结束时间'],
                                            showTime=True,
                                            style=style(width='400px', fontSize='14px')
                                        ),
                                    ],
                                    xs=24, sm=24, md=10, lg=10
                                ),
                                fac.AntdCol(
                                    [
                                        fac.AntdButton(
                                            '查询',
                                            id='fs-speed-query-btn',
                                            type='primary',
                                            style=style(marginLeft='10px', fontSize='14px', padding='8px 16px'),
                                            # 新增：按钮loading样式优化
                                            loading_state={'is_loading': False}
                                        ),
                                        fac.AntdButton(
                                            '重置',
                                            id='fs-speed-reset-btn',
                                            style=style(marginLeft='10px', fontSize='14px', padding='8px 16px')
                                        )
                                    ],
                                    xs=24, sm=24, md=14, lg=14,
                                    style=style(textAlign='right')
                                )
                            ],
                            style=style(marginBottom='10px')
                        ),
                        fac.AntdRow(
                            [
                                fac.AntdCol(
                                    [
                                        fac.AntdText('选择发射管：', style=style(fontWeight='bold', marginRight='10px',
                                                                                fontSize='14px')),
                                        fac.AntdCheckboxGroup(
                                            id='fs-speed-tube-select',
                                            options=TUBE_OPTIONS,
                                            value=DEFAULT_SELECTED_TUBES,
                                            style=style(width='100%', display='flex', flexWrap='wrap', gap='20px',
                                                        fontSize='14px')
                                        )
                                    ],
                                    xs=24
                                )
                            ]
                        )
                    ],
                    direction='vertical',
                    style=style(width='100%', padding='10px')
                ),
                title='数据筛选',
                style=style(width='100%', margin='0 10px 15px 10px', boxShadow='0 2px 8px rgba(0,0,0,0.1)')
            ),
            # 图表卡片
            Card(
                html.Div(
                    id='fs-speed-chart-container',
                    children=get_initial_chart_tip(),
                    style=style(width='100%', overflow_x='auto')
                ),
                title=card_title,
                style=style(
                    width='100%',
                    height='900px',
                    margin='0 10px',
                    padding=0,
                    boxShadow='0 2px 12px rgba(0,0,0,0.15)'
                )
            )
        ],
        direction='vertical',
        style=style(width='100%', padding='20px 0', margin=0)
    )


# 核心修复：移除yield，确保返回tuple类型，解决重置报错
@callback(
    Output('fs-speed-chart-container', 'children'),
    Output('fs-speed-query-btn', 'loading'),
    Output('fs-speed-time-range', 'value'),
    Output('fs-speed-tube-select', 'value'),
    Input('fs-speed-query-btn', 'nClicks'),
    Input('fs-speed-reset-btn', 'nClicks'),
    State('fs-speed-time-range', 'value'),
    State('fs-speed-tube-select', 'value'),
    prevent_initial_call=True
)
def handle_fs_speed_actions(query_clicks, reset_clicks, time_range, tube_list):
    """
    统一处理查询/重置操作，仅返回tuple类型，解决Schema验证错误
    """
    # 1. 获取触发源（容错处理）
    try:
        ctx = callback_context
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0] if ctx.triggered else ''
        logger.info(f'回调触发源：{trigger_id}')
    except Exception as e:
        logger.error(f'触发源解析失败: {e}')
        # 所有分支必须返回tuple，这里返回no_update的tuple
        return (no_update, False, no_update, no_update)

    # 2. 处理重置操作（核心：返回tuple类型）
    if trigger_id == 'fs-speed-reset-btn':
        logger.info('执行重置操作')
        return (
            get_initial_chart_tip(),  # 初始提示
            False,  # 关闭loading
            None,  # 清空时间范围
            DEFAULT_SELECTED_TUBES  # 恢复全选发射管
        )

    # 3. 处理查询操作（移除yield，同步处理loading）
    if trigger_id == 'fs-speed-query-btn' and query_clicks > 0:
        logger.info(f'执行查询操作，点击次数：{query_clicks}')

        # 解析时间范围
        start_time = None
        end_time = None
        if time_range and len(time_range) == 2:
            try:
                start_time = datetime.strptime(time_range[0], '%Y-%m-%d %H:%M:%S')
                end_time = datetime.strptime(time_range[1], '%Y-%m-%d %H:%M:%S')
            except ValueError:
                start_time = datetime.strptime(time_range[0], '%Y-%m-%d')
                end_time = datetime.strptime(time_range[1], '%Y-%m-%d')
            except Exception as e:
                logger.warning(f'时间格式解析失败: {e}')
                MessageManager.warning(content='时间格式解析失败，将展示全部时间数据')

        # 同步返回：图表刷新 + loading关闭 + 筛选条件不更新
        return (
            render_fs_speed_chart(start_time, end_time, tube_list),
            False,  # loading直接关闭（同步逻辑下无法分步，不影响核心功能）
            no_update,
            no_update
        )

    # 4. 其他场景：返回tuple类型的no_update
    return (no_update, False, no_update, no_update)