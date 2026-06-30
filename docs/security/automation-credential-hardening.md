# Automation Credential Hardening

Repo Foundry can run autonomously, but the GitHub credential should stay narrow.

## Current Warning

If Mission Control shows:

```text
Current GitHub token appears broad. Replace with a narrow Repo Foundry automation credential.
```

it means the API process can see a GitHub token hint such as `GH_TOKEN` or `GITHUB_TOKEN`. Repo Foundry never prints the token value.

## Recommended Credential

Use a dedicated GitHub account or fine-grained personal access token for `RapidFireRonin/Repo_foundry`.

Minimum permissions:

- Contents: read/write
- Pull requests: read/write
- Actions: read
- Checks/statuses: read
- Issues: read/write, if agents report to issue #13

Avoid granting:

- `delete_repo`
- broad admin/org/enterprise scopes
- package publishing scopes unless needed
- secret-management scopes until a specific workflow requires them

## Rotate Safely

1. Create a new narrow token in GitHub.
2. Store it on the PC as `REPO_FOUNDRY_GH_TOKEN` or configure `gh auth login`.
3. Restart Repo Foundry services.
4. Run:

```powershell
gh auth status
.\scripts\rf.ps1 health
.\scripts\rf.ps1 pr-status
```

5. Remove the older broad token from user/system environment variables.

## Operating Rules

- Never commit tokens to the repo.
- Never paste tokens into dashboard directions.
- Treat PR titles, issue bodies, comments, and cycle logs as untrusted text.
- Keep destructive operations behind explicit policy and command flags.
- Prefer read-only GitHub Actions plus local PC execution for privileged writes.
