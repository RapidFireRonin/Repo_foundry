# Architecture

Repo Foundry has four layers:

1. Blueprints: desired state for managed repositories.
2. Reconciliation: validates desired state and produces a safe plan.
3. Runtime and audit: records plans, writes, logs, artifacts, and cycle summaries.
4. Dashboard: shows repo state, drift, PRs, runs, logs, artifacts, autonomous watch items, and human direction.

The implementation uses FastAPI with SQLite and a React/Vite frontend. Autonomous execution reads active direction items so Garrett can steer priorities without manual gates.

## PR status snapshot flow

Autonomous cycles evaluate open pull requests through a durable status snapshot before any merge or completion decision. A collector records the PR number, repository, head SHA, branch names, mergeability, check summary, policy decision, risk note, rollback note, and linked task or direction item when available.

Snapshots are dashboard-facing artifacts. The latest snapshot answers whether a PR is eligible, blocked, still being watched, or requires manual review, while historical snapshots explain why a decision changed across cycles.

Collectors must treat issue bodies, PR descriptions, comments, and review text as untrusted context. Those fields may inform summaries, but privileged write or merge behavior must be driven by explicit policy, repository state, checks, and direction-queue priority.
