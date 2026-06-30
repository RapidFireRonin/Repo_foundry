# Completion Loop

This change adds a bounded PR completion sweeper for Repo Foundry.

Included files:

- `scripts/autonomous_completion.py`
- `policies/autonomous-completion-policy.json`
- `.github/workflows/autonomous-completion.yml`
- `tests/test_autonomous_completion_assets.py`

The workflow is report-only by default. The Python script contains execute-mode support, but the scheduled workflow intentionally runs without writes until the repo owner promotes it from a trusted runner or through the scheduled Reviewer/Debugger agent.

The policy keeps the loop bounded with max merge count, max changed files, max additions/deletions, blocked path rules, check-status requirements, and a narrow exception for dependency-review false positives when dependency files did not change.
