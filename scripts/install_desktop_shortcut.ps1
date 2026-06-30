param(
  [string]$ShortcutName = "Repo Foundry Mission Control"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "$ShortcutName.lnk"
$PowerShell = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"
$Launcher = Join-Path $PSScriptRoot "rf.ps1"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $PowerShell
$Shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Minimized -File `"$Launcher`" control"
$Shortcut.WorkingDirectory = $Root
$Shortcut.IconLocation = "$env:WINDIR\System32\shell32.dll,220"
$Shortcut.Description = "Launch Repo Foundry Mission Control"
$Shortcut.Save()

Write-Host "Created desktop shortcut: $ShortcutPath"
