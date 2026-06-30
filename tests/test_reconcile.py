from repo_foundry.reconcile import build_plan


def test_reconcile_plan_detects_missing_repo_and_previews_autonomous_command() -> None:
    plan = build_plan("blueprints/example-repo.yaml", "registry/repos.yaml")

    actions = {action.action: action for action in plan.actions}
    assert actions["create_repo"].dangerous is True
    assert actions["create_repo"].autonomous is True
    assert actions["create_repo"].command_preview[:3] == ["repo", "create", "RapidFireRonin/example-managed-repo"]
    assert "Autonomous mode" in " ".join(plan.visibility_items)


def test_reconcile_plan_opens_prs_for_workflows_and_memory_files() -> None:
    plan = build_plan("blueprints/example-repo.yaml", "registry/repos.yaml")

    pr_actions = [action for action in plan.actions if action.opens_pr]
    assert any(action.action == "open_pr_add_workflow" for action in pr_actions)
    assert any(action.action == "open_pr_add_memory_file" for action in pr_actions)


def test_reconcile_plan_includes_direction_queue() -> None:
    plan = build_plan("blueprints/example-repo.yaml", "registry/repos.yaml")

    assert any("Direction priority" in item for item in plan.visibility_items)
