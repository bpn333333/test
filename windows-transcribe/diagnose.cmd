@echo off
rem ダブルクリックでウィンドウ単位の取り込みを診断する。
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PY=python"
where py >nul 2>nul && set "PY=py"

%PY% diagnose.py
echo.
pause
