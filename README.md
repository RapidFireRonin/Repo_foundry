# Repo Foundry

Repo Foundry is a local and GitHub-based control plane for visible, directable autonomous repo work. Garrett can choose what gets attention, while scheduled agents, GitHub Actions, and local runners execute, report, and leave readable evidence.

## Principles

- Autonomous by default, directable by Garrett.
- Pull requests for meaningful source changes.
- Dry-run first for GitHub writes.
- Every write action records an audit event.
- Dashboards and markdown summaries explain what happened in plain language.

## Quickstart

```powershell
cd C:\Users\Garrett\Desktop\AUTOREPO
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
cd dashboard\frontend
corepack enable
pnpm install
cd ..\..
python -m repo_foundry.db seed
python -m repo_foundry.api
```

In another terminal:

```powershell
cd C:\Users\Garrett\Desktop\AUTOREPO\dashboard\frontend
pnpm run dev
```

Backend: `http://127.0.0.1:8765`

Frontend: `http://127.0.0.1:5274`

## Common Tasks

```powershell
python -m repo_foundry.blueprints validate blueprints/example-repo.yaml
python -m repo_foundry.reconcile plan blueprints/example-repo.yaml --registry registry/repos.yaml
python -m repo_foundry.reconcile apply blueprints/example-repo.yaml --registry registry/repos.yaml
python -m repo_foundry.reconcile apply blueprints/example-repo.yaml --registry registry/repos.yaml --execute
python -m repo_foundry.directions add "Polish dashboard" "Make the local control plane easier to read" --priority 90
python -m repo_foundry.cycle_summary append --from-sample
python -m repo_foundry.api
```

Windows task wrapper:

```powershell
.\scripts\rf.ps1 setup
.\scripts\rf.ps1 test
.\scripts\rf.ps1 run
.\scripts\rf.ps1 cycle-summary
```

## Autonomous Safety Model

Repo Foundry plans changes before applying them. `reconcile apply` is dry-run unless `--execute` is supplied, so scheduled agents can run safely and intentionally. The default repository visibility is private. Source changes are still PR-based for readability and traceability, but agents do not wait on manual gates before preparing or updating work.

Use directions to steer autonomy:

```powershell
python -m repo_foundry.directions add "Focus repo templates" "Expand generated repo scaffolds and run contracts" --priority 95 --scope global
```

For GitHub tokens, start with least privilege:

- `repo` only for private repo creation and PR work when using classic tokens.
- Fine-grained tokens scoped to the target owner and repositories are preferred.
- Actions and workflow updates should use pull requests.
- Do not store tokens in files. Use environment variables or GitHub secrets.
- For local apply, run `gh auth login` or set a valid `GH_TOKEN`.
- For GitHub Actions apply across repos, set `REPO_FOUNDRY_GH_TOKEN` as a repository secret when the default `github.token` is not broad enough.

See [docs/windows-setup.md](docs/windows-setup.md) and [docs/autonomous-direction.md](docs/autonomous-direction.md).
