# Windows Local Runtime Setup

Repo Foundry expects a local execution workspace at `C:\AgentRuntime`.

## Install Checklist

1. Install GitHub CLI.
2. Install Python 3.11 or newer.
3. Install Node.js 20 or newer.
4. Enable Corepack for pnpm.
5. Install Docker Desktop.
6. Install Playwright browser dependencies after Node setup.
7. Configure a GitHub self-hosted runner only for trusted repositories.

## Workspace

```powershell
New-Item -ItemType Directory -Force C:\AgentRuntime
New-Item -ItemType Directory -Force C:\AgentRuntime\work
New-Item -ItemType Directory -Force C:\AgentRuntime\logs
New-Item -ItemType Directory -Force C:\AgentRuntime\artifacts
```

## GitHub CLI

```powershell
gh auth login
gh auth status
```

Prefer fine-grained tokens when possible. Never commit tokens or runner secrets.

## Self-Hosted Runner Safety

- Use a dedicated Windows account where practical.
- Use labels such as `repo-foundry`, `windows`, and `local`.
- Do not run untrusted public PR code on the local runner.
- Keep runner registration, removal, and service changes logged and visible.
- Keep runner work directories under `C:\AgentRuntime`.

## Playwright

```powershell
cd C:\Users\Garrett\Desktop\AUTOREPO\dashboard\frontend
corepack enable
pnpm install
npx playwright install chromium
```
