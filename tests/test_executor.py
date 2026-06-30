from repo_foundry.executor import execute_plan
from repo_foundry.reconcile import build_plan


def test_execute_plan_dry_run_records_commands_without_running() -> None:
    plan = build_plan("blueprints/example-repo.yaml", "registry/repos.yaml")

    result = execute_plan(plan, "blueprints/example-repo.yaml", dry_run=True)

    assert result["dry_run"] is True
    assert any(item["action"] == "create_repo" and item["status"] == "planned" for item in result["results"])
