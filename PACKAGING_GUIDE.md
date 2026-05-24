# 车牌识别系统 - Android APK 打包指南

## 项目概述

这是一个基于 Python 的车牌识别系统，使用 OpenCV 和 SVM 机器学习算法进行车牌识别。本指南将帮助您将这个项目打包成 Android APK 文件。

## 系统要求

### 必需环境
- **操作系统**: Linux 或 macOS（Windows 需要使用 WSL2）
- **Python**: 3.7 或更高版本
- **内存**: 至少 8GB RAM
- **磁盘空间**: 至少 20GB 可用空间

### 依赖项
- Buildozer
- Cython
- OpenCV
- NumPy
- Kivy

## 打包步骤

### 方法一：使用 WSL2（Windows 用户推荐）

#### 1. 安装 WSL2
```bash
# 以管理员身份打开 PowerShell 并运行
wsl --install
# 重启计算机后，安装 Ubuntu 发行版
```

#### 2. 在 WSL2 中安装依赖
```bash
# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装必需工具
sudo apt install -y \
    git \
    zip \
    unzip \
    openjdk-11-jdk \
    python3 \
    python3-pip \
    autoconf \
    libtool \
    pkg-config \
    zlib1g-dev \
    libncurses5-dev \
    libncursesw5-dev \
    libtinfo5 \
    cmake \
    libffi-dev \
    libssl-dev \
    python3-dev

# 安装 Buildozer
pip3 install --upgrade pip
pip3 install buildozer
pip3 install cython==0.29.19
```

#### 3. 复制项目到 WSL2
```bash
# 在 Windows 中，项目位于：
# C:\Users\HUAWEI\Desktop\FinalDesign\Python_VLPR-master
# 在 WSL2 中，对应路径为：
# /mnt/c/Users/HUAWEI/Desktop/FinalDesign/Python_VLPR-master

cd /mnt/c/Users/HUAWEI/Desktop/FinalDesign/Python_VLPR-master
```

#### 4. 构建 APK
```bash
# 初始化 Buildozer（如果还没有 buildozer.spec）
buildozer android debug

# 等待构建完成（首次构建需要下载 Android SDK/NDK，可能需要 30-60 分钟）
# 构建成功后，APK 文件位于：
# bin/platedecoder-1.0-debug.apk
```

### 方法二：使用 Linux 虚拟机

#### 1. 安装 Ubuntu 20.04 LTS
- 下载并安装 VirtualBox 或 VMware
- 创建 Ubuntu 20.04 LTS 虚拟机
- 分配至少 4GB RAM 和 40GB 磁盘空间

#### 2. 在虚拟机中构建
参考方法一的步骤 2-4。

### 方法三：使用 GitHub Actions（无需本地环境）

