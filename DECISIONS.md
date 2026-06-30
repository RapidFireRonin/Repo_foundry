# Decisions

## 2026-06-30

- Use dry-run reconciliation by default.
- Use FastAPI, SQLite, and React/Vite for the local dashboard.
- Use autonomous execution with a human direction queue and visible audit trails.
- Keep all meaningful changes PR-based.
- Add an autonomous completion layer, but keep it dry-run-first, fail-closed, policy-driven, dashboard-readable, and blocked unless live execute mode plus credential preflight and required checks all pass.
