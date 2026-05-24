@echo off
chcp 65001 >nul
echo ========================================
echo   车牌识别系统 - APK 一键构建
echo ========================================
echo.

:: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 需要管理员权限
    echo 请右键点击 Build_APK_Auto.ps1
    echo 选择 "使用 PowerShell 运行" 或 "以管理员身份运行"
    pause
    exit /b 1
)

:: 运行 PowerShell 脚本
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0Build_APK_Auto.ps1"

pause
