# 修复后的card.py完整兼容代码
import feffery_antd_components as fac


class Card(fac.AntdCard):
    def __init__(self, *args, **kwargs):
        # 1. 提取旧版独立样式参数，从入参中移除避免报错
        head_style = kwargs.pop('headStyle', None)
        body_style = kwargs.pop('bodyStyle', None)

        # 2. 初始化新版styles字典
        styles = kwargs.pop('styles', {})

        # 3. 旧参数自动映射到新版规范
        if head_style:
            styles['header'] = head_style
        if body_style:
            styles['body'] = body_style

        # 4. 把处理后的样式字典回写入参
        if styles:
            kwargs['styles'] = styles

        # 5. 调用父类完成初始化
        super().__init__(*args, **kwargs)