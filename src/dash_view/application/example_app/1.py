import requests
import pdpractice as pd
from io import StringIO  # 用于修复 pandas 警告
from datetime import datetime


def debug_sge_page():
    """调试上海黄金交易所页面，查看实际表格结构"""
    url = "https://www.sge.com.cn/sjzx/mrhq"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.sge.com.cn/"
    }

    try:
        print("正在请求上海黄金交易所官网...")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        print("请求成功，正在解析页面...")

        # 修复 FutureWarning：用 StringIO 包装 HTML 字符串
        html_content = StringIO(response.text)
        tables = pd.read_html(html_content)

        print(f"\n页面中共找到 {len(tables)} 个表格")
        print("=" * 80)

        # 遍历所有表格，打印基本信息
        for i, df in enumerate(tables):
            print(f"\n【表格 {i}】")
            print(f"形状：{df.shape}")
            print(f"列名：{list(df.columns)}")
            print(f"前3行数据预览：")
            print(df.head(3).to_string())
            print("-" * 80)

            # 简单判断是否可能是行情表格（包含 'Pt' 或 'Au'）
            if not df.empty and any('Pt' in str(cell) or 'Au' in str(cell) for cell in df.values.flatten()):
                print(f"\n⚠️  表格 {i} 可能包含贵金属行情数据！")

    except Exception as e:
        print(f"\n调试失败：{e}")
        import traceback
        traceback.print_exc()


# 运行调试
debug_sge_page()