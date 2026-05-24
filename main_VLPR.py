# -*- coding: utf-8 -*-
__author__ = '樱花落舞'
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "file"))
import threading
import time
import tkinter as tk
import cv2
import config
import debug
import img_function as predict
import img_math
from threading import Thread
from tkinter import ttk
from tkinter.filedialog import *
from tkinter import messagebox as mBox
from PIL import Image, ImageTk
import json
import asyncio
import database

# ===== 摄像头状态共享文件 =====
CAMERA_STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".camera_status")
GUI_STATUS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".gui_status")

def write_gui_status(status):
    """写入 GUI 系统在线状态，供仪表盘读取"""
    try:
        with open(GUI_STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(str(status))
    except Exception:
        pass

def write_camera_status(status):
    """向状态文件写入摄像头状态，供 dashboard 服务器读取"""
    try:
        with open(CAMERA_STATUS_FILE, "w", encoding="utf-8") as f:
            f.write(str(status))
        print(f"[CAM-STATUS] Wrote {status} to {CAMERA_STATUS_FILE}")
    except Exception as e:
        print(f"[CAM-STATUS] Failed to write: {e}")


# ===== WebSocket 推送客户端 =====
WS_SERVER_URL = "ws://localhost:8082"

_ws_queue = []        # 待发送消息队列（跨线程安全）
_ws_thread = None
_ws_running = False
_last_saved_plate = ""  # 上一次保存到数据库的车牌号（摄像头去重用）


def _ws_worker():
    """WebSocket 后台线程，持续连接服务器并发送消息"""
    global _ws_running
    import websockets
    asyncio.set_event_loop(asyncio.new_event_loop())
    while _ws_running:
        try:
            # 每3秒重连一次
            for _ in range(30):  # 最多等30次×0.1s=3秒
                if not _ws_running:
                    break
                time.sleep(0.1)
            if not _ws_running:
                break
            # 非阻塞方式尝试连接和发送
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            async def _send_loop():
                try:
                    async with websockets.connect(WS_SERVER_URL, max_size=10 * 1024 * 1024) as ws:
                        print("[WS-CLIENT] Connected to dashboard server")
                        while _ws_running:
                            if _ws_queue:
                                msg = _ws_queue.pop(0)
                                await ws.send(msg)
                            await asyncio.sleep(0.05)
                except Exception as e:
                    print(f"[WS-CLIENT] Error: {e}")
            loop.run_until_complete(_send_loop())
        except Exception as e:
            print(f"[WS-CLIENT] Connection failed: {e}, retrying...")


def start_ws_client():
    """启动 WebSocket 推送客户端（后台线程）"""
    global _ws_thread, _ws_running
    if _ws_thread is not None and _ws_thread.is_alive():
        return
    _ws_running = True
    _ws_thread = threading.Thread(target=_ws_worker, daemon=True, name="WSClientThread")
    _ws_thread.start()


def stop_ws_client():
    """停止 WebSocket 推送客户端"""
    global _ws_running
    _ws_running = False


def push_recognition_result(plate, color, channel, confidence, timestamp, force_save=False):
    """将识别结果推送到仪表盘（线程安全），并持久化到数据库
    摄像头模式下，连续相同车牌号只保存一次数据库记录；
    图片模式通过 force_save=True 强制保存。
    """
    global _last_saved_plate

    # 确保 plate 是字符串（后端可能传字符列表）
    if isinstance(plate, (list, tuple)):
        plate = "".join(str(c) for c in plate)
    elif not isinstance(plate, str):
        plate = str(plate)

    # 写入 SQLite 数据库（去重：与上次保存的车牌相同则跳过）
    if plate and (force_save or plate != _last_saved_plate):
        try:
            database.add_record(plate, color, channel, confidence, timestamp)
            _last_saved_plate = plate
        except Exception as e:
            print(f"[DB] 写入失败: {e}")
    elif plate == _last_saved_plate and not force_save:
        print(f"[DB] 跳过重复车牌: {plate}")

    # 发送 WebSocket 消息（每次识别都推送，用于仪表盘实时显示）
    msg = json.dumps({
        "type": "recognition_result",
        "plate": plate,
        "color": color,
        "channel": channel,
        "confidence": confidence,
        "timestamp": timestamp,
    }, ensure_ascii=False)
    _ws_queue.append(msg)


class ThreadWithReturnValue(Thread):
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None, *, daemon=None):
        Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self):
        Thread.join(self)
        return self._return


