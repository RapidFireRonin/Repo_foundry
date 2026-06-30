from repo_foundry.executor import execute_plan
from repo_foundry.github_client import GitHubAuthUnavailable
from repo_foundry.reconcile import build_plan


def test_execute_plan_dry_run_records_commands_without_running() -> None:
    plan = build_plan("blueprints/example-repo.yaml", "registry/repos.yaml")

    result = execute_plan(plan, "blueprints/example-repo.yaml", dry_run=True)

    assert result["dry_run"] is True
    assert any(item["action"] == "create_repo" and item["status"] == "planned" for item in result["results"])


def test_execute_plan_execute_mode_blocks_without_github_credentials(monkeypatch) -> None:
    plan = build_plan("blueprints/example-repo.yaml", "registry/repos.yaml")

    def fail_credentials():
        raise GitHubAuthUnavailable("GitHub CLI is not authenticated.")

    monkeypatch.setattr("repo_foundry.executor.require_github_credentials", fail_credentials)

    result = execute_plan(plan, "blueprints/example-repo.yaml", dry_run=False)

    assert result["dry_run"] is False
    assert result["results"] == [
        {
            "action": "github_credential_preflight",
            "target": "RapidFireRonin/example-managed-repo",
            "dry_run": False,
            "status": "blocked",
            "error": "GitHub CLI is not authenticated.",
            "remediation": "Run `gh auth login` locally or set `REPO_FOUNDRY_GH_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN` in the runtime environment.",
        }
    ]
