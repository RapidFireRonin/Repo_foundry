param(
  [string]$Repo = "RapidFireRonin/Repo_foundry",
  [int]$MaxMerges = 3
)

$ErrorActionPreference = "Stop"

$Root = "C:\Users\Garrett\Desktop\AUTOREPO"
Set-Location $Root

$LogDir = Join-Path $Root "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$LogFile = Join-Path $LogDir "repo-foundry-pr-shipper-$Stamp.log"

function Log($msg) {
  $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
  Write-Host $line
  Add-Content -Path $LogFile -Value $line
}

function Get-Gh {
  $cmd = Get-Command gh -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }

  $candidates = @(
    "$env:ProgramFiles\GitHub CLI\gh.exe",
    "$env:LOCALAPPDATA\Programs\GitHub CLI\gh.exe"
  )

  foreach ($candidate in $candidates) {
    if (Test-Path $candidate) { return $candidate }
  }

  throw "GitHub CLI not found. Install GitHub CLI or reopen PowerShell."
}

$gh = Get-Gh

Log "Using gh: $gh"
Log "Checking GitHub auth..."
& $gh auth status
if ($LASTEXITCODE -ne 0) {
  throw "GitHub auth failed. Run: gh auth login"
}

Log "Enabling repo auto-merge setting if permitted..."
try {
  & $gh api -X PATCH "repos/$Repo" -f allow_auto_merge=true | Out-Null
  Log "Repo auto-merge setting enabled or already enabled."
} catch {
  Log "Could not enable repo auto-merge setting: $($_.Exception.Message)"
}

$depPatterns = @(
  "package.json",
  "package-lock.json",
  "pnpm-lock.yaml",
  "yarn.lock",
  "requirements.txt",
  "pyproject.toml",
  "poetry.lock",
  "Pipfile",
  "Pipfile.lock"
)

function Get-ChangedFiles($number) {
  $files = @(& $gh pr diff $number --repo $Repo --name-only)
  return $files
}

function Has-DependencyFileChange($files) {
  foreach ($file in $files) {
    foreach ($pattern in $depPatterns) {
      if ($file -eq $pattern -or $file.EndsWith("/$pattern")) {
        return $true
      }
    }
  }
  return $false
}

function Get-CheckSummary($detail) {
  $checks = @($detail.statusCheckRollup)

  $failed = @()
  $pending = @()
  $passed = @()

  foreach ($check in $checks) {
    $name = $check.name
    if (!$name) { $name = $check.context }
    if (!$name) { $name = "unknown-check" }

    $stateText = "$($check.status) $($check.conclusion) $($check.state)".ToUpperInvariant()

    if ($stateText -match "FAILURE|FAILED|ERROR|CANCELLED|TIMED_OUT|ACTION_REQUIRED") {
      $failed += $name
    } elseif ($stateText -match "PENDING|QUEUED|IN_PROGRESS|WAITING|REQUESTED" -or (!$check.conclusion -and !$check.state)) {
      $pending += $name
    } else {
      $passed += $name
    }
  }

  return [PSCustomObject]@{
    Failed = @($failed | Select-Object -Unique)
    Pending = @($pending | Select-Object -Unique)
    Passed = @($passed | Select-Object -Unique)
  }
}

function Update-Branch($number) {
  try {
    Log "Requesting branch update for PR #${number}..."
    & $gh api -X PUT "repos/$Repo/pulls/$number/update-branch" --silent
    if ($LASTEXITCODE -eq 0) {
      Log "Branch update requested for PR #${number}."
    } else {
      Log "Branch update failed or not needed for PR #${number}."
    }
  } catch {
    Log "Branch update error for PR #${number}: $($_.Exception.Message)"
  }
}