class Surface(ttk.Frame):
    pic_path = ""
    viewhigh = 600
    viewwide = 600
    update_time = 0
    thread = None
    thread_run = False
    camera = None
    recognizing = False
    color_transform = {"green": ("绿牌", "#55FF55"), "yello": ("黄牌", "#FFFF00"), "blue": ("蓝牌", "#6666FF")}

    def __init__(self, win):
        ttk.Frame.__init__(self, win)
        write_gui_status(1)  # GUI 已启动，通知仪表盘
        start_ws_client()    # 启动 WebSocket 推送客户端
        frame_left = ttk.Frame(self)
        frame_right1 = ttk.Frame(self)
        frame_right2 = ttk.Frame(self)
        win.title("车牌识别")
        win.state("zoomed")
        self.pack(fill=tk.BOTH, expand=tk.YES, padx="10", pady="10")
        frame_left.pack(side=LEFT, expand=1, fill=BOTH)
        frame_right1.pack(side=TOP, expand=1, fill=tk.Y)
        frame_right2.pack(side=RIGHT, expand=0)
        ttk.Label(frame_left, text='原图：').pack(anchor="nw")
        ttk.Label(frame_right1, text='形状定位车牌位置：').grid(column=0, row=0, sticky=tk.W)

        self.from_pic_ctl = ttk.Button(frame_right2, text="来自图片", width=20, command=self.from_pic)
        self.from_vedio_ctl = ttk.Button(frame_right2, text="来自摄像头", width=20, command=self.from_vedio)
        self.stop_vedio_ctl = ttk.Button(frame_right2, text="停止摄像头", width=20, command=self.stop_vedio, state="disabled")
        from_img_pre = ttk.Button(frame_right2, text="查看形状预处理图像", width=20, command=self.show_img_pre)
        self.image_ctl = ttk.Label(frame_left)
        self.image_ctl.pack(anchor="nw")

        self.roi_ctl = ttk.Label(frame_right1)
        self.roi_ctl.grid(column=0, row=1, sticky=tk.W)
        ttk.Label(frame_right1, text='形状定位识别结果：').grid(column=0, row=2, sticky=tk.W)
        self.r_ctl = ttk.Label(frame_right1, text="", font=('Times', '20'))
        self.r_ctl.grid(column=0, row=3, sticky=tk.W)
        self.color_ctl = ttk.Label(frame_right1, text="", width="20")
        self.color_ctl.grid(column=0, row=4, sticky=tk.W)
        self.from_vedio_ctl.pack(anchor="se", pady="5")
        self.stop_vedio_ctl.pack(anchor="se", pady="5")
        self.from_pic_ctl.pack(anchor="se", pady="5")
        from_img_pre.pack(anchor="se", pady="5")

        ttk.Label(frame_right1, text='颜色定位车牌位置：').grid(column=0, row=5, sticky=tk.W)
        self.roi_ct2 = ttk.Label(frame_right1)
        self.roi_ct2.grid(column=0, row=6, sticky=tk.W)
        ttk.Label(frame_right1, text='颜色定位识别结果：').grid(column=0, row=7, sticky=tk.W)
        self.r_ct2 = ttk.Label(frame_right1, text="")
        self.r_ct2.grid(column=0, row=8, sticky=tk.W)
        self.color_ct2 = ttk.Label(frame_right1, text="")
        self.color_ct2.grid(column=0, row=9, sticky=tk.W)

        self.predictor = predict.CardPredictor()
        self.predictor.train_svm()
        self.latest_result = ""   # 摄像头模式下叠加显示的最新识别结果
        self.latest_color = ""     # 对应的车牌颜色类型
        # 多帧融合相关（形状定位通道）
        self.history1 = []   # 形状定位历史结果列表
        self.confirmed1 = ("", None, "")  # (结果字符串, roi, 颜色)
        # 多帧融合相关（颜色定位通道）
        self.history2 = []   # 颜色定位历史结果列表
        self.confirmed2 = ("", None, "")  # (结果字符串, roi, 颜色)
        self.FUSION_WINDOW = 5    # 记录最近 N 帧
        self.FUSION_THRESHOLD = 3 # 结果出现 N 次以上才确认为有效
        self.history_lock = threading.Lock()  # 线程安全锁

    def get_imgtk(self, img_bgr):
        img = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(img)
        imgtk = ImageTk.PhotoImage(image=im)
        wide = imgtk.width()
        high = imgtk.height()
        if wide > self.viewwide or high > self.viewhigh:
            wide_factor = self.viewwide / wide
            high_factor = self.viewhigh / high
            factor = min(wide_factor, high_factor)
            wide = int(wide * factor)
            if wide <= 0: wide = 1
            high = int(high * factor)
            if high <= 0: high = 1
            im = im.resize((wide, high), Image.ANTIALIAS)
            imgtk = ImageTk.PhotoImage(image=im)
        return imgtk

    def show_roi1(self, r, roi, color):
        if r:
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            roi = Image.fromarray(roi)
            self.imgtk_roi1 = ImageTk.PhotoImage(image=roi)
            self.roi_ctl.configure(image=self.imgtk_roi1, state='enable')
            self.r_ctl.configure(text=str(r))
            self.update_time = time.time()
            color_text = ""
            try:
                c = self.color_transform[color]
                self.color_ctl.configure(text=c[0], background=c[1], state='enable')
                color_text = c[0]
            except:
                self.color_ctl.configure(state='disabled')
        else:
            self._show_no_result_roi1()

    def _show_no_result_roi1(self):
        """显示形状定位无结果状态"""
        self.roi_ctl.configure(state='disabled')
        self.r_ctl.configure(text="未识别到信息")
        self.color_ctl.configure(state='disabled')

    def show_roi2(self, r, roi, color):
        if r:
            roi = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
            roi = Image.fromarray(roi)
            self.imgtk_roi2 = ImageTk.PhotoImage(image=roi)
            self.roi_ct2.configure(image=self.imgtk_roi2, state='enable')
            self.r_ct2.configure(text=str(r))
            self.update_time = time.time()
            color_text = ""
            try:
                c = self.color_transform[color]
                self.color_ct2.configure(text=c[0], background=c[1], state='enable')
                color_text = c[0]
            except:
                self.color_ct2.configure(state='disabled')
        else:
            self._show_no_result_roi2()

    def _show_no_result_roi2(self):
        """显示颜色定位无结果状态"""
        self.roi_ct2.configure(state='disabled')
        self.r_ct2.configure(text="未识别到信息")
        self.color_ct2.configure(state='disabled')

    def show_img_pre(self):
        filename = config.get_name()
        if filename is not None:
            debug.img_show(filename)

    #摄像头功能
    def from_vedio(self):
        if self.thread_run:
            return
        if self.camera is None:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                mBox.showwarning('警告', '摄像头打开失败！')
                self.camera = None
                write_camera_status(0)  # 摄像头开启失败
                return
            write_camera_status(1)  # 摄像头已开启
        self.from_vedio_ctl.configure(state="disabled")
        self.stop_vedio_ctl.configure(state="normal")
        self.thread = threading.Thread(target=self.vedio_thread, args=(self,))
        self.thread.daemon = True
        self.thread.start()
        self.thread_run = True

    def stop_vedio(self):
        self.thread_run = False
        if self.thread is not None:
            self.thread.join(2.0)
            self.thread = None
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        write_camera_status(0)  # 摄像头已关闭
        self.from_vedio_ctl.configure(state="normal")
        self.stop_vedio_ctl.configure(state="disabled")

    def from_pic(self):
        if self.thread_run:
            self.stop_vedio()
        self.pic_path = askopenfilename(title="选择识别图片", filetypes=[("jpg图片", "*.jpg"), ("png图片", "*.png")])
        if self.pic_path:
            img_bgr = img_math.img_read(self.pic_path)
            first_img, oldimg = self.predictor.img_first_pre(img_bgr)
            self.imgtk = self.get_imgtk(img_bgr)
            self.image_ctl.configure(image=self.imgtk)
            th1 = ThreadWithReturnValue(target=self.predictor.img_color_contours, args=(first_img, oldimg))
            th2 = ThreadWithReturnValue(target=self.predictor.img_only_color, args=(oldimg, oldimg, first_img))
            th1.start()
            th2.start()
            r_c, roi_c, color_c = th1.join()
            r_color, roi_color, color_color = th2.join()
            print(r_c, r_color)

            self.show_roi2(r_color, roi_color, color_color)

            self.show_roi1(r_c, roi_c, color_c)

            # 推送结果到仪表盘（图片模式，强制保存一次）
            if r_c:
                # 颜色值转中文（同 show_roi1 逻辑）
                try:
                    color_text_c = self.color_transform[color_c][0]
                except:
                    color_text_c = ""
                push_recognition_result(r_c, color_text_c, "形状定位", 0.95,
                                       time.strftime("%Y-%m-%d %H:%M:%S"), force_save=True)
            elif r_color:
                try:
                    color_text_color = self.color_transform[color_color][0]
                except:
                    color_text_color = ""
                push_recognition_result(r_color, color_text_color, "颜色定位", 0.95,
                                       time.strftime("%Y-%m-%d %H:%M:%S"), force_save=True)

    @staticmethod
    def vedio_thread(self):
        self.thread_run = True
        self.recognizing = False
        self.predict_time = time.time()
        while self.thread_run:
            ret_val, img_bgr = self.camera.read()
            if not ret_val or img_bgr is None:
                continue
            # 在帧上叠加显示最新识别结果
            if self.latest_result:
                text = "".join(self.latest_result)
                color_map = {"blue": (255, 0, 0), "yello": (0, 255, 255), "green": (0, 255, 0)}
                draw_color = color_map.get(self.latest_color, (0, 255, 0))
                cv2.putText(img_bgr, text, (10, 40),
                            cv2.FONT_HERSHEY_SIMPLEX, 1.2, draw_color, 2)
            self.imgtk = self.get_imgtk(img_bgr)
            self.image_ctl.configure(image=self.imgtk)
            if time.time() - self.predict_time > 2 and not self.recognizing:
                self.recognizing = True
                frame_copy = img_bgr.copy()
                rec_thread = ThreadWithReturnValue(target=Surface._recognize_frame, args=(self.predictor, frame_copy,), daemon=True)
                rec_thread.start()
                def _check_rec(thread=rec_thread):
                    if thread.is_alive():
                        self.after(100, _check_rec)
                        return
                    r1, roi1, c1, r2, roi2, c2 = thread.join()

                    # ========== 各自独立的多帧融合 ==========
                    result_str1 = "".join(r1) if r1 else ""
                    result_str2 = "".join(r2) if r2 else ""

                    with self.history_lock:
                        # --- 形状定位通道 ---
                        self.history1.append(result_str1)
                        if len(self.history1) > self.FUSION_WINDOW:
                            self.history1.pop(0)
                        # 统计形状定位各结果出现次数
                        count1 = {}
                        for s in self.history1:
                            count1[s] = count1.get(s, 0) + 1
                        best1, best_cnt1 = "", 0
                        for s, cnt in count1.items():
                            if cnt > best_cnt1:
                                best_cnt1 = cnt
                                best1 = s
                        if best_cnt1 >= self.FUSION_THRESHOLD and best1:
                            self.show_roi1(best1, roi1, c1)
                            self.confirmed1 = (best1, roi1, c1)
                            self.history1 = []
                        elif self.confirmed1[0]:
                            self.show_roi1(self.confirmed1[0], self.confirmed1[1], self.confirmed1[2])
                        else:
                            self.update_time = time.time()
                            self.roi_ctl.configure(state='disabled')
                            self.r_ctl.configure(text="未识别到信息")
                            self.color_ctl.configure(state='disabled')

                        # --- 颜色定位通道 ---
                        self.history2.append(result_str2)
                        if len(self.history2) > self.FUSION_WINDOW:
                            self.history2.pop(0)
                        # 统计颜色定位各结果出现次数
                        count2 = {}
                        for s in self.history2:
                            count2[s] = count2.get(s, 0) + 1
                        best2, best_cnt2 = "", 0
                        for s, cnt in count2.items():
                            if cnt > best_cnt2:
                                best_cnt2 = cnt
                                best2 = s
                        if best_cnt2 >= self.FUSION_THRESHOLD and best2:
                            self.show_roi2(best2, roi2, c2)
                            self.confirmed2 = (best2, roi2, c2)
                            self.history2 = []
                        elif self.confirmed2[0]:
                            self.show_roi2(self.confirmed2[0], self.confirmed2[1], self.confirmed2[2])
                        else:
                            self.update_time = time.time()
                            self.roi_ct2.configure(state='disabled')
                            self.r_ct2.configure(text="未识别到信息")
                            self.color_ct2.configure(state='disabled')

                        # --- 叠加显示：优先用形状通道，其次颜色通道 ---
                        if self.confirmed1[0]:
                            self.latest_result = self.confirmed1[0]
                            self.latest_color = self.confirmed1[2]
                        elif self.confirmed2[0]:
                            self.latest_result = self.confirmed2[0]
                            self.latest_color = self.confirmed2[2]
                        elif result_str1:
                            self.latest_result = result_str1
                            self.latest_color = c1 if c1 else ""
                        elif result_str2:
                            self.latest_result = result_str2
                            self.latest_color = c2 if c2 else ""

                        # 推送最终结果到仪表盘（每轮只推送一次）
                        if self.latest_result:
                            if self.confirmed1[0]:
                                _push_channel = "形状定位"
                            elif self.confirmed2[0]:
                                _push_channel = "颜色定位"
                            elif result_str1:
                                _push_channel = "形状定位"
                            else:
                                _push_channel = "颜色定位"
                            # 颜色值转中文（同 show_roi1/show_roi2 逻辑）
                            try:
                                _push_color = self.color_transform[self.latest_color][0]
                            except:
                                _push_color = ""
                            push_recognition_result(
                                self.latest_result, _push_color,
                                _push_channel, 0.95,
                                time.strftime("%Y-%m-%d %H:%M:%S")
                            )
                    # ========== 融合逻辑结束 ==========

                    self.recognizing = False
                    self.predict_time = time.time()
                self.after(100, _check_rec)
        print("run end")

    @staticmethod
    def _recognize_frame(predictor, img_bgr):
        """对单帧做完整识别，返回两组结果"""
        try:
            first_img, oldimg = predictor.img_first_pre(img_bgr)
            r_c, roi_c, color_c = predictor.img_color_contours(first_img, oldimg)
            r_color, roi_color, color_color = predictor.img_only_color(oldimg, oldimg, first_img)
            return r_c, roi_c, color_c, r_color, roi_color, color_color
        except Exception as e:
            print("_recognize_frame error:", e)
            return [], None, None, [], None, None

def close_window():
    print("destroy")
    if surface.thread_run:
        surface.thread_run = False
        surface.thread.join(2.0)
    if surface.camera is not None:
        surface.camera.release()
        surface.camera = None
    write_camera_status(0)  # 窗口关闭，摄像头状态归零
    write_gui_status(0)     # GUI 已关闭，通知仪表盘
    stop_ws_client()        # 停止 WebSocket 推送客户端
    win.destroy()


if __name__ == '__main__':
    win = tk.Tk()

    surface = Surface(win)
    # close,退出输出destroy
    win.protocol('WM_DELETE_WINDOW', close_window)
    # 进入消息循环
    win.mainloop()
