from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
from common.utilities.util_logger import Log
from dash import Input, Output, callback
from database.sql_db.dao import dao_talent


# 二级菜单的标题、图标和显示顺序
title = '员工花名册'
icon = None
logger = Log.get_logger(__name__)
order = 1
access_metas = ('员工花名册-页面',)

DEPT_ID = '1704945130517040384'
EMPLOYEE_TABLE_COLUMNS = [
    {'title': '姓名', 'dataIndex': '姓名', 'key': '姓名', 'align': 'center'},
    {'title': '手机号', 'dataIndex': '手机号', 'key': '手机号', 'align': 'center'},
    {'title': '工号', 'dataIndex': '工号', 'key': '工号', 'align': 'center'},
]


def get_employee_data(search_val=None):
    sql = """
        SELECT
            u.`name` AS `姓名`,
            u.`mobile` AS `手机号`,
            u.`code_num2` AS `工号`
        FROM `v_xjr_user` u
        WHERE u.`id` IN (
            SELECT r.`user_id`
            FROM `v_xjr_user_dept_relation` r
            WHERE r.`dept_id` = %s
        )
    """
    params = [DEPT_ID]

    if search_val:
        sql += """
            AND (
                u.`name` LIKE %s
                OR u.`mobile` LIKE %s
                OR u.`code_num2` LIKE %s
            )
        """
        keyword = f'%{search_val}%'
        params.extend([keyword, keyword, keyword])

    sql += ' ORDER BY u.`name`'

    try:
        return dao_talent.select_all(sql, params)
    except Exception:
        logger.error('获取员工花名册数据失败', exc_info=True)
        return []


def format_table_data(data):
    for idx, row in enumerate(data):
        row['key'] = str(idx)
    return data


def render_content(menu_access: MenuAccess, **kwargs):
    if not menu_access.has_access('员工花名册-页面'):
        return fac.AntdResult(status='403', title='无权限', subTitle='请联系管理员')

    return fac.AntdFlex(
        [
            fac.AntdRow(
                [
                    fac.AntdCol(
                        fac.AntdInput(
                            id='emp-search-input',
                            placeholder='姓名/手机号/工号',
                            allowClear=True,
                            style={'width': '100%'},
                        ),
                        span=8,
                        offset=8,
                    )
                ],
                gutter=16,
                style={'marginBottom': 20},
            ),
            fac.AntdTable(
                id='emp-info-table',
                columns=EMPLOYEE_TABLE_COLUMNS,
                data=format_table_data(get_employee_data()),
                pagination=True,
                bordered=True,
                style={'width': '100%'},
            ),
        ],
        vertical=True,
        style={'width': '100%', 'padding': 20},
    )


@callback(Output('emp-info-table', 'data'), Input('emp-search-input', 'value'))
def filter_emp(search_val):
    return format_table_data(get_employee_data(search_val))
