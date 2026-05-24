@echo off
chcp 65001 >nul
echo ========================================
echo   车牌识别系统 - Android APK 构建工具
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 此脚本需要管理员权限
    echo 请右键点击此脚本，选择"以管理员身份运行"
    pause
    exit /b 1
)

echo [1/5] 检查 WSL 状态...
wsl --list --verbose >nul 2>&1
if %errorlevel% neq 0 (
    echo WSL 未安装，开始安装...
    echo [2/5] 启用 WSL 功能...
    dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart
    echo [3/5] 启用虚拟机平台...
    dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart
    echo.
    echo ========================================
    echo   需要重启计算机来完成安装！
    echo   重启后请再次运行此脚本
    echo ========================================
    pause
    shutdown /r /t 30 /c "WSL 安装需要重启"
    exit /b 0
)

echo ✓ WSL 已安装
echo [4/5] 在 WSL 中安装依赖和构建工具...

:: 在 WSL 中执行安装
wsl -e bash -c "cd ~ && echo '更新系统...' && sudo apt update && sudo apt upgrade -y && echo '安装工具...' && sudo apt install -y git zip unzip openjdk-11-jdk python3 python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev python3-dev wget 2>/dev/null || true && echo '安装 Python 包...' && pip3 install --upgrade pip -q && pip3 install buildozer cython==0.29.19 -q && echo '完成！'"

echo.
echo [5/5] 复制项目并构建 APK...
echo.

:: 复制项目到 WSL
wsl -e bash -c "rm -rf ~/Python_VLPR 2>/dev/null; cp -r /mnt/c/Users/HUAWEI/Desktop/FinalDesign/Python_VLPR-master ~/Python_VLPR && cd ~/Python_VLPR && echo '项目已复制，开始构建 APK...' && buildozer android debug 2>&1"

:: 复制 APK 回 Windows
wsl -e bash -c "cp ~/Python_VLPR/bin/*.apk /mnt/c/Users/HUAWEI/Desktop/ 2>/dev/null || echo 'APK 构建可能失败，请检查上方日志'"

echo.
echo ========================================
echo   构建完成！
echo   请检查桌面上的 APK 文件
echo ========================================
pause
