@echo off
rem ダブルクリックで文字起こしアプリを起動する。
rem すでに起動していればブラウザを開くだけで、二重に立ち上げない。
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PORT=8765"
set "URL=http://127.0.0.1:%PORT%"

rem 起動済みかどうかを確かめる
curl.exe -s -m 2 -o nul "%URL%/healthz" 2>nul
if not errorlevel 1 (
  echo すでに起動しています。ブラウザを開きます。
  start "" "%URL%"
  timeout /t 2 >nul
  exit /b 0
)

rem py ランチャーがあれば優先する
set "PY=python"
where py >nul 2>nul && set "PY=py"

title 文字起こし  -  このウィンドウを閉じると停止します
echo.
echo   文字起こしアプリを起動しています
echo   ブラウザが自動で開きます: %URL%
echo.
echo   停止するには、このウィンドウを閉じるか Ctrl+C を押してください。
echo.

%PY% webapp.py --port %PORT% --open
set "CODE=%ERRORLEVEL%"

if not "%CODE%"=="0" (
  echo.
  echo   起動に失敗しました。終了コード: %CODE%
  echo   依存パッケージが入っていない場合は次を実行してください:
  echo     pip install -r requirements.txt
  echo.
  pause
)
exit /b %CODE%
