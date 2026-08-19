@echo off
REM 依存をそろえてサーバーを起動する(Windows)
REM
REM   PowerShell では先頭に .\ が必要:  .\run.bat
REM   オプションはそのまま渡せる:      .\run.bat --view-only --open
setlocal
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [エラー] python が見つかりません。
  echo   https://www.python.org/downloads/ から Python 3.10 以上をインストールし、
  echo   インストール時に "Add python.exe to PATH" にチェックを入れてください。
  exit /b 1
)

if not exist .venv (
  echo 初回セットアップ中です。少し時間がかかります...
  python -m venv .venv
  if errorlevel 1 (
    echo [エラー] 仮想環境の作成に失敗しました。上のメッセージを確認してください。
    exit /b 1
  )
  .venv\Scripts\python -m pip install --upgrade pip
  .venv\Scripts\python -m pip install -r requirements.txt
  if errorlevel 1 (
    echo [エラー] 依存パッケージのインストールに失敗しました。
    echo   .venv フォルダを削除してから、もう一度実行すると直ることがあります。
    exit /b 1
  )
)

.venv\Scripts\python -m rdcontrol %*
if errorlevel 1 (
  echo.
  echo [エラー] サーバーが起動できませんでした。上のメッセージを確認してください。
  exit /b 1
)
