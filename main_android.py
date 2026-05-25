# -*- coding: utf-8 -*-
"""
车牌识别 Android 版本
使用 Kivy 框架构建移动端界面
支持：图片识别、拍照识别、摄像头实时识别、历史记录
"""
__author__ = '樱花落舞 - Android Port'

import os
import sys
import cv2
import numpy as np
import threading
import time

# ── Kivy 核心 ──────────────────────────────────────────────────────────────────
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp, sp
from kivy.logger import Logger
from kivy.core.window import Window
from kivy.properties import StringProperty, ListProperty
from kivy.core.text import LabelBase

# ── 注册中文字体（Kivy 默认 Roboto 不含 CJK 字形，否则界面中文乱码/方框）──
# 优先用 Android 系统自带中文字体，免打包、零额外体积。注册名覆盖默认 'Roboto'，
# 这样所有 Label/Button 无需逐个指定 font_name 即可显示中文。
_CJK_FONT_CANDIDATES = [
    '/system/fonts/NotoSansCJK-Regular.ttc',
    '/system/fonts/NotoSansCJKsc-Regular.otf',
    '/system/fonts/NotoSansSC-Regular.otf',
    '/system/fonts/DroidSansFallbackFull.ttf',
    '/system/fonts/DroidSansFallback.ttf',
]
for _cjk in _CJK_FONT_CANDIDATES:
    if os.path.exists(_cjk):
        try:
            LabelBase.register(name='Roboto', fn_regular=_cjk)
            break
        except Exception:
            continue

# 确保模块路径正确
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import img_function as predict
import img_math
import img_recognition

# ── Android 特有模块（仅真机可用）──────────────────────────────────────────────
try:
    from android.permissions import request_permissions, Permission
    IS_ANDROID = True
except ImportError:
    request_permissions = None
    Permission = None
    IS_ANDROID = False

try:
    from android import mActivity
except ImportError:
    mActivity = None

# ── 常量 ───────────────────────────────────────────────────────────────────────
COLOR_TRANSFORM = {
    "green": ("绿牌",  (0.2, 0.8, 0.2, 1)),
    "yello": ("黄牌",  (1.0, 0.85, 0.0, 1)),
    "blue":  ("蓝牌",  (0.2, 0.5, 1.0, 1)),
}
COLOR_BG_MAIN   = (0.1,  0.1,  0.14, 1)   # 深色背景
COLOR_CARD      = (0.16, 0.16, 0.22, 1)   # 卡片背景
COLOR_ACCENT    = (0.2,  0.6,  1.0,  1)   # 强调蓝
COLOR_SUCCESS   = (0.2,  0.8,  0.4,  1)   # 成功绿
COLOR_TEXT      = (0.95, 0.95, 0.95, 1)   # 主文字
COLOR_SECONDARY = (0.6,  0.6,  0.7,  1)   # 次要文字
COLOR_BTN       = (0.22, 0.22, 0.30, 1)   # 按钮底色
COLOR_BTN_PRESS = (0.3,  0.5,  0.9,  1)   # 按钮按下色


# ══════════════════════════════════════════════════════════════════════════════
# 自定义 Widget
# ══════════════════════════════════════════════════════════════════════════════

class RoundedButton(Button):
    """带圆角的自定义按钮"""
    def __init__(self, btn_color=None, **kwargs):
        self.btn_color = btn_color or COLOR_BTN
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)   # 透明原始背景
        self.color = COLOR_TEXT
        self.font_size = sp(15)
        self.bold = True
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.btn_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

    def on_press(self):
        with self.canvas.before:
            Color(*COLOR_BTN_PRESS)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

    def on_release(self):
        self._draw()


