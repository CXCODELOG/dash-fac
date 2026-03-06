from datetime import datetime

from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash_components import Card

# 二级菜单的标题、图标和显示顺序
title = '应用3'
icon = None
order = 3
logger = Log.get_logger(__name__)

access_metas = (
    '应用3-基础权限',
    '应用3-权限1',
    '应用3-权限2',
)

def render_content(menu_access: MenuAccess, **kwargs):
    return fac.AntdFlex(
        [
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='展示',
                            value=fuc.FefferyCountUp(end=100, duration=3),
                        ),
                        title='应用3-权限1',
                    )
                ]
                if menu_access.has_access('应用3-权限1')
                else []
            ),
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='展示',
                            value=fuc.FefferyCountUp(end=200, duration=3),
                        ),
                        title='应用3-权限2',
                    )
                ]
                if menu_access.has_access('应用3-权限2')
                else []
            ),
            fac.AntdCenter(
                '常规居中',
                style={'width': 300, 'height': 150, 'background': '#f0f0f0'},
            ),
            fac.AntdSpace(
                [
                    fac.AntdCenter(
                        '常规居中',
                        style={'width': 300, 'height': 150, 'background': '#f0f0f0'},
                    ),
                    fac.AntdParagraph(
                        [
                            '测试内容',
                            fac.AntdCenter(
                                '行内居中',
                                style={
                                    'width': 100,
                                    'height': 100,
                                    'background': '#f0f0f0',
                                },
                                inline=True,
                            ),
                            '测试内容',
                        ]
                    ),
                ],
                direction='vertical',
                style={'width': '100%'},
            ),
            fac.AntdTable(
                columns=[
                    {'title': 'int型示例', 'dataIndex': 'int型示例'},
                    {'title': 'float型示例', 'dataIndex': 'float型示例'},
                    {'title': 'str型示例', 'dataIndex': 'str型示例'},
                    {'title': '日期时间示例', 'dataIndex': '日期时间示例'},
                ],
                data=[
                         {
                             'int型示例': 123,
                             'float型示例': 1.23,
                             'str型示例': '示例字符',
                             '日期时间示例': datetime.now(),
                         }
                     ]
                     * 3,
            )
        ],
        wrap='wrap',
    )