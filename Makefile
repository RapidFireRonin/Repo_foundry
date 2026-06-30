.PHONY: setup test build run run-mobile bench agent-report cycle-summary poll-prs merge-pr

setup:
	python -m pip install -e ".[dev]"
	cd dashboard/frontend && corepack enable && pnpm install

test:
	pytest

build:
	cd dashboard/frontend && pnpm run build

run:
	python -m repo_foundry.api

run-mobile:
	REPO_FOUNDRY_API_HOST=0.0.0.0 python -m repo_foundry.api

bench:
	python -m repo_foundry.reconcile plan blueprints/example-repo.yaml --registry registry/repos.yaml

agent-report:
	python -m repo_foundry.reports agent-report

cycle-summary:
	python -m repo_foundry.cycle_summary append --from-sample

poll-prs:
	python -m repo_foundry.pr_monitor RapidFireRonin/Repo_foundry

merge-pr:
	python -m repo_foundry.merge_executor RapidFireRonin/Repo_foundry $(PR)
