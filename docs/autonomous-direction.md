# Autonomous Direction

Repo Foundry is autonomous by default, but Garrett can direct what it works on.

## Default Flow

1. Garrett adds or edits direction items in `registry/repos.yaml` or with `python -m repo_foundry.directions add`.
2. Reconciliation reads blueprints, registry state, and active directions.
3. Agents prioritize high-priority active directions.
4. Source changes are prepared through PR-oriented artifacts and adapters.
5. GitHub writes and local actions record audit events.
6. The dashboard and hourly cycle log explain what happened, what changed, what failed, and what should happen next.

## Direction Fields

- `title`: short instruction.
- `priority`: `0` to `100`; higher runs first.
- `scope`: `global`, repo name, or `owner/repo`.
- `desired_outcome`: what success looks like.
- `avoid`: boundaries or anti-goals.
- `status`: usually `active`.

## Autonomous Execution

`python -m repo_foundry.reconcile apply ...` runs as a dry-run by default. Add `--execute` when the scheduled or local runner is intentionally allowed to perform GitHub writes.

Human-friendly visibility remains mandatory: audit logs, artifacts, dashboard panels, and hourly cycle summaries should be readable without digging through raw runner logs.
