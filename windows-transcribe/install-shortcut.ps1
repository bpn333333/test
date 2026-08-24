<#
  デスクトップに「文字起こし」のショートカットを作る。

      powershell -ExecutionPolicy Bypass -File install-shortcut.ps1

  -Startup を付けると Windows へのサインイン時に自動起動する。
  -Remove を付けると両方とも削除する。
#>
param(
  [switch]$Startup,
  [switch]$Remove
)

$ErrorActionPreference = "Stop"

$here   = $PSScriptRoot
$target = Join-Path $here "start-app.cmd"
if (-not (Test-Path $target)) {
  throw "start-app.cmd が見つかりません: $target"
}

$name    = "文字起こし.lnk"
$desktop = Join-Path ([Environment]::GetFolderPath("Desktop")) $name
$startup = Join-Path ([Environment]::GetFolderPath("Startup")) $name

function New-Link($path) {
  $shell = New-Object -ComObject WScript.Shell
  $link = $shell.CreateShortcut($path)
  $link.TargetPath       = $target
  $link.WorkingDirectory = $here
  $link.Description      = "デスクトップ音声の文字起こし"
  $link.WindowStyle      = 7   # 最小化で開く。ウィンドウは停止用に残る
  $link.Save()
  Write-Host "作成しました: $path"
}

if ($Remove) {
  foreach ($path in @($desktop, $startup)) {
    if (Test-Path $path) {
      Remove-Item $path
      Write-Host "削除しました: $path"
    }
  }
  return
}

New-Link $desktop
if ($Startup) {
  New-Link $startup
  Write-Host "サインイン時に自動起動します。解除するには -Remove を付けて実行してください。"
}
