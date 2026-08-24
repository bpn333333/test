<#
  「文字起こし」のショートカットを作る。

      powershell -ExecutionPolicy Bypass -File install-shortcut.ps1

  デスクトップとスタートメニューの両方に置く。デスクトップは OneDrive に
  移動していることがあるため、作成先を実際のパスで表示し、最後に
  エクスプローラーで選択状態にして開く。

  -Startup  サインイン時に自動起動する
  -Remove   作ったショートカットをすべて削除する
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

$name = "文字起こし.lnk"
$paths = [ordered]@{
  "デスクトップ"       = Join-Path ([Environment]::GetFolderPath("Desktop")) $name
  "スタートメニュー"   = Join-Path ([Environment]::GetFolderPath("Programs")) $name
}
$startupPath = Join-Path ([Environment]::GetFolderPath("Startup")) $name

function New-Link($path) {
  $parent = Split-Path -Parent $path
  if (-not (Test-Path $parent)) {
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
  }
  $shell = New-Object -ComObject WScript.Shell
  $link = $shell.CreateShortcut($path)
  $link.TargetPath       = $target
  $link.WorkingDirectory = $here
  $link.Description      = "デスクトップ音声の文字起こし"
  $link.WindowStyle      = 7   # 最小化で開く。ウィンドウは停止用に残る
  $link.Save()
}

if ($Remove) {
  foreach ($path in @($paths.Values) + @($startupPath)) {
    if (Test-Path $path) {
      Remove-Item $path
      Write-Host "削除しました: $path"
    }
  }
  Write-Host ""
  Write-Host "ショートカットを削除しました。start-app.cmd は残っています。"
  return
}

Write-Host ""
foreach ($entry in $paths.GetEnumerator()) {
  New-Link $entry.Value
  Write-Host ("  {0,-16} {1}" -f $entry.Key, $entry.Value)
}

if ($Startup) {
  New-Link $startupPath
  Write-Host ("  {0,-16} {1}" -f "自動起動", $startupPath)
}

Write-Host ""
Write-Host "デスクトップに見つからないときは、スタートメニューで「文字起こし」と入力してください。"
Write-Host "元のファイルはこちらです: $target"

# 作った場所をエクスプローラーで開き、ショートカットを選択状態にする
Start-Process explorer.exe "/select,`"$($paths['デスクトップ'])`""
