"""Claude Panel 桌面程序（PyWebView 前端壳）"""
import os
import webview

# 项目根目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RENDERER_DIR = os.path.join(BASE_DIR, "renderer")

# 主页面路径
INDEX_URL = os.path.join(RENDERER_DIR, "index.html")


def main():
    window = webview.create_window(
        title="Claude Panel",
        url=INDEX_URL,
        width=960,
        height=700,
        min_size=(780, 560),
        text_select=True,
    )
    webview.start(debug=False)


if __name__ == "__main__":
    main()
