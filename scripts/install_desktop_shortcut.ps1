param(
  [string]$ShortcutName = "Repo Foundry Mission Control"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Desktop = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $Desktop "$ShortcutName.lnk"
$Cmd = Join-Path $env:WINDIR "System32\cmd.exe"
$Launcher = Join-Path $PSScriptRoot "launch_control_window.cmd"

$Shell = New-Object -ComObject WScript.Shell
$Shortcut = $Shell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $Cmd
$Shortcut.Arguments = "/c `"$Launcher`""
$Shortcut.WorkingDirectory = $Root
$Shortcut.IconLocation = "$env:WINDIR\System32\shell32.dll,220"
$Shortcut.Description = "Launch Repo Foundry Mission Control"
$Shortcut.Save()

Write-Host "Created desktop shortcut: $ShortcutPath"