class ResultCard(BoxLayout):
    """识别结果卡片"""
    def __init__(self, channel_name, **kwargs):
        super().__init__(orientation='vertical', padding=dp(8), spacing=dp(4), **kwargs)
        self.channel_name = channel_name
        with self.canvas.before:
            Color(*COLOR_CARD)
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update_bg, size=self._update_bg)

        ch_label = Label(
            text=channel_name,
            color=COLOR_SECONDARY,
            font_size=sp(12),
            size_hint_y=None,
            height=dp(20),
        )
        self.plate_label = Label(
            text='未识别',
            color=COLOR_TEXT,
            font_size=sp(22),
            bold=True,
            size_hint_y=None,
            height=dp(36),
        )
        self.color_label = Label(
            text='',
            color=COLOR_SECONDARY,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(22),
        )
        self.add_widget(ch_label)
        self.add_widget(self.plate_label)
        self.add_widget(self.color_label)

    def _update_bg(self, *args):
        self.bg_rect.pos  = self.pos
        self.bg_rect.size = self.size

    def update(self, plate_text, color_key):
        self.plate_label.text = plate_text or '未识别'
        if color_key in COLOR_TRANSFORM:
            name, rgba = COLOR_TRANSFORM[color_key]
            self.color_label.text  = name
            self.plate_label.color = rgba
        else:
            self.color_label.text  = ''
            self.plate_label.color = COLOR_TEXT

    def reset(self):
        self.plate_label.text  = '未识别'
        self.plate_label.color = COLOR_TEXT
        self.color_label.text  = ''


class HistoryItem(BoxLayout):
    """历史记录条目"""
    def __init__(self, plate, color_name, channel, ts, **kwargs):
        super().__init__(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            padding=(dp(12), dp(6)),
            spacing=dp(8),
            **kwargs
        )
        with self.canvas.before:
            Color(*COLOR_CARD)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=lambda *a: setattr(self.bg, 'pos', self.pos),
                  size=lambda *a: setattr(self.bg, 'size', self.size))

        self.add_widget(Label(text=plate,    color=COLOR_TEXT,      font_size=sp(16), bold=True, size_hint_x=0.4))
        self.add_widget(Label(text=color_name, color=COLOR_SECONDARY, font_size=sp(13), size_hint_x=0.2))
        self.add_widget(Label(text=channel,  color=COLOR_SECONDARY, font_size=sp(11), size_hint_x=0.2))
        self.add_widget(Label(text=ts,       color=COLOR_SECONDARY, font_size=sp(11), size_hint_x=0.2))


# ══════════════════════════════════════════════════════════════════════════════
# 主界面 Screen
# ══════════════════════════════════════════════════════════════════════════════

class MainScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref

    def build_ui(self):
        """在 App 初始化完成后调用，构建实际 UI"""
        root = BoxLayout(orientation='vertical')

        with root.canvas.before:
            Color(*COLOR_BG_MAIN)
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(self.bg, 'pos', root.pos),
                  size=lambda *a: setattr(self.bg, 'size', root.size))

        # ── 标题栏 ──
        header = BoxLayout(size_hint_y=None, height=dp(52), padding=(dp(16), dp(8)))
        with header.canvas.before:
            Color(0.13, 0.13, 0.18, 1)
            self.header_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda *a: setattr(self.header_bg, 'pos', header.pos),
                    size=lambda *a: setattr(self.header_bg, 'size', header.size))
        header.add_widget(Label(
            text='🚗 车牌识别系统',
            color=COLOR_TEXT,
            font_size=sp(20),
            bold=True,
            halign='left',
        ))
        history_btn = RoundedButton(text='记录', size_hint=(None, None),
                                    size=(dp(60), dp(36)), btn_color=COLOR_ACCENT)
        history_btn.bind(on_press=lambda *a: self.app.screen_mgr.switch('history'))
        header.add_widget(history_btn)
        root.add_widget(header)

        # ── 图像预览区 ──
        self.app.image_display = KivyImage(
            size_hint_y=0.48,
            allow_stretch=True,
            keep_ratio=True,
        )
        with self.app.image_display.canvas.before:
            Color(*COLOR_CARD)
            Rectangle(pos=self.app.image_display.pos, size=self.app.image_display.size)
        root.add_widget(self.app.image_display)

        # ── 识别状态提示 ──
        self.app.status_label = Label(
            text='请选择图片或开启摄像头',
            color=COLOR_SECONDARY,
            font_size=sp(13),
            size_hint_y=None,
            height=dp(28),
        )
        root.add_widget(self.app.status_label)

        # ── 结果卡片区 ──
        card_row = BoxLayout(
            size_hint_y=None,
            height=dp(100),
            spacing=dp(8),
            padding=(dp(12), dp(4)),
        )
        self.app.card1 = ResultCard('形状定位')
        self.app.card2 = ResultCard('颜色定位')
        card_row.add_widget(self.app.card1)
        card_row.add_widget(self.app.card2)
        root.add_widget(card_row)

        # ── 按钮区 ──
        btn_row = GridLayout(
            cols=2,
            size_hint_y=None,
            height=dp(110),
            spacing=dp(8),
            padding=(dp(12), dp(6)),
        )
        btn_cfg = [
            ('📷 拍照识别',   self.app.from_camera,      COLOR_ACCENT),
            ('🖼 从相册选择', self.app.from_gallery,     COLOR_BTN),
            ('📹 开启摄像头', self.app.toggle_video,     COLOR_BTN),
            ('🔄 清除结果',   self.app.clear_results,    COLOR_BTN),
        ]
        self.app.btn_video = None
        for txt, cb, clr in btn_cfg:
            btn = RoundedButton(text=txt, btn_color=clr)
            btn.bind(on_press=cb)
            if '摄像头' in txt:
                self.app.btn_video = btn
            btn_row.add_widget(btn)
        root.add_widget(btn_row)

        self.add_widget(root)


