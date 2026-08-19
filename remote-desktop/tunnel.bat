@echo off
REM Open an SSH tunnel to a machine running rdcontrol (run this on the
REM device you are controlling FROM).
REM
REM   tunnel.bat user@host [remote-port] [local-port]
REM
REM Keep this window open, then browse to
REM   http://127.0.0.1:<local-port>/?token=...
REM
REM NOTE: keep this file ASCII-only (cmd.exe reads it as cp932 on Japanese
REM Windows, which would garble UTF-8 text).
setlocal

set "TARGET=%~1"
set "REMOTE_PORT=%~2"
set "LOCAL_PORT=%~3"
if "%TARGET%"=="" (
  echo Usage: %~nx0 user@host [remote-port] [local-port]
  echo   e.g. %~nx0 nori@desktop.local
  echo   e.g. %~nx0 nori@desktop.local 8765 9000
  exit /b 2
)
if "%REMOTE_PORT%"=="" set "REMOTE_PORT=8765"
if "%LOCAL_PORT%"=="" set "LOCAL_PORT=%REMOTE_PORT%"

echo Opening tunnel: 127.0.0.1:%LOCAL_PORT% -^> %TARGET% 127.0.0.1:%REMOTE_PORT%
echo Keep this window open, then browse to:
echo   http://127.0.0.1:%LOCAL_PORT%/?token=^<token shown by the server^>
echo Press Ctrl+C to stop.
echo.

ssh -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -L %LOCAL_PORT%:127.0.0.1:%REMOTE_PORT% %TARGET%
