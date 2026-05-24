[app]

# ─── 基本信息 ──────────────────────────────────────────────────────────────────
title = 车牌识别
package.name = vlpr
package.domain = com.vlpr

# ─── 入口与源码 ────────────────────────────────────────────────────────────────
# main.py 是 Buildozer 默认入口（已设为 from main_android import LicensePlateApp）
source.dir = .

# 打包的文件类型
source.include_exts = py,png,jpg,jpeg,dat,kv,txt,xml

# 明确包含模型文件和图标
source.include_patterns = svm.dat,svmchinese.dat,img/icon.png,img/*.png,img/*.PNG

# 明确排除不需要的大目录（训练数据体积巨大，APK 里不需要）
source.exclude_dirs = train,test,file,workplace,__pycache__,.workbuddy
source.exclude_patterns = *.pyc,*.pyo,*.7z,*.docx,*.bat,*.ps1,*.md,*.spec,.git/**

# ─── 版本 ──────────────────────────────────────────────────────────────────────
version = 1.0

# ─── 依赖库 ────────────────────────────────────────────────────────────────────
# 注意: Buildozer/p4a 中 opencv 包名为 opencv，不是 opencv-python
requirements = python3,kivy==2.1.0,numpy,opencv,pillow,plyer

# ─── 图标 ──────────────────────────────────────────────────────────────────────
icon.filename = %(source.dir)s/img/icon.png

# ─── 屏幕方向 ─────────────────────────────────────────────────────────────────
# portrait 竖屏 / landscape 横屏 / all 不限制
orientation = portrait

# ─── Android 平台配置 ─────────────────────────────────────────────────────────
# API 级别：目标 / 最低 / 编译
android.api = 33
android.minapi = 21
android.ndk = 25b

# 权限（Android 13+ 需要 READ_MEDIA_IMAGES 替代 READ_EXTERNAL_STORAGE）
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,READ_MEDIA_IMAGES,INTERNET

# 硬件特性声明
android.features = android.hardware.camera,android.hardware.camera.autofocus

# ABI 目标架构（arm64-v8a 覆盖主流手机；可加 armeabi-v7a 兼容旧机）
android.archs = arm64-v8a

# 保持屏幕常亮（识别时需要）
android.wakelock = True

# 状态栏颜色
android.statusbar_color = #1A1A23

# 允许备份（可选）
android.allow_backup = True

# 自动接受 SDK 许可协议（CI/CD 环境必须设为 True）
android.accept_sdk_license = True

# ─── 全屏 / 沉浸式 ────────────────────────────────────────────────────────────
fullscreen = 0

# ─── iOS 占位（不使用）────────────────────────────────────────────────────────
# ios.kivy_ios_url = https://github.com/kivy/kivy-ios
# ios.kivy_ios_branch = master

# ─── Python for Android ───────────────────────────────────────────────────────
# 使用最新稳定版 p4a（留空则 buildozer 自动选择）
# p4a.branch = master

# ─── 构建选项 ─────────────────────────────────────────────────────────────────
[buildozer]

# 日志级别：0=错误 1=信息 2=调试（首次构建建议用 2 方便排查）
log_level = 2

# 自动接受 Google 的 SDK 许可
android.accept_sdk_license = True
