from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash import html, dash
from dash_components import Card
import dash_callback.application.message_.announcement_c  # noqa: F401
from i18n import t__notification, translator
import pandas as pd
import random
from datetime import date
from dash import Input, Output, State, callback


# 二级菜单的标题、图标和显示顺序
title = '员工花名册'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('员工花名册-页面',)


# ---------------------- 模拟数据 ----------------------
def get_employee_data():
    return pd.DataFrame([
        {
            "员工姓名": "高俊", "出生日期": "1970-05-10", "参加工作日期": "1994-10-01",
             "手机号码": "13800138001", "民族": "汉族",
            "性别": "男", "预计退休年龄": 60, "籍贯": "云南省昆明市", "出生地": "云南省昆明市",
            "岗位": "生产厂领导", "政治面貌": "中共党员", "加入该政治面貌时间": "1992-07-01"
        },
        {
            "员工姓名": "李成冬", "出生日期": "1985-08-15", "参加工作日期": "2007-12-01",
             "手机号码": "13800138002", "民族": "汉族",
            "性别": "男", "预计退休年龄": 60, "籍贯": "云南省曲靖市", "出生地": "云南省曲靖市",
            "岗位": "制丝车间", "政治面貌": "中共党员", "加入该政治面貌时间": "2005-10-01"
        },
        {
            "员工姓名": "胡婕", "出生日期": "1995-03-20", "参加工作日期": "2025-07-13",
             "手机号码": "13800138003", "民族": "彝族",
            "性别": "女", "预计退休年龄": 55, "籍贯": "云南省大理市", "出生地": "云南省昆明市",
            "岗位": "滤棒成型车间", "政治面貌": "共青团员", "加入该政治面貌时间": "2012-05-04"
        }
    ])

df_employee = get_employee_data()

# ---------------------- 核心渲染 ----------------------
def render_content(menu_access: MenuAccess, **kwargs):
    if not menu_access.has_access('员工花名册-页面'):
        return fac.AntdResult(status='403', title='无权限', subTitle='请联系管理员')

    return fac.AntdFlex(
        [
            # 搜索框
            fac.AntdRow(
                [fac.AntdCol(
                    fac.AntdInput(
                        id='emp-search-input',
                        placeholder='姓名/政治面貌/手机号',
                        allowClear=True,
                        style={'width': '100%'}
                    ), span=8, offset=8
                )],
                gutter=16, style={'marginBottom': 20}
            ),

            # 表格（0.3.15 严格兼容写法）
            fac.AntdTable(
                id='emp-info-table',
                columns=[
                    {'title': col, 'dataIndex': col, 'key': col, 'align': 'center'}
                    for col in df_employee.columns
                ] + [
                    {
                        'title': '操作', 'dataIndex': 'operation', 'key': 'operation',
                        'align': 'center', 'renderOptions': {'renderType': 'button'}, 'width': 120
                    }
                ],
                data=format_table_data(df_employee.to_dict('records')),
                bordered=True,
                style={'width': '100%'}
            ),

            # 详情弹窗
            fac.AntdModal(
                id='emp-detail-modal', title='员工详情', width=700, maskClosable=False,
                children=[fac.AntdDescriptions(id='emp-detail-descriptions', bordered=True, column=2, layout='vertical')]
            )
        ],
        vertical=True, style={'width': '100%', 'padding': 20}
    )

# ---------------------- 辅助函数 ----------------------
def format_table_data(data):
    for idx, row in enumerate(data):
        row['key'] = str(idx)
        row['operation'] = [{'title': '查看详情', 'type': 'link', 'action': 'custom', 'customEvent': f'view_detail_{idx}'}]
    return data

# ---------------------- 回调 ----------------------
@callback(Output('emp-info-table', 'data'), Input('emp-search-input', 'value'))
def filter_emp(search_val):
    if not search_val:
        return format_table_data(df_employee.to_dict('records'))
    mask = df_employee['员工姓名'].str.contains(search_val, na=False) | \
           df_employee['手机号码'].str.contains(search_val, na=False) | \
           df_employee['政治面貌'].str.contains(search_val, na=False)
    return format_table_data(df_employee[mask].to_dict('records'))

@callback(
    [Output('emp-detail-modal', 'visible'), Output('emp-detail-descriptions', 'items')],
    [Input('emp-info-table', 'nClicksButton')],
    [State('emp-info-table', 'data')],
    prevent_initial_call=True
)
def show_detail(n_clicks, data):
    if not n_clicks: return False, []
    row = data[int(n_clicks['customEvent'].split('_')[-1])]
    return True, [{'label': k, 'children': v} for k, v in row.items() if k not in ('key', 'operation')]