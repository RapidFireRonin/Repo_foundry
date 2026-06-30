# Autonomous Completion Loop v1 research note

## Purpose

Repo Foundry can already coordinate scheduled roles that open PRs and diagnose failures. The next system unlock is completion: safely deciding when a PR can move from open work to merged work without losing human visibility or directability.

## Key opportunity

Build a policy-gated completion loop:

```text
pick task -> implement -> test -> open/update PR -> poll status -> evaluate policy -> merge or block -> log completion -> select next task
```

## Guardrails from current research

### Agentic workflow injection

Agentic GitHub workflows should treat issue bodies, PR descriptions, comments, and event payload fields as untrusted until classified and sanitized. Completion jobs should not allow untrusted event text to become privileged agent prompts or shell commands.

Practical rule for this repo:

- Privileged completion jobs operate from repo-authored policy files, PR metadata, check status, and explicit audit records.
- PR/comment text can be summarized for humans, but it must not directly instruct merge/write behavior.
- Any shell use of GitHub context needs quoting/sanitization helpers.

Source: https://arxiv.org/abs/2605.07135

### Least-privilege GitHub Actions

Merge/check automation should avoid broad default permissions. Read-only jobs should explicitly use read-only permissions, and write-capable jobs should be isolated, audited, and policy-gated.

Practical rule for this repo:

- Default workflows to `permissions: contents: read`.
- Isolate write steps into jobs that request only the required permissions.
- Treat workflow file edits, credential docs, policy files, and local-runner hooks as higher-risk paths.

Source: https://arxiv.org/abs/2512.11602

## Proposed policy surface

Create `policies/autonomous-completion-policy.yml` with:

- version
- allowed branch patterns
- required checks
- max changed files
- max additions/deletions
- blocked paths
- sensitive paths requiring human review
- merge method preference
- stale PR rules
- superseded PR rules
- audit requirements

## Proposed modules

- `repo_foundry/completion_policy.py`
- `repo_foundry/pr_status.py`
- `repo_foundry/merge_planner.py`
- `repo_foundry/completion_log.py`
- `tests/test_completion_policy.py`
- `tests/test_merge_planner.py`

## Safe first PR

Do not implement live merging first. Implement policy parsing, fixture-backed PR status models, dry-run merge planning, and completion log rendering first. Live merge execution should be a later PR after tests and dashboard visibility exist.
