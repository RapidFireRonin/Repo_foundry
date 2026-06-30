# Autonomous Completion Loop Contract

## Purpose

Repo Foundry is autonomous-by-default, but autonomous work is only valuable when it can be safely completed. This contract defines the architecture boundary for moving from "agents open PRs" to "agents finish safe work end-to-end" without losing human visibility, reversibility, or policy control.

The completion loop must remain dry-run-first. Live merges require explicit execute mode, a policy pass, a known PR/check state, and a durable audit trail.

## Loop stages

Every autonomous completion cycle has these stages:

1. **Observe**
   - Read open PRs, issues, direction items, recent cycle logs, and workflow/check state.
   - Store a normalized snapshot in the runtime database.
   - Mark data freshness and source timestamps.

2. **Classify**
   - Classify each PR as ready, blocked, stale, superseded, unsafe, unknown, or human-direction-required.
   - Treat unknown mergeability, unknown checks, missing diff metadata, and stale snapshots as blocked.

3. **Plan**
   - Produce a merge or closure plan in dry-run mode.
   - Explain every allow/deny decision in dashboard-readable language.
   - Link decisions to policy rule IDs.

4. **Execute**
   - Only run when `--execute` is explicitly enabled and credentials pass preflight.
   - Merge only policy-allowed PRs with clean mergeability and successful required checks.
   - Prefer squash merge unless the policy says otherwise.
   - Never force-push, rewrite history, bypass checks, or merge unknown states.

5. **Record**
   - Write audit events before and after every live action.
   - Append a human-readable completion entry to the cycle log.
   - Record PR URL, head SHA, merge SHA, policy result, check result, risk level, and rollback note.

6. **Refresh**
   - Refresh dashboard state immediately after any live action.
   - Mark linked direction items completed only after merge confirmation.
   - Surface the next recommended completion action.

## Required data model

The runtime should expose a normalized `completion_candidates` view or equivalent model with:

- PR number and URL.
- Title.
- Author.
- Base branch.
- Head branch and head SHA.
- Mergeable state.
- Review state if available.
- Required checks and latest conclusions.
- Changed file count, additions, deletions, and blocked path matches.
- Linked issue or direction item IDs.
- Policy decision: allow, deny, or unknown.
- Blocking reasons.
- Next recommended action.
- Snapshot timestamp and freshness status.

## Policy requirements

The completion policy must support:

- Allowed base branches.
- Allowed head branch patterns.
- Required successful checks.
- Maximum changed files.
- Maximum additions and deletions.
- Blocked paths.
- Blocked operations and dangerous keywords.
- Required audit event types.
- Merge method.
- Staleness timeout for PR/check snapshots.
- Optional labels that require human direction.

A policy miss, parse failure, missing rule, or unknown field must fail closed.

## Dashboard contract

The dashboard must include an Autonomous Completion surface with:

- Ready to merge.
- Blocked by policy.
- Blocked by checks.
- Unknown/stale state.
- Superseded or duplicate work.
- Recently completed work.
- Dry-run versus execute status.
- Last refresh time.
- Next recommended action.

Each row must include enough detail for Garrett to override priorities through the direction queue without editing code or logs.

## Audit contract

Every autonomous completion attempt must emit audit events for:

- `completion_observed`
- `completion_policy_evaluated`
- `completion_plan_created`
- `completion_execute_blocked`
- `completion_merge_started`
- `completion_merge_completed`
- `completion_merge_failed`
- `completion_log_written`

Audit events must include the actor role, PR number, head SHA, policy version, result, and reason list.

## Safety defaults

The completion loop must never:

- Merge with failing, pending, missing, stale, or unknown required checks.
- Merge with unknown `mergeable` state.
- Merge changes to secrets, authentication, workflow permissions, policy files, or destructive scripts unless the policy explicitly allows that category.
- Close a PR as superseded without linking the replacement PR or issue.
- Treat a model-generated summary as authoritative over GitHub API state.
- Require human approval for normal safe work, but it must preserve human override and visibility.

## Builder acceptance criteria

A Builder implementation is contract-complete when it adds:

- Policy parser and fail-closed evaluator.
- PR/check snapshot ingestion.
- Dry-run completion planner.
- Execute-mode merge function behind credential preflight.
- Audit events and cycle-log append.
- Dashboard panel backed by stored state.
- Tests for allowed merge, failed checks, unknown checks, blocked paths, stale snapshots, oversized PRs, missing policy, and successful dry-run planning.
