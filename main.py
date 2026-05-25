"""Claude Panel 桌面程序（PyWebView 前端壳 + FastAPI 后端）"""
import os
import time
import threading
import uvicorn
import webview

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RENDERER_DIR = os.path.join(BASE_DIR, "renderer")
INDEX_URL = "http://localhost:8520"


def start_backend():
    """在后台线程启动 FastAPI"""
    from backend import app
    uvicorn.run(app, host="127.0.0.1", port=8520, log_level="warning")


def main():
    # 启动后端
    t = threading.Thread(target=start_backend, daemon=True)
    t.start()
    # 等待端口就绪
    time.sleep(1.5)

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
