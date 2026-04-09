# 导入Dash核心库
import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import pdpractice as pd
import plotly.express as px

# 1. 初始化Dash应用（相当于创建一个空白网页）
app = dash.Dash(__name__, title="滤棒成型车间业务看板")

# 2. 模拟车间生产数据（后续你可以替换成真实的Excel/数据库数据）
# 字段贴合滤棒车间：机台号、班次、产量、合格率、生产时间
data = {
    "机台号": ["1号", "2号", "3号", "1号", "2号", "3号"],
    "班次": ["早班", "早班", "早班", "晚班", "晚班", "晚班"],
    "产量(支)": [85000, 92000, 78000, 90000, 88000, 82000],
    "合格率(%)": [99.2, 99.5, 98.8, 99.0, 99.3, 98.9],
    "生产时间(小时)": [8, 8, 8, 8, 8, 8]
}
df = pd.DataFrame(data)  # 把数据转换成Dash能处理的格式

# 3. 设计网页布局（Layout）：决定网页显示什么内容
app.layout = html.Div(  # 整个网页的容器
    style={"padding": "20px"},  # 网页内边距，避免内容贴边
    children=[
        # 标题
        html.H1("滤棒成型车间生产看板", style={"textAlign": "center"}),

        # 选择框：按班次筛选数据（交互组件）
        html.Div([
            html.Label("选择班次："),
            dcc.Dropdown(
                id="shift-select",  # 组件唯一标识（回调要用）
                options=[
                    {"label": "全部", "value": "全部"},
                    {"label": "早班", "value": "早班"},
                    {"label": "晚班", "value": "晚班"}
                ],
                value="全部"  # 默认选中「全部」
            )
        ], style={"width": "30%", "margin": "20px 0"}),

        # 生产数据表格
        dash_table.DataTable(
            id="production-table",  # 表格唯一标识
            columns=[{"name": col, "id": col} for col in df.columns],  # 表格列名
            style_table={"overflowX": "auto"},  # 表格横向滚动（适配小屏幕）
            style_cell={"textAlign": "center"},  # 单元格居中
        ),

        # 产量趋势图（柱状图）
        dcc.Graph(id="production-chart")
    ]
)


# 4. 回调函数（Callback）：实现「选择班次→更新表格和图表」的交互
@app.callback(
    # 输出：表格数据、图表数据
    [Output("production-table", "data"),
     Output("production-chart", "figure")],
    # 输入：班次选择框的选中值
    Input("shift-select", "value")
)
def update_dashboard(selected_shift):
    # 筛选数据：如果选「全部」，用原始数据；否则筛选对应班次
    if selected_shift == "全部":
        filtered_df = df
    else:
        filtered_df = df[df["班次"] == selected_shift]

    # 生成表格数据（转换成Dash表格能识别的格式）
    table_data = filtered_df.to_dict("records")

    # 生成产量柱状图（x轴：机台号，y轴：产量）
    fig = px.bar(
        filtered_df,
        x="机台号",
        y="产量(支)",
        color="合格率(%)",  # 用合格率颜色区分
        title=f"{selected_shift}各机台产量对比",
        labels={"产量(支)": "产量（支）"},  # 轴标签优化
        text_auto=True  # 柱子上显示数值
    )

    return table_data, fig


# 5. 运行应用（本地访问）
if __name__ == "__main__":
    app.run_server(debug=True)  # debug=True：修改代码后网页自动刷新