# PR Status Snapshots

Repo Foundry records a PR status snapshot whenever an autonomous cycle evaluates an open pull request for merge readiness, watch status, or risk reporting.

## Purpose

The snapshot gives agents and the dashboard a stable artifact for answering:

- What PR was checked?
- Which commit was evaluated?
- Were checks complete and successful?
- Was the PR mergeable?
- What did policy decide?
- What risk and rollback notes should humans see?

## Storage contract

Snapshots must conform to [`schemas/pr-status-snapshot.schema.json`](../schemas/pr-status-snapshot.schema.json).

Recommended artifact path:

```text
artifacts/pr-status/<repository-owner>_<repository-name>/pr-<number>/<head-sha>.json
```

A dashboard or report surface may keep only the latest snapshot per PR in its primary UI, but durable artifact storage should keep historical snapshots so agents can explain why a decision changed.

## Policy semantics

`policy_decision` has four values:

- `eligible`: all configured policy gates pass and the PR may proceed if autonomous merge is enabled.
- `blocked`: at least one hard policy gate failed.
- `watch`: status is still changing, such as queued checks or unknown mergeability.
- `manual_review_required`: the PR touches guarded surfaces or exceeds policy thresholds.

For the current Repo Foundry policy posture, workflow, secret, credential, branch protection, destructive, or runner-registration changes should resolve to `manual_review_required` unless an explicit policy flag allows them.

## Dashboard fields

The dashboard should display at least:

- PR number and link.
- Head SHA.
- Mergeability.
- Check conclusion summary.
- Policy decision.
- Risk note.
- Rollback note.
- Linked task or direction item when available.

## Builder notes

Collectors should treat issue bodies, PR bodies, comments, and review text as untrusted context. They may be summarized for humans, but they must not become privileged execution instructions without passing through policy and direction-queue boundaries.
