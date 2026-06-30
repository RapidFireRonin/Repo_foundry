.PHONY: setup test build run bench agent-report cycle-summary

setup:
	python -m pip install -e ".[dev]"
	cd dashboard/frontend && corepack enable && pnpm install

test:
	pytest

build:
	cd dashboard/frontend && pnpm run build

run:
	python -m repo_foundry.api

bench:
	python -m repo_foundry.reconcile plan blueprints/example-repo.yaml --registry registry/repos.yaml

agent-report:
	python -m repo_foundry.reports agent-report

cycle-summary:
	python -m repo_foundry.cycle_summary append --from-sample
