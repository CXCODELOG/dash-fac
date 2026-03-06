from datetime import datetime

from common.utilities.util_menu_access import MenuAccess
import feffery_antd_components as fac
import feffery_utils_components as fuc
from common.utilities.util_logger import Log
from dash_components import Card
from dash import html


# 二级菜单的标题、图标和显示顺序
title = '应用1'
icon = None
order = 2
logger = Log.get_logger(__name__)

############# 注册权限，固定全局变量名access_metas ################
access_metas = (
    '应用1-基础权限',
    '应用1-权限1',
    '应用1-权限2',
)

############# 返回视图页面的方法，方法名固定为render_content，menu_access为用户权限对象，kwargs为url内的query参数信息 #########
def render_content(menu_access: MenuAccess, **kwargs):
    return html.Div([(fac.AntdFlex(
        [
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='展示',
                            value=fuc.FefferyCountUp(end=100, duration=3),
                        ),
                        title='应用1-权限1',
                    )
                ]
                if menu_access.has_access('应用1-权限1')  ############# 判断是否拥有“应用1-权限1”的权限
                else []
            ),
            *(
                [
                    Card(
                        fac.AntdStatistic(
                            title='展示',
                            value=fuc.FefferyCountUp(end=200, duration=3),
                        ),
                        title='应用1-权限2',
                    )
                ]
                if menu_access.has_access('应用1-权限2') ############# 判断是否拥有“应用1-权限2”的权限
                else []
            ),
        ],
        wrap='wrap',
    )),
        (fac.AntdTable(
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
)),
        (fac.AntdSlider(min=0, max=100, defaultValue=33, style={'width': 300}))])