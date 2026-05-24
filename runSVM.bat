@echo off
title VLPR System

set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

call "%PROJECT_DIR%workplace\venv\Scripts\activate.bat"

echo Starting License Plate Recognition System...
python main_VLPR.py

call "%PROJECT_DIR%workplace\venv\Scripts\deactivate.bat"
pause
