param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("setup","install","test","build","run","api","run-mobile","bench","plan","agent-report","cycle-summary","poll-prs","merge-pr","health","pr-status","mission")]
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

switch ($Task) {
  "setup" { Install-Backend }
  "install" { Install-Backend }
  "api" { & $Py -m repo_foundry.api }
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
