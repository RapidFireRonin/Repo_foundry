# Autonomous Completion Loop

Repo Foundry can now move safe work toward completion:

1. Poll open PRs.
2. Store mergeability, checks, failed checks, staleness, and policy decisions in SQLite.
3. Display completion state in the dashboard.
4. Plan a squash merge by default.
5. Execute only with `--execute`.
6. Write audit entries before and after merge attempts.
7. Append completion records to `AGENT_CYCLE_LOG.md` when a merge executes.
8. Mark a matching active direction done when a linked PR merges.

## Commands

```powershell
python -m repo_foundry.pr_monitor RapidFireRonin/Repo_foundry
python -m repo_foundry.merge_executor RapidFireRonin/Repo_foundry 12
python -m repo_foundry.merge_executor RapidFireRonin/Repo_foundry 12 --execute
python -m repo_foundry.merge_executor RapidFireRonin/Repo_foundry 11 --close-superseded --execute
```

The GitHub workflow `Autonomous Completion Loop` runs PR polling on a schedule and can be manually dispatched with a PR number. Its default mode is dry-run.

## Policy

The policy lives at `policies/auto-merge.yaml`. It blocks unknown checks, failed checks, conflicts, oversized PRs, blocked paths, and dangerous operations. Normal safe merges do not require human approval, but every step is logged and dashboard-visible.
