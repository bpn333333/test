@echo off
REM 操作する「側」の端末で実行するスクリプト(Windows 10 以降の ssh.exe を使用)。
REM
REM   tunnel.bat user@desktop-host [リモートポート] [ローカルポート]
REM
REM ローカルポートを省略するとリモートと同じ番号を使う。
REM
REM つないだままにして、手元のブラウザで
REM   http://127.0.0.1:<ポート>/?token=...
REM を開く。
setlocal

set "TARGET=%~1"
set "REMOTE_PORT=%~2"
set "LOCAL_PORT=%~3"
if "%TARGET%"=="" (
  echo 使い方: %~nx0 user@host [リモートポート] [ローカルポート]
  echo   例: %~nx0 nori@desktop.local
  echo   例: %~nx0 nori@desktop.local 8765 9000
  exit /b 2
)
if "%REMOTE_PORT%"=="" set "REMOTE_PORT=8765"
if "%LOCAL_PORT%"=="" set "LOCAL_PORT=%REMOTE_PORT%"

echo SSH トンネルを開きます: 127.0.0.1:%LOCAL_PORT% -^> %TARGET% の 127.0.0.1:%REMOTE_PORT%
echo つながったら、このウィンドウは開いたままブラウザで次を開いてください:
echo   http://127.0.0.1:%LOCAL_PORT%/?token=^<サーバー起動時に表示されたトークン^>
echo 終了するには Ctrl+C。
echo.

ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L %LOCAL_PORT%:127.0.0.1:%REMOTE_PORT% %TARGET%