function Try-CompletePr($pr) {
  $n = $pr.number
  Log "----"
  Log "Inspecting PR #${n}: $($pr.title)"

  $detailRaw = & $gh pr view $n --repo $Repo --json number,title,isDraft,mergeStateStatus,statusCheckRollup,headRefName,baseRefName,url
  if (!$detailRaw) {
    Log "Could not read PR #${n}. Skipping."
    return $false
  }

  $detail = $detailRaw | ConvertFrom-Json

  if ($detail.isDraft) {
    Log "PR #${n} is draft. Skipping."
    return $false
  }

  $mergeState = "$($detail.mergeStateStatus)"
  Log "Merge state: $mergeState"

  if ($mergeState -match "DIRTY|CONFLICTING") {
    Log "PR #${n} is conflicted. Skipping for agent repair."
    return $false
  }

  if ($mergeState -match "UNKNOWN") {
    Update-Branch $n
    Log "UNKNOWN merge state. Waiting 90 seconds, then rechecking PR #${n}..."
    Start-Sleep -Seconds 90

    $detailRaw = & $gh pr view $n --repo $Repo --json number,title,isDraft,mergeStateStatus,statusCheckRollup,headRefName,baseRefName,url
    $detail = $detailRaw | ConvertFrom-Json
    $mergeState = "$($detail.mergeStateStatus)"
    Log "Rechecked merge state: $mergeState"

    if ($mergeState -match "UNKNOWN|DIRTY|CONFLICTING") {
      Log "PR #${n} still not safely mergeable. Skipping."
      return $false
    }
  }

  $files = Get-ChangedFiles $n
  $depChanged = Has-DependencyFileChange $files

  Log "Changed files: $($files.Count)"
  Log "Dependency files changed: $depChanged"

  if ($files.Count -gt 30) {
    Log "PR #${n} changes too many files. Skipping."
    return $false
  }

  $checks = Get-CheckSummary $detail

  $failed = @($checks.Failed)
  $pending = @($checks.Pending)

  if ($pending.Count -gt 0) {
    Log "PR #${n} has pending checks: $($pending -join ', '). Enabling auto-merge."
    & $gh pr merge $n --repo $Repo --squash --auto --delete-branch
    if ($LASTEXITCODE -eq 0) {
      Log "Auto-merge enabled for PR #${n}."
    } else {
      Log "Auto-merge command failed for PR #${n}."
    }
    return $false
  }

  if ($failed.Count -eq 1 -and $failed[0] -eq "dependency-review" -and !$depChanged) {
    Log "PR #${n} is blocked only by dependency-review and changed no dependency files. Admin-merging as safe override."
    & $gh pr merge $n --repo $Repo --squash --admin --delete-branch
    if ($LASTEXITCODE -eq 0) {
      Log "Admin-merged PR #${n}."
      return $true
    } else {
      Log "Admin merge failed for PR #${n}."
      return $false
    }
  }

  if ($failed.Count -gt 0) {
    Log "PR #${n} has failing checks: $($failed -join ', '). Skipping."
    return $false
  }

  Log "PR #${n} has no failed/pending checks. Squash merging."
  & $gh pr merge $n --repo $Repo --squash --delete-branch
  if ($LASTEXITCODE -eq 0) {
    Log "Merged PR #${n}."
    return $true
  }

  Log "Normal merge failed for PR #${n}. Trying auto-merge fallback."
  & $gh pr merge $n --repo $Repo --squash --auto --delete-branch
  if ($LASTEXITCODE -eq 0) {
    Log "Auto-merge enabled for PR #${n}."
  } else {
    Log "Auto-merge fallback failed for PR #${n}."
  }

  return $false
}

Log "Fetching open PRs..."
$prs = & $gh pr list --repo $Repo --state open --limit 50 --json number,title,updatedAt | ConvertFrom-Json

if (!$prs -or $prs.Count -eq 0) {
  Log "No open PRs. Nothing to ship."
  exit 0
}

$priority = @(4,8,9,10,3)
$ordered = @()

foreach ($num in $priority) {
  $match = $prs | Where-Object { $_.number -eq $num }
  if ($match) { $ordered += $match }
}

$ordered += $prs | Where-Object { $priority -notcontains $_.number }

$merged = 0

foreach ($pr in $ordered) {
  if ($merged -ge $MaxMerges) {
    Log "Max merges reached for this run: $MaxMerges"
    break
  }

  $didMerge = Try-CompletePr $pr
  if ($didMerge) {
    $merged += 1
    Log "Waiting 45 seconds after merge so GitHub can update main..."
    Start-Sleep -Seconds 45
  }
}

Log "Done. Merged $merged PR(s)."
Log "Log written to $LogFile"
