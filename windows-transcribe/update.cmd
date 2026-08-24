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
rem netstat の出力解析は表示形式に左右されて空振りするので API を使う
powershell -NoProfile -Command "$p = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } ; exit 10 } ; exit 0"
if errorlevel 10 (set "RUNNING=1") else (set "RUNNING=")

echo.
if defined RUNNING (
  timeout /t 1 >nul
  echo   起動中だったので再起動します...
  start "" "%~dp0start-app.cmd"
  timeout /t 2 >nul
  echo.
  echo   更新して再起動しました。
  echo   画面の ↻ ボタンを押すと新しい一覧になります。
) else (
  echo   更新しました。start-app.cmd をダブルクリックすると起動します。
)
echo.
pause
