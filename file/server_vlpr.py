# -*- coding: utf-8 -*-
"""
VLPR WebSocket 实时识别服务（被动模式）
只负责 HTTP 静态文件 + WebSocket 推送 + REST API，不主动打开摄像头
摄像头状态由 VLPR GUI 写入 .camera_status 文件，本服务轮询检测
端口: HTTP 8081 / WebSocket 8082
REST API: /api/records, /api/stats, /api/today_count
"""

import asyncio
import json
import os
import sys
import threading
import time
import socket
import urllib.parse

import database

# ===== 数据库初始化 =====
database.init_db()

# ===== 全局状态 =====
CAMERA_STATUS_FILE = None   # 状态文件路径
GUI_STATUS_FILE = None      # GUI 系统状态文件路径
gui_camera_online = False   # GUI 摄像头是否在线（通过状态文件判断）
gui_system_online = False   # GUI 系统是否在线
ws_clients = set()
_main_loop = None
camera_check_interval = 2.0  # 每 2 秒检查一次状态文件

# ===== HTTP 服务器 =====

class HTTPHandler:
    """轻量 HTTP 处理器"""

    def __init__(self):
        self.static_root = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        self.html_path = os.path.join(self.static_root, "dashboard.html")

    def do_GET(self, path, client):
        if path == "/" or path == "/dashboard.html":
            return self.serve_file(self.html_path, "text/html; charset=utf-8", client)
        elif path == "/status":
            status = {
                "camera_connected": gui_camera_online,
                "message": "摄像机已连接" if gui_camera_online else "摄像机未连接",
                "total_today": 0,
                "accuracy": 96.8,
            }
            body = json.dumps(status, ensure_ascii=False).encode('utf-8')
            self.send_response(client, 200, "application/json", body)
            return
        elif path == "/camera_status":
            # 摄像头状态专用接口，仪表盘轮询此接口检测 GUI 摄像头状态
            body = json.dumps({
                "online": gui_camera_online,
                "message": "摄像机已开启" if gui_camera_online else "摄像机未开启",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }, ensure_ascii=False).encode('utf-8')
            self.send_response(client, 200, "application/json", body)
            return
        elif path == "/gui_status":
            # GUI 系统状态接口，供仪表盘右上角使用
            body = json.dumps({
                "online": gui_system_online,
                "message": "系统在线" if gui_system_online else "系统离线",
            }, ensure_ascii=False).encode('utf-8')
            self.send_response(client, 200, "application/json", body)
            return
        elif path.startswith("/api/"):
            # ===== REST API =====
            return self.handle_api(path, client)
        else:
            file_path = os.path.join(self.static_root, path.lstrip("/"))
            if os.path.isfile(file_path):
                import mimetypes
                mime = mimetypes.guess_type(file_path)[0] or "application/octet-stream"
                return self.serve_file(file_path, mime, client)
            else:
                self.send_response(client, 404, "text/plain", b"Not Found")

    def serve_file(self, file_path, content_type, client):
        try:
            with open(file_path, 'rb') as f:
                body = f.read()
            self.send_response(client, 200, content_type, body)
        except Exception as e:
            self.send_response(client, 500, "text/plain", str(e).encode())

    def send_response(self, client, status, content_type, body):
        try:
            client.sendall(
                f"HTTP/1.1 {status} OK\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(body)}\r\n"
                f"Access-Control-Allow-Origin: *\r\n"
                f"Connection: close\r\n"
                f"\r\n".encode()
            )
            client.sendall(body)
        except Exception:
            pass

    def handle(self, client_socket, client_addr):
        try:
            data = client_socket.recv(4096)
            if not data:
                return
            lines = data.decode('utf-8', errors='ignore').split('\r\n')
            if not lines:
                return
            request_line = lines[0]
            parts = request_line.split(' ')
            if len(parts) < 2:
                return
            method, path = parts[0], parts[1]
            if method == "GET":
                self.do_GET(path, client_socket)
        except Exception:
            pass
        finally:
            try:
                client_socket.shutdown(1)
                client_socket.close()
            except Exception:
                pass

    # ===== REST API 处理器 =====
    def handle_api(self, path, client):
        """REST API 路由"""
        try:
            # 解析路径和查询参数
            if "?" in path:
                url_path, query_str = path.split("?", 1)
                params = dict(urllib.parse.parse_qsl(query_str))
            else:
                url_path = path
                params = {}

            if url_path == "/api/records":
                # 获取识别记录列表
                limit = int(params.get("limit", 100))
                offset = int(params.get("offset", 0))
                records = database.get_records(limit=limit, offset=offset)
                # 转换颜色和通道为前端需要的英文 key
                color_map = {"蓝牌": "blue", "黄牌": "yello", "绿牌": "green"}
                channel_map = {"形状定位": "shape", "颜色定位": "color"}
                for r in records:
                    r["colorKey"] = color_map.get(r["color"], "blue")
                    r["channelKey"] = channel_map.get(r["channel"], "color")
                    r["confidencePct"] = round(r["confidence"] * 100, 1)
                body = json.dumps({"success": True, "data": records}, ensure_ascii=False).encode("utf-8")
                self.send_response(client, 200, "application/json", body)

            elif url_path == "/api/stats":
                # 获取统计数据
                stats = {
                    "total": database.get_total_count(),
                    "today": database.get_today_count(),
                    "byColor": database.get_stats_by_color(),
                    "byChannel": database.get_stats_by_channel(),
                    "byProvince": database.get_stats_by_province(limit=20),
                }
                body = json.dumps({"success": True, "data": stats}, ensure_ascii=False).encode("utf-8")
                self.send_response(client, 200, "application/json", body)

            elif url_path == "/api/today_count":
                # 快速获取今日数量
                count = database.get_today_count()
                body = json.dumps({"success": True, "data": count}, ensure_ascii=False).encode("utf-8")
                self.send_response(client, 200, "application/json", body)

            else:
                body = json.dumps({"success": False, "error": "API not found"}, ensure_ascii=False).encode("utf-8")
                self.send_response(client, 404, "application/json", body)

        except Exception as e:
            body = json.dumps({"success": False, "error": str(e)}, ensure_ascii=False).encode("utf-8")
            self.send_response(client, 500, "application/json", body)


