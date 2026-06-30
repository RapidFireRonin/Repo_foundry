@echo off
setlocal

set "ROOT=%~dp0.."
set "URL=http://127.0.0.1:5274/"
cd /d "%ROOT%"

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%ROOT%\scripts\rf.ps1" phone

for /l %%i in (1,1,20) do (
  powershell.exe -NoProfile -Command "try { Invoke-WebRequest -Uri '%URL%' -UseBasicParsing -TimeoutSec 1 | Out-Null; exit 0 } catch { exit 1 }" >nul 2>nul
  if not errorlevel 1 goto open_window
  timeout /t 1 >nul
)

:open_window
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
  start "Repo Foundry Mission Control" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=%URL% --new-window
  exit /b 0
)

if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
  start "Repo Foundry Mission Control" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=%URL% --new-window
  exit /b 0
)

if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
  start "Repo Foundry Mission Control" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" --app=%URL% --new-window
  exit /b 0
)

start "Repo Foundry Mission Control" "%URL%"
