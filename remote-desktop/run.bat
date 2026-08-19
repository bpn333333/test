@echo off
REM Start the rdcontrol server on Windows.
REM   PowerShell needs the .\ prefix:   .\run.bat
REM   Options are passed through:       .\run.bat --tailscale --token mytoken123
REM
REM NOTE: keep this file ASCII-only. cmd.exe reads batch files using the OEM
REM code page (cp932 on Japanese Windows), so UTF-8 text would be garbled.
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] python not found.
  echo   Install Python 3.10+ from https://www.python.org/downloads/
  echo   and tick "Add python.exe to PATH" during setup.
  exit /b 1
)

if not exist .venv (
  echo First-time setup. This takes a few minutes...
  python -m venv .venv
  if errorlevel 1 (
    echo [ERROR] Could not create the virtual environment. See the message above.
    exit /b 1
  )
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [ERROR] Could not install dependencies.
    echo   Deleting the .venv folder and running again often fixes this.
    exit /b 1
  )
)

.venv\Scripts\python -m rdcontrol %*
