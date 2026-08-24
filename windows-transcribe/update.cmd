@echo off
rem ダブルクリックで最新版に更新し、起動中なら自動で再起動する。
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PORT=8765"

echo.
echo   最新版を取得しています...
echo.

git pull
if errorlevel 1 (
  echo.
  echo   更新に失敗しました。上のメッセージを確認してください。
  echo   git が入っていない場合は https://git-scm.com/download/win から導入します。
  echo.
  pause
  exit /b 1
)

rem 起動中のサーバは古いコードを読み込んだままなので、必ず入れ替える。
rem ポートを掴んでいるプロセスを止めれば、ウィンドウが見えなくても確実に落ちる
set "RUNNING="
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /r /c:":%PORT% .*LISTENING"') do (
  set "RUNNING=1"
  taskkill /PID %%p /F >nul 2>nul
)

echo.
if defined RUNNING (
  timeout /t 1 >nul
  echo   起動中だったので再起動します...
  start "" "%~dp0start-app.cmd"
  timeout /t 2 >nul
  echo.
  echo   更新して再起動しました。
  echo   ブラウザで Ctrl+F5 を押すと新しい画面になります。
) else (
  echo   更新しました。start-app.cmd をダブルクリックすると起動します。
)
echo.
pause
