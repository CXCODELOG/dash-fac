from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html, Input, Output, State, callback
from dash_components import Card
import dash_callback.application.message_.announcement_c  # noqa: F401
from i18n import t__notification, translator
import pandas as pd
import random
from datetime import date

# 二级菜单的标题、图标和显示顺序
title = '紧急联系人'
icon = None
logger = Log.get_logger(__name__)
order = 8
access_metas = ('紧急联系人-页面',)


# ---------------------- 模拟数据 ----------------------
def get_employee_data():
    return pd.DataFrame([
        {
            "厂编号": "001155", "员工姓名": "胡婕", "出生日期": "1995-03-20", "参加工作日期": "2025-07-13",
            "手机号码": "13800138003", "民族": "彝族",
            "性别": "女", "预计退休年龄": 55, "籍贯": "云南省大理市", "出生地": "云南省昆明市",
            "岗位": "滤棒成型车间", "政治面貌": "共青团员", "加入该政治面貌时间": "2012-05-04"
        }
    ])


df_employee = get_employee_data()


# ---------------------- 核心渲染 ----------------------
def render_content(menu_access: MenuAccess, **kwargs):
    if not menu_access.has_access('紧急联系人-页面'):
        return fac.AntdResult(status='403', title='无权限', subTitle='请联系管理员')

    return fac.AntdFlex(
        [
            # 搜索框
            fac.AntdRow(
                [fac.AntdCol(
                    fac.AntdInput(
                        id='eme-search-input',
                        placeholder='姓名/政治面貌/手机号',
                        allowClear=True,
                        style={'width': '100%'}
                    ), span=8, offset=8
                )],
                gutter=16, style={'marginBottom': 20}
            ),

            # 表格（0.4.5 兼容写法）
            fac.AntdTable(
                id='eme-info-table',
                columns=[
                            {'title': col, 'dataIndex': col, 'key': col, 'align': 'center'}
                            for col in df_employee.columns
                        ] + [
                            {
                                'title': '操作',
                                'dataIndex': 'operation',
                                'key': 'operation',
                                'align': 'center',
                                'renderOptions': {'renderType': 'button'},
                                'width': 120
                            }
                        ],
                data=format_table_data(df_employee.to_dict('records')),
                pagination=True,
                bordered=True,
                style={'width': '100%'}
            ),

            # 详情弹窗
            fac.AntdModal(
                id='eme-detail-modal', title='员工详情', width=700, maskClosable=False,
                children=[
                    fac.AntdDescriptions(id='eme-detail-descriptions', bordered=True, column=2, layout='vertical')]
            )
        ],
        vertical=True, style={'width': '100%', 'padding': 20}
    )


# ---------------------- 辅助函数 ----------------------
def format_table_data(data):
    for idx, row in enumerate(data):
        row['key'] = str(idx)
        row['operation'] = [{'title': '查看详情', 'type': 'link'}]  # 简化按钮配置
    return data


# ---------------------- 回调 ----------------------
@callback(Output('eme-info-table', 'data'), Input('eme-search-input', 'value'))
def filter_emp(search_val):
    if not search_val:
        return format_table_data(df_employee.to_dict('records'))
    mask = df_employee['员工姓名'].str.contains(search_val, na=False) | \
           df_employee['手机号码'].str.contains(search_val, na=False) | \
           df_employee['政治面貌'].str.contains(search_val, na=False)
    return format_table_data(df_employee[mask].to_dict('records'))


@callback(
    [Output('eme-detail-modal', 'visible'), Output('eme-detail-descriptions', 'items')],
    [Input('eme-info-table', 'nClicksButton'), Input('eme-info-table', 'recentlyButtonClickedRow')],
    # 修复：用recentlyButtonClickedRow获取行数据
    prevent_initial_call=True
)
def show_detail(n_clicks, clicked_row):
    # 修复：仅判断n_clicks是否有点击，clicked_row直接提供行数据
    if not n_clicks or not clicked_row:
        return False, []

    try:
        # 直接使用clicked_row构造详情项
        items = [{'label': k, 'children': v} for k, v in clicked_row.items() if k not in ('key', 'operation')]
        return True, items
    except (Exception,):
        logger.error('获取员工详情失败', exc_info=True)
        return False, []