class HistoryScreen(Screen):
    def __init__(self, app_ref, **kwargs):
        super().__init__(**kwargs)
        self.app = app_ref

    def build_ui(self):
        root = BoxLayout(orientation='vertical')

        with root.canvas.before:
            Color(*COLOR_BG_MAIN)
            self.bg = Rectangle(pos=root.pos, size=root.size)
        root.bind(pos=lambda *a: setattr(self.bg, 'pos', root.pos),
                  size=lambda *a: setattr(self.bg, 'size', root.size))

        # 标题栏
        header = BoxLayout(size_hint_y=None, height=dp(52), padding=(dp(12), dp(8)))
        with header.canvas.before:
            Color(0.13, 0.13, 0.18, 1)
            self.header_bg = Rectangle(pos=header.pos, size=header.size)
        header.bind(pos=lambda *a: setattr(self.header_bg, 'pos', header.pos),
                    size=lambda *a: setattr(self.header_bg, 'size', header.size))
        back_btn = RoundedButton(text='← 返回', size_hint=(None, None),
                                 size=(dp(70), dp(36)), btn_color=COLOR_BTN)
        back_btn.bind(on_press=lambda *a: self.app.screen_mgr.switch('main'))
        header.add_widget(back_btn)
        header.add_widget(Label(text='识别历史记录', color=COLOR_TEXT,
                                font_size=sp(18), bold=True))
        clear_btn = RoundedButton(text='清空', size_hint=(None, None),
                                  size=(dp(60), dp(36)), btn_color=(0.8, 0.2, 0.2, 1))
        clear_btn.bind(on_press=self.app.clear_history)
        header.add_widget(clear_btn)
        root.add_widget(header)

        # 列表标题
        col_header = BoxLayout(size_hint_y=None, height=dp(32),
                               padding=(dp(12), dp(4)))
        for txt, sx in [('车牌号', 0.4), ('颜色', 0.2), ('通道', 0.2), ('时间', 0.2)]:
            col_header.add_widget(Label(text=txt, color=COLOR_SECONDARY,
                                        font_size=sp(12), size_hint_x=sx))
        root.add_widget(col_header)

        # 滚动列表
        scroll = ScrollView()
        self.app.history_list = BoxLayout(
            orientation='vertical',
            spacing=dp(4),
            padding=(dp(8), dp(4)),
            size_hint_y=None,
        )
        self.app.history_list.bind(minimum_height=self.app.history_list.setter('height'))
        scroll.add_widget(self.app.history_list)
        root.add_widget(scroll)

        self.add_widget(root)


