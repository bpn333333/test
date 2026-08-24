@echo off
rem ダブルクリックで最新版に更新する（git pull）。
setlocal
cd /d "%~dp0"
chcp 65001 >nul

echo.
echo   最新版を取得しています...
echo.

git pull
if errorlevel 1 (
  echo.
  echo   更新に失敗しました。上のメッセージを確認してください。
  echo   git が入っていない場合は https://git-scm.com/download/win から導入します。
) else (
  echo.
  echo   更新しました。start-app.cmd をダブルクリックすると起動します。
)
echo.
pause