#### 1. 创建 GitHub 仓库
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/Python_VLPR.git
git push -u origin main
```

#### 2. 添加 GitHub Actions 工作流
创建 `.github/workflows/build-apk.yml`：
```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        sudo apt-get update
        sudo apt-get install -y \
          git zip unzip openjdk-11-jdk \
          autoconf libtool pkg-config \
          zlib1g-dev libncurses5-dev \
          libncursesw5-dev libtinfo5 \
          cmake libffi-dev libssl-dev \
          python3-dev
        pip3 install --upgrade pip
        pip3 install buildozer cython==0.29.19
    
    - name: Build APK
      run: |
        buildozer android debug
    
    - name: Upload APK
      uses: actions/upload-artifact@v2
      with:
        name: platedecoder-apk
        path: bin/*.apk
```

#### 3. 下载 APK
- 推送到 GitHub 后，Actions 会自动构建
- 在 Actions 页面下载生成的 APK 文件

## 常见问题

### 1. 构建失败：缺少 SDK 或 NDK
**解决方案**：
```bash
# 手动下载 Android SDK 和 NDK
# 或者在 buildozer.spec 中设置：
# android.sdk_path = /path/to/sdk
# android.ndk_path = /path/to/ndk
```

### 2. OpenCV 导入错误
**解决方案**：
在 `buildozer.spec` 中确保包含：
```python
requirements = python3,kivy,opencv-python,numpy,pillow
```

### 3. 权限问题
**解决方案**：
确保 `buildozer.spec` 中包含正确的权限：
```python
android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE
```

### 4. 内存不足
**解决方案**：
```bash
# 增加 swap 空间
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 安装和测试

### 1. 传输 APK 到手机
- 通过 USB 传输
- 通过云存储（Google Drive、Dropbox 等）
- 通过邮件发送

### 2. 在手机上安装
1. 打开手机"设置"
2. 进入"安全"或"隐私"
3. 启用"未知来源"或"允许安装未知应用"
4. 使用文件管理器找到 APK 文件
5. 点击安装

### 3. 测试应用
1. 打开应用
2. 授予相机和存储权限
3. 测试"从相册选择"功能
4. 测试"拍照识别"功能
5. 测试"摄像头流"功能

## 项目结构说明

```
Python_VLPR-master/
├── main_android.py          # Android 版主程序（Kivy 界面）
├── main_VLPR.py             # 桌面版主程序（Tkinter 界面）
├── img_function.py          # 车牌识别核心逻辑
├── img_math.py             # 数学计算和图像处理工具
├── img_recognition.py       # 字符识别（SVM 模型）
├── config.py                # 配置文件
├── debug.py                 # 调试工具
├── svm.dat                 # 英文和数字识别模型
├── svmchinese.dat          # 中文识别模型
├── buildozer.spec          # Buildozer 配置文件
├── train/                  # 训练数据
│   ├── chars2/             # 英文和数字样本
│   └── charsChinese/       # 中文样本
├── test/                   # 测试图片
├── img/                    # 图像资源
└── file/                   # 其他文件
```

## 代码修改说明

### 从 Tkinter 到 Kivy 的迁移

#### 主要变化：
1. **界面框架**：从 Tkinter 改为 Kivy
2. **布局管理**：从 `pack()`/`grid()` 改为 `BoxLayout`/`GridLayout`
3. **事件处理**：从 `command=` 改为 `bind(on_press=)`
4. **图像显示**：从 `ImageTk` 改为 Kivy `Texture`

#### 核心逻辑保留：
- `img_function.py`：车牌识别核心逻辑完全保留
- `img_math.py`：数学计算和图像处理工具完全保留
- `img_recognition.py`：SVM 模型训练和预测完全保留

## 性能优化建议

### 1. 减小 APK 大小
```bash
# 在 buildozer.spec 中添加
android.clean_build = True
```

### 2. 优化识别速度
- 降低摄像头分辨率
- 减少图像处理步骤
- 使用多线程进行识别

### 3. 提高识别准确率
- 增加训练数据
- 调整 SVM 参数
- 使用更先进的深度学习模型（如 YOLO、CRNN）

## 进一步开发建议

### 1. 使用深度学习模型
替换 SVM 为 CNN 或 Transformer 模型：
- 使用 TensorFlow Lite
- 使用 PyTorch Mobile
- 使用 OpenCV DNN 模块

### 2. 添加云端识别
- 将图像上传到服务器
- 使用更强大的模型进行识别
- 返回识别结果

### 3. 添加数据库功能
- 存储识别历史
- 同步到云端
- 数据分析和统计

## 参考资料

- [Kivy 官方文档](https://kivy.org/doc/stable/)
- [Buildozer 官方文档](https://buildozer.readthedocs.io/)
- [OpenCV 官方文档](https://docs.opencv.org/)
- [Android 开发者文档](https://developer.android.com/docs)

## 联系和支持

如有问题，请：
1. 查看项目 Issues
2. 创建新的 Issue
3. 联系开发者

---

**注意**：首次构建需要下载 Android SDK 和 NDK，可能需要较长时间（30-60 分钟）。请耐心等待。
