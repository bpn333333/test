@echo off
REM 操作する「側」の端末で実行するスクリプト(Windows 10 以降の ssh.exe を使用)。
REM
REM   tunnel.bat user@desktop-host [ポート]
REM
REM つないだままにして、手元のブラウザで
REM   http://127.0.0.1:<ポート>/?token=...
REM を開く。
setlocal

set "TARGET=%~1"
set "PORT=%~2"
if "%TARGET%"=="" (
  echo 使い方: %~nx0 user@host [ポート]
  echo   例: %~nx0 nori@desktop.local 8765
  exit /b 2
)
if "%PORT%"=="" set "PORT=8765"

echo SSH トンネルを開きます: 127.0.0.1:%PORT% -^> %TARGET% の 127.0.0.1:%PORT%
echo つながったら、このウィンドウは開いたままブラウザで次を開いてください:
echo   http://127.0.0.1:%PORT%/?token=^<サーバー起動時に表示されたトークン^>
echo 終了するには Ctrl+C。
echo.

ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L %PORT%:127.0.0.1:%PORT% %TARGET%
