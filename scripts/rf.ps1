param(
  [Parameter(Mandatory=$true)]
  [ValidateSet("setup","test","build","run","bench","agent-report","cycle-summary","poll-prs","merge-pr")]
  [string]$Task
  ,
  [int]$Pr = 0,
  [switch]$Execute
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

switch ($Task) {
  "setup" {
    python -m pip install -e ".[dev]"
    Push-Location dashboard\frontend
    corepack enable
    pnpm install
    Pop-Location
  }
  "test" { pytest }
  "build" {
    Push-Location dashboard\frontend
    pnpm run build
    Pop-Location
  }
  "run" { python -m repo_foundry.api }
  "bench" { python -m repo_foundry.reconcile plan blueprints/example-repo.yaml --registry registry/repos.yaml }
  "agent-report" { python -m repo_foundry.reports agent-report }
  "cycle-summary" { python -m repo_foundry.cycle_summary append --from-sample }
  "poll-prs" { python -m repo_foundry.pr_monitor RapidFireRonin/Repo_foundry }
  "merge-pr" {
    if ($Pr -le 0) { throw "Pass -Pr <number> for merge-pr." }
    $args = @("RapidFireRonin/Repo_foundry", "$Pr")
    if ($Execute) { $args += "--execute" }
    python -m repo_foundry.merge_executor @args
  }
}
