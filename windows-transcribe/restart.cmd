@echo off
rem 動きが古いままのときに、状態を表示してからサーバを入れ替える。
setlocal
cd /d "%~dp0"
chcp 65001 >nul

set "PORT=8765"

echo.
echo ================================================================
echo   サーバの状態
echo ================================================================

echo.
echo [1] このフォルダのコード
git log --oneline -1 2>nul
findstr /c:"/api/windows" webapp.py >nul 2>nul && (echo     webapp.py  新しい^(ウィンドウ機能あり^)) || (echo     webapp.py  古い^(ウィンドウ機能なし^))

echo.
echo [2] ポート %PORT% を使っているプロセス
powershell -NoProfile -Command "$c = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if (-not $c) { 'none' } else { $c | ForEach-Object { Get-CimInstance Win32_Process -Filter ('ProcessId=' + $_.OwningProcess) } | ForEach-Object { '    PID ' + $_.ProcessId + '  ' + $_.CommandLine } }"

echo.
echo [3] 入れ替え
powershell -NoProfile -Command "$p = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if ($p) { $p | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue } ; exit 10 } ; exit 0"
if errorlevel 10 (set "RUNNING=1") else (set "RUNNING=")
if defined RUNNING (
  timeout /t 1 >nul
  echo     古いサーバを停止しました
) else (
  echo     動いていませんでした
)
start "" "%~dp0start-app.cmd"
timeout /t 2 >nul
echo     起動しました

echo.
echo   画面の ↻ ボタンを押してください。
echo.
pause