def http_server_thread():
    """HTTP 服务器线程（同步，在子线程运行）"""
    import socket
    http_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    http_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    http_sock.bind(("", PORT))
    http_sock.listen(5)
    http_sock.settimeout(1.0)
    print(f"[HTTP] Server running on http://localhost:{PORT}")
    print(f"[HTTP] Dashboard: http://localhost:{PORT}/dashboard.html")

    handler = HTTPHandler()
    while True:
        try:
            client, addr = http_sock.accept()
            t = threading.Thread(target=handler.handle, args=(client, addr), daemon=True)
            t.start()
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[HTTP] Server error: {e}")
            break

    http_sock.close()


# ===== 摄像头状态轮询线程 =====

def camera_poll_thread():
    """定期检查 .camera_status 和 .gui_status 文件，同步 GUI 摄像头及系统状态"""
    global gui_camera_online, gui_system_online, _main_loop

    print("[CAM] Camera poll thread started (passive mode).")
    print(f"[CAM] Watching camera: {CAMERA_STATUS_FILE}")
    print(f"[CAM] Watching GUI:    {GUI_STATUS_FILE}")
    was_camera_online = False
    was_gui_online = False

    while True:
        time.sleep(camera_check_interval)

        # 检查摄像头状态
        camera_online = False
        try:
            if os.path.isfile(CAMERA_STATUS_FILE):
                with open(CAMERA_STATUS_FILE, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    camera_online = (val == "1")
            if camera_online != was_camera_online:
                was_camera_online = camera_online
                ws_broadcast({
                    "type": "camera_status",
                    "connected": camera_online,
                    "message": "摄像机已开启" if camera_online else "摄像机未连接",
                })
        except Exception:
            pass

        gui_camera_online = camera_online

        # 检查 GUI 系统状态
        gui_online = False
        try:
            if os.path.isfile(GUI_STATUS_FILE):
                with open(GUI_STATUS_FILE, "r", encoding="utf-8") as f:
                    val = f.read().strip()
                    gui_online = (val == "1")
        except Exception:
            pass

        if gui_online != was_gui_online:
            was_gui_online = gui_online
            ws_broadcast({
                "type": "gui_status",
                "online": gui_online,
            })

        gui_system_online = gui_online


# ===== WebSocket 处理 =====

import websockets
import websockets.server

connected_clients = set()


async def ws_handler(websocket):
    """处理 WebSocket 客户端连接"""
    connected_clients.add(websocket)
    print(f"[WS] Client connected. Total: {len(connected_clients)}")

    try:
        # 发送初始摄像头状态
        status = {
            "type": "camera_status",
            "connected": gui_camera_online,
            "message": "摄像机已开启" if gui_camera_online else "摄像机未连接",
        }
        await websocket.send(json.dumps(status, ensure_ascii=False))

        async for msg in websocket:
            # 解析来自 GUI 的消息（如识别结果）
            try:
                data = json.loads(msg)
                if data.get("type") == "recognition_result":
                    # 广播识别结果给所有其他客户端（仪表盘）
                    broadcast_except(websocket, data)
                    print(f"[WS] Recognition result pushed: {data.get('plate', '')}")
            except Exception:
                pass

    except websockets.exceptions.ConnectionClosedOK:
        pass
    except Exception as e:
        print(f"[WS] Client error: {e}")
    finally:
        connected_clients.discard(websocket)
        print(f"[WS] Client disconnected. Total: {len(connected_clients)}")


def broadcast_except(sender_ws, message: dict):
    """广播消息给除发送者之外的所有客户端"""
    msg_str = json.dumps(message, ensure_ascii=False)

    async def _do_async():
        dead = set()
        for ws in list(connected_clients):
            if ws is sender_ws:
                continue
            try:
                await ws.send(msg_str)
            except Exception:
                dead.add(ws)
        for ws in dead:
            connected_clients.discard(ws)

    def _do():
        if _main_loop and _main_loop.is_running():
            asyncio.run_coroutine_threadsafe(_do_async(), _main_loop)

    _do()


def ws_broadcast(message: dict):
    """从任意线程广播消息到所有 WebSocket 客户端"""
    msg_str = json.dumps(message, ensure_ascii=False)

    async def _do_async():
        dead = set()
        for ws in list(connected_clients):
            try:
                await ws.send(msg_str)
            except Exception:
                dead.add(ws)
        for ws in dead:
            connected_clients.discard(ws)

    def _do():
        if _main_loop and _main_loop.is_running():
            asyncio.run_coroutine_threadsafe(_do_async(), _main_loop)

    _do()


# ===== WebSocket 服务器 =====

async def websocket_server():
    """异步 WebSocket 服务器"""
    async with websockets.serve(ws_handler, "", WS_PORT) as server:
        print(f"[WS]   WebSocket server running on ws://localhost:{WS_PORT}")
        await server.serve_forever()


# ===== 主程序 =====

PORT = 8081
WS_PORT = 8082


def open_browser():
    import webbrowser
    webbrowser.open(f"http://localhost:{PORT}/dashboard.html")


if __name__ == "__main__":
    # 确定状态文件路径（与 main_VLPR.py 同目录，即项目根目录）
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CAMERA_STATUS_FILE = os.path.join(PROJECT_ROOT, ".camera_status")
    GUI_STATUS_FILE = os.path.join(PROJECT_ROOT, ".gui_status")

    print("=" * 52)
    print("  VLPR Real-time Dashboard Server (Passive Mode)")
    print(f"  HTTP:  http://localhost:{PORT}/dashboard.html")
    print(f"  WS:    ws://localhost:{WS_PORT}")
    print("=" * 52)
    print()
    print("  [Camera Mode] Passive monitoring - no camera opened here.")
    print("  Start VLPR GUI via runSVM.bat, then click '来自摄像头'")
    print("  to activate. The dashboard will detect camera status automatically.")
    print()

    # 启动摄像头状态轮询线程（不打开摄像头，只读状态文件）
    poll_t = threading.Thread(target=camera_poll_thread, daemon=True, name="CameraPollThread")
    poll_t.start()

    # 启动 HTTP 服务器线程
    http_t = threading.Thread(target=http_server_thread, daemon=True, name="HTTPThread")
    http_t.start()

    # 启动 WebSocket 服务器（asyncio 主循环）
    _main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_main_loop)

    threading.Timer(1.5, open_browser).start()

    try:
        _main_loop.run_until_complete(websocket_server())
    except KeyboardInterrupt:
        print("\n[INFO] Server stopped by user.")
    finally:
        _main_loop.close()
