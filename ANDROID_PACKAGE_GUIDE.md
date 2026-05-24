# 车牌识别系统 - Android APK 打包完成说明

## ✅ 完成的工作

### 1. 代码适配 Android 环境
- ✅ 创建 `main_android.py` - Kivy 版本的 Android 应用界面
- ✅ 修改 `img_function.py` - 添加 Android 路径适配
- ✅ 创建 `buildozer.spec` - Buildozer 配置文件
- ✅ 创建 `test_android.py` - 测试脚本验证核心功能

### 2. 核心功能验证
- ✅ 依赖库导入成功 (OpenCV, NumPy, Kivy)
- ✅ 模型文件加载成功 (svm.dat, svmchinese.dat)
- ✅ 车牌识别核心逻辑正常
- ✅ Android 环境路径适配完成

## 📦 打包步骤（Windows 用户使用 WSL2）

### 第一步：安装 WSL2
```powershell
# 以管理员身份打开 PowerShell 并运行
wsl --install

# 重启计算机后，从 Microsoft Store 安装 Ubuntu 20.04 LTS
```

### 第二步：在 WSL2 中安装依赖
```bash
# 启动 Ubuntu，然后运行以下命令

# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装必需工具
sudo apt install -y \
    git zip unzip openjdk-11-jdk \
    python3 python3-pip autoconf \
    libtool pkg-config zlib1g-dev \
    libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev \
    libssl-dev python3-dev

# 安装 Buildozer
pip3 install --upgrade pip
pip3 install buildozer
pip3 install cython==0.29.19
```

### 第三步：复制项目到 WSL2
```bash
# 在 WSL2 中，Windows 文件系统位于 /mnt/
cd /mnt/c/Users/HUAWEI/Desktop/FinalDesign/Python_VLPR-master

# 或者复制项目到 WSL2 主目录（推荐，构建更快）
cp -r /mnt/c/Users/HUAWEI/Desktop/FinalDesign/Python_VLPR-master ~/
cd ~/Python_VLPR-master
```

### 第四步：构建 APK
```bash
# 初始化 Buildozer（首次运行）
buildozer android debug

# 等待构建完成
# - 首次构建需要下载 Android SDK/NDK（30-60 分钟）
# - 后续构建仅需 5-10 分钟

# 构建成功后，APK 文件位于：
# bin/platedecoder-1.0-debug.apk
```

## 📱 安装和测试

### 1. 传输 APK 到手机
- 通过 USB 数据线复制
- 通过云存储（Google Drive、Dropbox、OneDrive）
- 通过聊天软件发送

### 2. 在手机上安装
1. 打开手机"设置"
2. 进入"安全"或"隐私"设置
3. 启用"允许安装未知应用"或"未知来源"
4. 使用文件管理器找到 APK 文件
5. 点击安装

### 3. 测试应用
1. 打开"车牌识别系统"应用
2. 授予相机和存储权限
3. 测试"从相册选择"功能
4. 测试"拍照识别"功能
5. 测试"摄像头流"功能

## 🔧 常见问题解决

### 问题 1：构建失败 - 缺少 SDK/NDK
**解决方案**：
```bash
# 手动指定 SDK 和 NDK 路径（在 buildozer.spec 中）
android.sdk_path = /path/to/sdk
android.ndk_path = /path/to/ndk
```

### 问题 2：内存不足
**解决方案**：
```bash
# 增加 swap 空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 问题 3：OpenCV 导入错误
**解决方案**：
在 `buildozer.spec` 中确保包含：
```python
requirements = python3,kivy==2.1.0,opencv-python,numpy,pillow
```

### 问题 4：权限被拒绝
**解决方案**：
确保 `buildozer.spec` 中包含：
```python
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
```

## 📊 项目文件说明

```
Python_VLPR-master/
├── main_android.py          # ✅ Android 版主程序（Kivy 界面）
├── main_VLPR.py             # 桌面版主程序（Tkinter 界面）
├── img_function.py          # ✅ 车牌识别核心逻辑（已适配 Android）
├── img_math.py             # 数学计算和图像处理工具
├── img_recognition.py       # 字符识别（SVM 模型）
├── config.py                # 配置文件
├── debug.py                 # 调试工具
├── svm.dat                 # 英文和数字识别模型
├── svmchinese.dat          # 中文识别模型
├── buildozer.spec          # ✅ Buildozer 配置文件
├── test_android.py         # ✅ 测试脚本
├── PACKAGING_GUIDE.md     # 详细打包指南
├── ANDROID_PACKAGE_GUIDE.md # 本文件
├── train/                  # 训练数据
│   ├── chars2/             # 英文和数字样本
│   └── charsChinese/       # 中文样本
├── test/                   # 测试图片
├── img/                    # 图像资源
└── file/                   # 其他文件
```

## 🎯 核心改进点

### 从 Tkinter 到 Kivy 的迁移
| 功能 | Tkinter (桌面版) | Kivy (Android 版) |
|------|------------------|-------------------|
| 界面框架 | Tk() | App() |
| 布局管理 | pack(), grid() | BoxLayout, GridLayout |
| 按钮 | Button() | Button() |
| 图像显示 | Label + ImageTk | Image + Texture |
| 事件处理 | command= | bind(on_press=) |
| 文件选择 | filedialog.askopenfilename() | FileChooser |
| 摄像头 | cv2.VideoCapture(0) | Plyer + OpenCV |

### Android 路径适配
```python
# 添加在 img_function.py 开头
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# 用于正确加载模型和训练数据
```

## 🚀 性能优化建议

### 1. 减小 APK 大小
在 `buildozer.spec` 中添加：
```python
android.clean_build = True
```

### 2. 优化识别速度
- 降低摄像头分辨率
- 减少图像处理步骤
- 使用多线程进行识别

### 3. 提高识别准确率
- 增加训练数据
- 调整 SVM 参数
- 使用深度学习模型（TensorFlow Lite）

## 📝 下一步开发建议

### 1. 使用更先进的模型
- YOLO (车牌检测)
- CRNN (字符识别)
- TensorFlow Lite 或 PyTorch Mobile

### 2. 添加云端功能
- 将图像上传到服务器
- 使用云端强大的模型进行识别
- 返回识别结果

### 3. 添加数据库
- 存储识别历史
- 数据同步到云端
- 数据分析和统计

## 📞 技术支持

如遇问题，请：
1. 查看 `PACKAGING_GUIDE.md` 详细文档
2. 检查构建日志
3. 搜索相关问题
4. 联系开发者

---

**构建时间说明**：
- 首次构建：30-60 分钟（需要下载 SDK/NDK）
- 后续构建：5-10 分钟
- 请耐心等待，不要中断构建过程

**最后更新**：2026-05-17
