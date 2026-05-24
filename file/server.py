# -*- coding: utf-8 -*-
"""
车牌识别系统 - 仪表盘 Web 服务
监听端口: 8081
访问地址: http://localhost:8081/dashboard.html
"""

import http.server
import socketserver
import os
import webbrowser
import threading

PORT = 8081
# 静态文件根目录：本脚本所在的 file/ 文件夹
SERVE_DIR = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)

    def log_message(self, format, *args):
        print(f"[REQUEST] {self.address_string()} - {format % args}")


def open_browser():
    url = f"http://localhost:{PORT}/dashboard.html"
    print(f"[INFO] 正在打开浏览器: {url}")
    webbrowser.open(url)


if __name__ == "__main__":
    os.chdir(SERVE_DIR)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        httpd.allow_reuse_address = True
        print("=" * 50)
        print("  车牌识别系统 · 仪表盘服务已启动")
        print(f"  访问地址: http://localhost:{PORT}/dashboard.html")
        print("  按 Ctrl+C 可停止服务")
        print("=" * 50)
        # 延迟 1 秒后自动打开浏览器
        threading.Timer(1.0, open_browser).start()
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] 服务已停止。")
