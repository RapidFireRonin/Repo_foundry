# Architecture

Repo Foundry has four layers:

1. Blueprints: desired state for managed repositories.
2. Reconciliation: validates desired state and produces a safe plan.
3. Runtime and audit: records plans, writes, logs, artifacts, and cycle summaries.
4. Dashboard: shows repo state, drift, PRs, runs, logs, artifacts, autonomous watch items, and human direction.

The implementation uses FastAPI with SQLite and a React/Vite frontend. Autonomous execution reads active direction items so Garrett can steer priorities without manual gates.
