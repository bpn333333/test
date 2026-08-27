@echo off
rem ダブルクリックでデスクトップとスタートメニューにショートカットを作る。
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo.
echo   ショートカットを作成します
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install-shortcut.ps1" %*
if errorlevel 1 (
  echo.
  echo   作成に失敗しました。上のメッセージを確認してください。
)
echo.
pause