# ══════════════════════════════════════════════════════════════════════════════
# ScreenManager 包装
# ══════════════════════════════════════════════════════════════════════════════

class AppScreenManager(ScreenManager):
    def __init__(self, **kwargs):
        super().__init__(transition=FadeTransition(duration=0.2), **kwargs)

    def switch(self, name):
        self.current = name


# ══════════════════════════════════════════════════════════════════════════════
# 主 App 类
# ══════════════════════════════════════════════════════════════════════════════

class LicensePlateApp(App):

    def build(self):
        Window.clearcolor = COLOR_BG_MAIN

        # 申请权限
        self._request_android_permissions()

        # 初始化识别器（在后台线程中加载，避免阻塞 UI）
        self.predictor = None
        self._model_ready = False
        threading.Thread(target=self._load_model, daemon=True).start()

        # 摄像头状态
        self.camera         = None
        self.camera_active  = False
        self._video_event   = None

        # 识别状态
        self.latest_result  = ''
        self.latest_color   = ''
        self._recognizing   = False
        self._predict_time  = 0

        # 多帧融合
        self.history1       = []
        self.history2       = []
        self.confirmed1     = ('', None, '')
        self.confirmed2     = ('', None, '')
        self.FUSION_WINDOW  = 5
        self.FUSION_THRESHOLD = 3
        self._hist_lock     = threading.Lock()

        # 历史记录（内存中）
        self._history_records = []   # list of dict

        # ── 构建 ScreenManager ──
        self.screen_mgr = AppScreenManager()

        self.main_screen    = MainScreen(app_ref=self, name='main')
        self.history_screen = HistoryScreen(app_ref=self, name='history')

        self.screen_mgr.add_widget(self.main_screen)
        self.screen_mgr.add_widget(self.history_screen)

        # 构建各 Screen 的 UI（需要 app 属性已设好）
        self.main_screen.build_ui()
        self.history_screen.build_ui()

        # 占位图
        self._show_placeholder()

        return self.screen_mgr

    # ── 模型加载 ──────────────────────────────────────────────────────────────

    def _load_model(self):
        try:
            self._set_status('正在加载识别模型…')
            p = predict.CardPredictor()
            p.train_svm()
            self.predictor = p
            self._model_ready = True
            Clock.schedule_once(lambda dt: self._set_status('模型加载完成，可以开始识别'), 0)
            Logger.info('VLPR: Model loaded successfully')
        except Exception as e:
            Logger.error(f'VLPR: Model load failed: {e}')
            Clock.schedule_once(lambda dt, e=e: self._set_status(f'模型加载失败: {e}'), 0)

    # ── Android 权限 ──────────────────────────────────────────────────────────

    def _request_android_permissions(self):
        if not IS_ANDROID or request_permissions is None:
            return
        try:
            request_permissions([
                Permission.CAMERA,
                Permission.READ_EXTERNAL_STORAGE,
                Permission.WRITE_EXTERNAL_STORAGE,
            ])
        except Exception as e:
            Logger.warning(f'VLPR: Permission request error: {e}')

    # ── 辅助方法 ──────────────────────────────────────────────────────────────

    def _set_status(self, msg):
        if hasattr(self, 'status_label'):
            self.status_label.text = msg

    def _show_placeholder(self):
        """显示占位空图"""
        try:
            h, w = 300, 400
            placeholder = np.zeros((h, w, 3), dtype=np.uint8)
            placeholder[:] = (40, 40, 55)
            # 绘制车牌形状提示
            cv2.rectangle(placeholder, (120, 120), (280, 180), (80, 120, 200), -1)
            cv2.rectangle(placeholder, (120, 120), (280, 180), (100, 160, 255), 2)
            cv2.putText(placeholder, 'AB 12345', (128, 165),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
            self._display_image(placeholder)
        except Exception:
            pass

    def _display_image(self, img_bgr):
        """将 BGR numpy 图像显示到 Kivy Image Widget"""
        try:
            img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
            h, w   = img_rgb.shape[:2]
            texture = Texture.create(size=(w, h), colorfmt='rgb')
            texture.blit_buffer(img_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')
            texture.flip_vertical()
            self.image_display.texture = texture
        except Exception as e:
            Logger.error(f'VLPR: Display error: {e}')

    def _show_error(self, message):
        content = BoxLayout(orientation='vertical', padding=dp(16), spacing=dp(10))
        with content.canvas.before:
            Color(*COLOR_CARD)
            Rectangle(pos=content.pos, size=content.size)
        content.add_widget(Label(text=message, color=COLOR_TEXT, font_size=sp(14)))
        btn = RoundedButton(text='确定', size_hint_y=None, height=dp(44), btn_color=COLOR_ACCENT)
        popup = Popup(title='提示', content=content,
                      size_hint=(0.85, None), height=dp(200),
                      title_color=COLOR_TEXT, separator_color=COLOR_ACCENT)
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()

    # ── 图片处理与识别 ────────────────────────────────────────────────────────

    def from_gallery(self, instance=None):
        """从相册/文件系统选择图片"""
        self.stop_video()
        if not self._model_ready:
            self._show_error('模型尚未加载完成，请稍候…')
            return

        content = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(8))
        # 用 ListView 而非 IconView：图标视图对每张图生成缩略图，缩略图加载失败时
        # 条目可能不显示；列表视图只列文件名，更可靠。
        # filters 用函数而非 glob：'*.jpg' 大小写敏感，匹配不到 .JPG/.JPEG 大写扩展名。
        fc = FileChooserListView(
            path=self._get_pictures_dir(),
            filters=[lambda folder, fn: fn.lower().endswith(
                ('.jpg', '.jpeg', '.png', '.bmp', '.webp'))],
        )
        btn_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        btn_ok     = RoundedButton(text='选择',  btn_color=COLOR_ACCENT)
        btn_cancel = RoundedButton(text='取消',  btn_color=COLOR_BTN)
        btn_row.add_widget(btn_ok)
        btn_row.add_widget(btn_cancel)
        content.add_widget(fc)
        content.add_widget(btn_row)

        popup = Popup(title='选择图片', content=content,
                      size_hint=(0.95, 0.9),
                      title_color=COLOR_TEXT, separator_color=COLOR_ACCENT)

        def do_select(*_):
            if fc.selection:
                popup.dismiss()
                self._process_image_async(fc.selection[0])

        btn_ok.bind(on_press=do_select)
        btn_cancel.bind(on_press=popup.dismiss)
        popup.open()

    def from_camera(self, instance=None):
        """拍照识别（调用系统相机）"""
        self.stop_video()
        if not self._model_ready:
            self._show_error('模型尚未加载完成，请稍候…')
            return
        try:
            from plyer import camera as plyer_cam
            filename = os.path.join(self.user_data_dir, 'capture.jpg')
            plyer_cam.take_picture(filename=filename, on_complete=self._camera_callback)
        except Exception as e:
            Logger.warning(f'VLPR: Plyer camera unavailable ({e}), falling back to OpenCV')
            # 桌面环境备选：直接抓一帧
            self._grab_single_frame()

    def _camera_callback(self, file_path):
        if file_path and os.path.exists(file_path):
            self._process_image_async(file_path)
        else:
            Clock.schedule_once(lambda dt: self._show_error('拍照失败，请重试'), 0)

    def _grab_single_frame(self):
        """桌面/调试环境：抓取摄像头单帧"""
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if ret and frame is not None:
                self._display_image(frame)
                self._process_image_async(frame, is_array=True)
            else:
                self._show_error('无法打开摄像头')
        except Exception as e:
            self._show_error(f'摄像头错误: {e}')

    def _get_pictures_dir(self):
        """获取图片默认目录"""
        if IS_ANDROID:
            return '/sdcard/DCIM'
        # Windows / Linux 桌面
        pictures = os.path.join(os.path.expanduser('~'), 'Pictures')
        if os.path.exists(pictures):
            return pictures
        return os.path.expanduser('~')

    def _process_image_async(self, source, is_array=False):
        """在后台线程中处理图片，完成后更新 UI"""
        self._set_status('正在识别…')
        threading.Thread(
            target=self._recognize_image_worker,
            args=(source, is_array),
            daemon=True,
        ).start()

    def _recognize_image_worker(self, source, is_array):
        try:
            if is_array:
                img_bgr = source
            else:
                img_bgr = img_math.img_read(source)
                if img_bgr is None:
                    raise ValueError(f'无法读取图片: {source}')

            Clock.schedule_once(lambda dt: self._display_image(img_bgr), 0)

            first_img, oldimg = self.predictor.img_first_pre(img_bgr)

            r1, roi1, c1 = self.predictor.img_color_contours(first_img, oldimg)
            r2, roi2, c2 = self.predictor.img_only_color(oldimg, oldimg, first_img)

            plate1 = ''.join(r1) if r1 else ''
            plate2 = ''.join(r2) if r2 else ''

            Clock.schedule_once(lambda dt: self._update_results(plate1, c1, plate2, c2), 0)

            # 记录历史
            best_plate = plate1 or plate2
            best_color = c1 if plate1 else c2
            if best_plate:
                self._add_history(best_plate, best_color,
                                  '形状定位' if plate1 else '颜色定位',
                                  time.strftime('%H:%M:%S'))

        except Exception as e:
            Logger.error(f'VLPR: Recognition error: {e}')
            Clock.schedule_once(lambda dt, e=e: self._set_status(f'识别出错: {e}'), 0)

    def _update_results(self, plate1, color1, plate2, color2):
        self.card1.update(plate1, color1)
        self.card2.update(plate2, color2)
        if plate1 or plate2:
            self._set_status(f'识别完成：{plate1 or plate2}')
        else:
            self._set_status('未检测到车牌，请确保图片清晰')

    # ── 摄像头实时流 ──────────────────────────────────────────────────────────

    def toggle_video(self, instance=None):
        if self.camera_active:
            self.stop_video()
        else:
            self.start_video()

    def start_video(self):
        # 安卓端 OpenCV 不带摄像头后端，cv2.VideoCapture 取不到帧（灰屏）。
        # 实时预览改走原生需大改，这里禁用实时流，引导使用「拍照识别」。
        if IS_ANDROID:
            self._show_error('安卓端暂不支持实时摄像头，请使用「📷 拍照识别」')
            return
        if not self._model_ready:
            self._show_error('模型尚未加载完成，请稍候…')
            return
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                self._show_error('无法打开摄像头')
                self.camera = None
                return
            self.camera_active = True
            if self.btn_video:
                self.btn_video.text = '⏹ 停止摄像头'
            self._predict_time = time.time()
            self._video_event = Clock.schedule_interval(self._update_video, 1 / 24)
            self._set_status('摄像头已开启，实时识别中…')
        except Exception as e:
            Logger.error(f'VLPR: Start video error: {e}')
            self._show_error(f'摄像头启动失败: {e}')

    def stop_video(self):
        self.camera_active = False
        if self._video_event:
            self._video_event.cancel()
            self._video_event = None
        if self.camera is not None:
            self.camera.release()
            self.camera = None
        if hasattr(self, 'btn_video') and self.btn_video:
            self.btn_video.text = '📹 开启摄像头'
        self._set_status('摄像头已关闭')

    def _update_video(self, dt):
        if not self.camera_active or self.camera is None:
            return False

        ret, frame = self.camera.read()
        if not ret or frame is None:
            return True

        # 叠加上一次识别结果文字
        if self.latest_result:
            cv2.putText(frame, self.latest_result, (10, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 80), 2)

        self._display_image(frame)

        # 每 2 秒识别一次
        if (not self._recognizing and
                time.time() - self._predict_time > 2):
            self._recognizing = True
            self._predict_time = time.time()
            frame_copy = frame.copy()
            threading.Thread(
                target=self._video_recognize_worker,
                args=(frame_copy,),
                daemon=True,
            ).start()

        return True

    def _video_recognize_worker(self, frame):
        try:
            first_img, oldimg = self.predictor.img_first_pre(frame)
            r1, roi1, c1 = self.predictor.img_color_contours(first_img, oldimg)
            r2, roi2, c2 = self.predictor.img_only_color(oldimg, oldimg, first_img)

            plate1 = ''.join(r1) if r1 else ''
            plate2 = ''.join(r2) if r2 else ''

            with self._hist_lock:
                # 多帧融合 - 通道1
                self.history1.append(plate1)
                if len(self.history1) > self.FUSION_WINDOW:
                    self.history1.pop(0)
                cnt1 = {}
                for s in self.history1:
                    cnt1[s] = cnt1.get(s, 0) + 1
                best1 = max(cnt1, key=cnt1.get, default='')
                if cnt1.get(best1, 0) >= self.FUSION_THRESHOLD and best1:
                    self.confirmed1 = (best1, roi1, c1)
                    self.history1.clear()

                # 多帧融合 - 通道2
                self.history2.append(plate2)
                if len(self.history2) > self.FUSION_WINDOW:
                    self.history2.pop(0)
                cnt2 = {}
                for s in self.history2:
                    cnt2[s] = cnt2.get(s, 0) + 1
                best2 = max(cnt2, key=cnt2.get, default='')
                if cnt2.get(best2, 0) >= self.FUSION_THRESHOLD and best2:
                    self.confirmed2 = (best2, roi2, c2)
                    self.history2.clear()

                final1 = self.confirmed1[0] or plate1
                final2 = self.confirmed2[0] or plate2
                final_color1 = self.confirmed1[2] or c1
                final_color2 = self.confirmed2[2] or c2

                self.latest_result = final1 or final2
                self.latest_color  = final_color1 if final1 else final_color2

            Clock.schedule_once(lambda dt: self._update_results(final1, final_color1, final2, final_color2), 0)

            # 加入历史
            if self.latest_result:
                self._add_history(self.latest_result,
                                  final_color1 if final1 else final_color2,
                                  '形状定位' if final1 else '颜色定位',
                                  time.strftime('%H:%M:%S'))

        except Exception as e:
            Logger.debug(f'VLPR: Video recognize error: {e}')
        finally:
            self._recognizing = False

    # ── 历史记录 ──────────────────────────────────────────────────────────────

    def _add_history(self, plate, color_key, channel, ts):
        color_name = COLOR_TRANSFORM.get(color_key, ('未知', None))[0]
        record = dict(plate=plate, color_name=color_name, channel=channel, ts=ts)
        self._history_records.insert(0, record)
        if len(self._history_records) > 100:
            self._history_records = self._history_records[:100]
        Clock.schedule_once(lambda dt: self._refresh_history_list(), 0)

    def _refresh_history_list(self):
        if not hasattr(self, 'history_list'):
            return
        self.history_list.clear_widgets()
        for rec in self._history_records[:50]:
            item = HistoryItem(rec['plate'], rec['color_name'],
                               rec['channel'], rec['ts'])
            self.history_list.add_widget(item)

    def clear_history(self, instance=None):
        self._history_records.clear()
        if hasattr(self, 'history_list'):
            self.history_list.clear_widgets()

    def clear_results(self, instance=None):
        if hasattr(self, 'card1'):
            self.card1.reset()
        if hasattr(self, 'card2'):
            self.card2.reset()
        self._show_placeholder()
        self._set_status('结果已清除')

    # ── App 生命周期 ──────────────────────────────────────────────────────────

    def on_stop(self):
        self.stop_video()

    def on_pause(self):
        self.stop_video()
        return True

    def on_resume(self):
        pass


# ── 入口 ──────────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    LicensePlateApp().run()
