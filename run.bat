@echo off
chcp 65001 >nul
title VLPR Real-time Dashboard - Port 8081/8082

echo.
echo  ================================================
echo    VLPR Real-time Recognition Dashboard
echo    HTTP:  http://localhost:8081/dashboard.html
echo    WS:    ws://localhost:8082
echo  ================================================
echo.

cd /d "%~dp0"

if exist "workplace\venv\Scripts\python.exe" (
    echo  [INFO] Using venv Python...
    "workplace\venv\Scripts\python.exe" "file\server_vlpr.py"
) else if exist "D:\ALLpython\python.exe" (
    echo  [INFO] Using system Python: D:\ALLpython\python.exe
    "D:\ALLpython\python.exe" "file\server_vlpr.py"
) else (
    echo  [INFO] Using default python in PATH...
    python "file\server_vlpr.py"
)

echo.
echo  Server stopped. Press any key to close...
pause >nul
