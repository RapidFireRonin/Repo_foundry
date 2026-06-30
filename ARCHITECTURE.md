# Architecture

Repo Foundry has five layers:

1. Blueprints: desired state for managed repositories.
2. Reconciliation: validates desired state and produces a safe plan.
3. Runtime and audit: records plans, writes, logs, artifacts, and cycle summaries.
4. Dashboard: shows repo state, drift, PRs, runs, logs, artifacts, autonomous watch items, and human direction.
5. Autonomous completion: observes PR/check state, evaluates merge policy, plans safe completion actions, executes only in explicit live mode, records audit/completion logs, and refreshes dashboard state.

The implementation uses FastAPI with SQLite and a React/Vite frontend. Autonomous execution reads active direction items so Garrett can steer priorities without manual gates.

## Autonomous completion boundary

The completion layer is responsible for turning safe autonomous work into completed outcomes. It must be dry-run-first, policy-driven, fail-closed on unknown states, and dashboard-readable.

The detailed implementation contract lives in `contracts/AUTONOMOUS_COMPLETION_LOOP_CONTRACT.md`. Builders should implement completion work against that contract rather than adding ad hoc merge behavior.
