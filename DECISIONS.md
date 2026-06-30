# Decisions

## 2026-06-30

- Use dry-run reconciliation by default.
- Use FastAPI, SQLite, and React/Vite for the local dashboard.
- Use autonomous execution with a human direction queue and visible audit trails.
- Keep all meaningful changes PR-based.
- Add completion stewardship as a first-class architecture layer so autonomous agents prioritize landing safe work, repairing blocked PRs, and logging cycle status before opening unrelated new feature work.
- Keep hosted completion workflows report-first unless repository policy explicitly authorizes write-capable automation; use trusted local runners for repository maintenance actions when hosted workflow permissions are intentionally constrained.