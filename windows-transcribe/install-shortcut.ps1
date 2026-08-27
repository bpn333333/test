<#
  「文字起こし」のショートカットを作る。

      make-shortcut.cmd をダブルクリック
      （または powershell -ExecutionPolicy Bypass -File install-shortcut.ps1）

  -Startup  サインイン時に自動起動する
  -Remove   作ったショートカットをすべて削除する

  実装上の注意:
  - このファイルは UTF-8 BOM 付きで保存すること。Windows PowerShell 5.1 は
    BOM の無い .ps1 を ANSI として読み、日本語が壊れて構文解析に失敗する。
  - WScript.Shell に日本語のパスを渡すと名前が化けて保存に失敗することがある。
    ASCII の一時ファイルとして作り、.NET 側で目的の名前へ移動する。
#>
param(
  [switch]$Startup,
  [switch]$Remove
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch { }

$here   = $PSScriptRoot
$target = Join-Path $here "start-app.cmd"
if (-not (Test-Path $target)) {
  throw "start-app.cmd が見つかりません: $target"
}

$linkName = "文字起こし.lnk"

function Get-DesktopDir {
  # OneDrive でデスクトップが移動していることがあるので順に探す
  $candidates = @(
    [Environment]::GetFolderPath("DesktopDirectory")
    (Join-Path $env:USERPROFILE "Desktop")
    (Join-Path $env:USERPROFILE "OneDrive\Desktop")
    (Join-Path $env:USERPROFILE "OneDrive\デスクトップ")
  ) | Where-Object { $_ } | Select-Object -Unique

  foreach ($dir in $candidates) {
    if (Test-Path -LiteralPath $dir) { return $dir }
  }
  return $candidates[0]
}

function New-Link([string]$dir) {
  if (-not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  $final = Join-Path $dir $linkName

  # COM には ASCII のパスだけを渡す
  $temp = Join-Path ([IO.Path]::GetTempPath()) ("transcribe-" + [Guid]::NewGuid().ToString("N") + ".lnk")
  $shell = New-Object -ComObject WScript.Shell
  $link = $shell.CreateShortcut($temp)
  $link.TargetPath       = $target
  $link.WorkingDirectory = $here
  $link.Description      = "Desktop audio transcription"
  $link.WindowStyle      = 7   # 最小化で開く。ウィンドウは停止用に残る
  $link.Save()

  Move-Item -LiteralPath $temp -Destination $final -Force
  return $final
}

$desktopDir = Get-DesktopDir
$places = [ordered]@{
  "デスクトップ"     = $desktopDir
  "スタートメニュー" = [Environment]::GetFolderPath("Programs")
}
if ($Startup) {
  $places["自動起動"] = [Environment]::GetFolderPath("Startup")
}

# ---- 削除 ----------------------------------------------------------------

if ($Remove) {
  $dirs = @($places.Values) + @([Environment]::GetFolderPath("Startup")) |
          Where-Object { $_ } | Select-Object -Unique
  $removed = 0
  foreach ($dir in $dirs) {
    $path = Join-Path $dir $linkName
    if (Test-Path -LiteralPath $path) {
      Remove-Item -LiteralPath $path -Force
      Write-Host "  削除: $path"
      $removed++
    }
  }
  Write-Host ""
  if ($removed -eq 0) {
    Write-Host "削除するショートカットはありませんでした。"
  } else {
    Write-Host "$removed 件のショートカットを削除しました。start-app.cmd は残っています。"
  }
  return
}

# ---- 作成 ----------------------------------------------------------------

$created = @()
foreach ($place in $places.GetEnumerator()) {
  try {
    $path = New-Link $place.Value
    if (Test-Path -LiteralPath $path) {
      $created += $path
      Write-Host ("  [OK]   {0,-14} {1}" -f $place.Key, $path)
    } else {
      Write-Host ("  [失敗] {0,-14} 保存できましたが見つかりません: {1}" -f $place.Key, $path)
    }
  } catch {
    Write-Host ("  [失敗] {0,-14} {1}" -f $place.Key, $_.Exception.Message)
  }
}

Write-Host ""
if ($created.Count -eq 0) {
  Write-Host "ショートカットを作成できませんでした。"
  Write-Host "start-app.cmd を直接ダブルクリックすればアプリは起動します:"
  Write-Host "  $target"
  exit 1
}

Write-Host "$($created.Count) 件作成しました。"
Write-Host "見つからないときは、スタートメニューで「文字起こし」と入力してください。"

# 作った場所をエクスプローラーで開く。失敗しても作成自体には影響しない
try {
  Start-Process explorer.exe -ArgumentList ("/select,`"{0}`"" -f $created[0])
} catch { }
