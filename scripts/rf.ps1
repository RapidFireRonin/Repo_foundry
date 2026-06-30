param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("setup","install","test","build","run","api","phone","run-mobile","bench","plan","agent-report","cycle-summary","poll-prs","merge-pr","health","pr-status","mission")]
  [string]$Task
  ,
  [int]$Pr = 0,
  [switch]$Execute
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Get-Python {
  $candidates = @(
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "C:\Users\Garrett\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe",
    "python"
  )
  foreach ($candidate in $candidates) {
    try {
      if ($candidate -eq "python") {
        $cmd = Get-Command python -ErrorAction SilentlyContinue
        if ($cmd) { return $cmd.Source }
      } elseif (Test-Path $candidate) {
        return $candidate
      }
    } catch {}
  }
  throw "Python not found. Install Python 3.11+ or run setup from Codex bundled runtime."
}

function Get-Pnpm {
  $cmd = Get-Command pnpm -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $candidate = "C:\Users\Garrett\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd"
  if (Test-Path $candidate) { return $candidate }
  throw "pnpm not found. Install Node/pnpm or use the bundled Codex runtime."
}

$Py = Get-Python

function Install-Backend {
  if (Test-Path ".\pyproject.toml") {
    & $Py -m pip install -e ".[dev]"
  } elseif (Test-Path ".\requirements.txt") {
    & $Py -m pip install -r .\requirements.txt
  } else {
    & $Py -m pip install fastapi uvicorn pydantic pyyaml pytest httpx
  }
}

function Build-Frontend {
  Push-Location .\dashboard\frontend
  try {
    $pnpm = Get-Pnpm
    & $pnpm install
    & $pnpm run build
  } finally {
    Pop-Location
  }
}

function Get-LanIp {
  $override = $env:REPO_FOUNDRY_LAN_IP
  if ($override) { return $override }
  $route = Get-NetRoute -DestinationPrefix "0.0.0.0/0" -ErrorAction SilentlyContinue | Sort-Object RouteMetric | Select-Object -First 1
  if ($route) {
    $addr = Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex -ErrorAction SilentlyContinue |
      Where-Object { $_.IPAddress -notlike "169.254.*" -and $_.IPAddress -ne "127.0.0.1" } |
      Select-Object -First 1
    if ($addr) { return $addr.IPAddress }
  }
  return "127.0.0.1"
}

function Get-TailscaleIp {
  if ($env:REPO_FOUNDRY_TAILSCALE_IP) { return $env:REPO_FOUNDRY_TAILSCALE_IP }
  $cmd = Get-Command tailscale -ErrorAction SilentlyContinue
  if (-not $cmd) { return $null }
  $ip = (& $cmd.Source ip -4 2>$null | Where-Object { $_ -like "100.*" } | Select-Object -First 1)
  return $ip
}

function Start-PhoneDashboard {
  $lan = Get-LanIp
  $tail = Get-TailscaleIp
  $artifactDir = Join-Path $Root "artifacts\phone"
  New-Item -ItemType Directory -Force -Path $artifactDir | Out-Null

  $apiListening = Get-NetTCPConnection -LocalPort 8765 -State Listen -ErrorAction SilentlyContinue
  if (-not $apiListening) {
    $apiArgs = "-NoProfile -ExecutionPolicy Bypass -Command `$env:REPO_FOUNDRY_API_HOST='0.0.0.0'; `$env:REPO_FOUNDRY_LAN_IP='$lan'; $(if ($tail) { "`$env:REPO_FOUNDRY_TAILSCALE_IP='$tail'; " }) Set-Location '$Root'; & '$Py' -m repo_foundry.api *> artifacts\phone\api.log"
    Start-Process -FilePath "powershell.exe" -ArgumentList $apiArgs -WindowStyle Hidden | Out-Null
  }

  $pnpmPath = Get-Pnpm
  $uiListening = Get-NetTCPConnection -LocalPort 5274 -State Listen -ErrorAction SilentlyContinue
  if (-not $uiListening) {
    $uiArgs = "-NoProfile -ExecutionPolicy Bypass -Command `$env:Path='C:\Users\Garrett\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin;C:\Users\Garrett\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin;' + `$env:Path; Set-Location '$Root\dashboard\frontend'; & '$pnpmPath' run dev:mobile *> '$Root\artifacts\phone\ui.log'"
    Start-Process -FilePath "powershell.exe" -ArgumentList $uiArgs -WindowStyle Hidden | Out-Null
  }

  $payload = [ordered]@{
    generated_at = (Get-Date).ToUniversalTime().ToString("o")
    desktop_url = "http://127.0.0.1:5274"
    lan_phone_url = "http://${lan}:5274"
    tailscale_phone_url = $(if ($tail) { "http://${tail}:5274" } else { $null })
    api_url = "http://${lan}:8765"
  }
  $payload | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $artifactDir "latest-url.json")
  @(
    "# Repo Foundry Phone URL"
    ""
    "- Desktop: http://127.0.0.1:5274"
    "- iPhone on Wi-Fi: http://${lan}:5274"
    $(if ($tail) { "- iPhone on Tailscale: http://${tail}:5274" } else { "- iPhone on Tailscale: not detected" })
    "- API: http://${lan}:8765"
  ) | Set-Content -Encoding UTF8 (Join-Path $artifactDir "latest-url.md")

  Write-Host ""
  Write-Host "Repo Foundry is starting for phone access."
  Write-Host "Desktop: http://127.0.0.1:5274"
  Write-Host "iPhone on Wi-Fi: http://${lan}:5274"
  if ($tail) { Write-Host "iPhone on Tailscale: http://${tail}:5274" }
  Write-Host "API: http://${lan}:8765"
  Write-Host "Saved: artifacts\phone\latest-url.md"
}

switch ($Task) {
  "setup" { Install-Backend }
  "install" { Install-Backend }
  "api" { & $Py -m repo_foundry.api }
  "phone" { Start-PhoneDashboard }
  "run" { & $Py -m repo_foundry.api }
  "run-mobile" {
    $env:REPO_FOUNDRY_API_HOST = "0.0.0.0"
    & $Py -m repo_foundry.api
  }
  "test" { & $Py -m pytest }
  "build" { Build-Frontend }
  "bench" { & $Py -m repo_foundry.reconcile plan .\blueprints\example-repo.yaml --registry .\registry\repos.yaml }
  "plan" { & $Py -m repo_foundry.reconcile plan .\blueprints\example-repo.yaml --registry .\registry\repos.yaml }
  "agent-report" { & $Py -m repo_foundry.reports agent-report }
  "cycle-summary" { & $Py -m repo_foundry.cycle_summary append --from-sample }
  "poll-prs" { & $Py -m repo_foundry.pr_monitor RapidFireRonin/Repo_foundry --write-snapshots artifacts/pr-status }
  "merge-pr" {
    if ($Pr -le 0) { throw "Pass -Pr <number> for merge-pr." }
    $args = @("RapidFireRonin/Repo_foundry", $Pr)
    if ($Execute) { $args += "--execute" }
    & $Py -m repo_foundry.merge_executor @args
  }
  "health" { & $Py -m repo_foundry.health }
  "pr-status" { & $Py -m repo_foundry.pr_status }
  "mission" { & $Py -c "import json; from repo_foundry.mission_control import build_mission_control; print(json.dumps(build_mission_control(), indent=2))" }
}
