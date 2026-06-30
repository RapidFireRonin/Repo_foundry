# GitHub Credential Preflight

`reconcile apply --execute` now checks GitHub credentials before attempting any write action.

## Accepted credential paths

Repo Foundry accepts credentials in this order:

1. `REPO_FOUNDRY_GH_TOKEN`
2. `GH_TOKEN`
3. `GITHUB_TOKEN`
4. An authenticated GitHub CLI session from `gh auth status`

`REPO_FOUNDRY_GH_TOKEN` is preferred for automation because it makes the runtime intent explicit and avoids accidentally reusing a broader local shell token.

## Local setup

Use one of these approaches:

```powershell
gh auth login
```

or:

```powershell
$env:REPO_FOUNDRY_GH_TOKEN = "<token>"
python -m repo_foundry.reconcile apply blueprints/example-repo.yaml --registry registry/repos.yaml --execute
```

## Automation setup

For GitHub Actions or another scheduler, store the token as a secret and expose it as `REPO_FOUNDRY_GH_TOKEN` only for the job that needs repo writes.

## Failure behavior

When credentials are missing, execute mode returns a blocked result before creating repositories, labels, branch protection, branches, commits, or pull requests. The result includes remediation instructions and an audit event, so the dashboard can show the blocker without guessing.

## Safety note

Credential preflight does not make destructive actions safe by itself. Repo Foundry still relies on blueprint policy, dangerous-action flags, audit logging, and PR-based source changes to preserve human visibility.
