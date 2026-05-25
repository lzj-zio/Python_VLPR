# -*- coding: utf-8 -*-
"""
车牌识别系统 - Buildozer 入口文件
Kivy App 入口，供 Buildozer 打包 APK 使用

启动期装全局异常钩子：把任何未捕获异常（含 import cv2/numpy 期崩溃）的
traceback 写到 app 外部存储，便于在真机闪退时取回日志定位。
"""
import os
import sys
import time
import traceback


def _crash_paths():
    """收集可写的崩溃日志路径，优先 app 私有外部存储（无需额外权限）。"""
    paths = []
    # 1) app 私有外部存储：/sdcard/Android/data/<pkg>/files/vlpr_crash.txt
    try:
        from android import mActivity  # noqa
        ext = mActivity.getExternalFilesDir(None)
        if ext is not None:
            paths.append(os.path.join(ext.getAbsolutePath(), "vlpr_crash.txt"))
    except Exception:
        pass
    # 2) 公共存储根（需 WRITE_EXTERNAL_STORAGE，已在 spec 声明）
    paths.append("/sdcard/vlpr_crash.txt")
    # 3) 源码目录兜底（开发环境）
    try:
        paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "vlpr_crash.txt"))
    except Exception:
        pass
    return paths


def _write_crash(exc_type, exc_value, exc_tb):
    msg = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    stamp = time.strftime("%Y-%m-%d %H:%M:%S\n")
    body = stamp + msg
    for p in _crash_paths():
        try:
            with open(p, "w", encoding="utf-8") as f:
                f.write(body)
            break  # 写成功一个即可
        except Exception:
            continue
    # 同时打到 logcat（tag: python）
    try:
        from kivy.logger import Logger
        Logger.error("VLPR-CRASH:\n" + msg)
    except Exception:
        print("VLPR-CRASH:\n" + msg)


# 主线程未捕获异常
sys.excepthook = _write_crash

# 子线程未捕获异常（Python 3.8+）
try:
    import threading

    def _thread_hook(args):
        _write_crash(args.exc_type, args.exc_value, args.exc_traceback)

    threading.excepthook = _thread_hook
except Exception:
    pass


def main():
    # import 放在钩子安装之后：若 import cv2/numpy 阶段崩溃也能被记录
    from main_android import LicensePlateApp
    LicensePlateApp().run()


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException:
        _write_crash(*sys.exc_info())
        raise
