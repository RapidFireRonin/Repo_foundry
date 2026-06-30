# Architecture

Repo Foundry has five layers:

1. Blueprints: desired state for managed repositories.
2. Reconciliation: validates desired state and produces a safe plan.
3. Runtime and audit: records plans, writes, logs, artifacts, and cycle summaries.
4. Dashboard: shows repo state, drift, PRs, runs, logs, artifacts, autonomous watch items, and human direction.
5. Completion stewardship: observes open PRs, check results, mergeability, policy limits, and direction priorities so safe work can land instead of accumulating.

The implementation uses FastAPI with SQLite and a React/Vite frontend. Autonomous execution reads active direction items so Garrett can steer priorities without manual gates.

## Runtime completion contract

Completion stewardship is a reusable control loop, not a one-off script. Every cycle should:

1. Snapshot open PRs, required checks, changed-file counts, risky paths, dependency-file changes, branch freshness, and mergeability.
2. Classify each PR as `merge-ready`, `auto-merge-waiting`, `needs-repair`, `superseded`, or `blocked-by-policy`.
3. Prefer landing safe, low-risk, already-reviewed work before creating new feature branches.
4. Fail closed when checks, policy, mergeability, or credential scope are unknown.
5. Write a visible cycle summary and machine-readable artifact for the dashboard.

Local runners may execute completion actions when GitHub-hosted workflow permissions are intentionally limited. GitHub Actions should remain report-first unless repository policy explicitly grants write-capable automation.