from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from repo_foundry.audit import write_audit_event
from repo_foundry.blueprints import load_blueprint
from repo_foundry.executor import execute_plan
from repo_foundry.github_client import branch_protection_command, label_create_command, repo_create_command
from repo_foundry.models import PlanAction, ReconcilePlan, RegisteredRepo, Registry


def load_registry(path: str | Path) -> Registry:
    p = Path(path)
    if not p.exists():
        return Registry()
    return Registry.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")) or {})


def find_repo(registry: Registry, owner: str, name: str) -> RegisteredRepo | None:
    return next((repo for repo in registry.repos if repo.owner == owner and repo.name == name), None)


def build_plan(blueprint_path: str | Path, registry_path: str | Path, dry_run: bool = True) -> ReconcilePlan:
    blueprint = load_blueprint(blueprint_path)
    registry = load_registry(registry_path)
    current = find_repo(registry, blueprint.owner, blueprint.name)
    plan = ReconcilePlan(
        blueprint=f"{blueprint.owner}/{blueprint.name}",
        dry_run=dry_run,
        automation_mode=blueprint.automation_mode,
    )

    if current is None or not current.exists:
        plan.actions.append(
            PlanAction(
                action="create_repo",
                target=f"{blueprint.owner}/{blueprint.name}",
                reason="Repository is missing from registry or marked absent.",
                dangerous=True,
                command_preview=repo_create_command(blueprint),
            )
        )

    known_labels = set(current.labels if current else [])
    for label in blueprint.labels:
        if label.name not in known_labels:
            plan.actions.append(
                PlanAction(
                    action="create_label",
                    target=label.name,
                    reason="Required label is missing.",
                    command_preview=label_create_command(blueprint.owner, blueprint.name, label),
                )
            )

    known_workflows = set(current.workflows if current else [])
    for workflow in blueprint.workflows:
        if workflow.path not in known_workflows:
            plan.actions.append(
                PlanAction(
                    action="open_pr_add_workflow",
                    target=workflow.path,
                    reason="Required workflow is missing.",
                    autonomous=True,
                    opens_pr=True,
                )
            )

    known_memory = set(current.memory_files if current else [])
    for memory_file in blueprint.memory_files:
        if memory_file not in known_memory:
            plan.actions.append(
                PlanAction(
                    action="open_pr_add_memory_file",
                    target=memory_file,
                    reason="Required repo memory file is missing.",
                    autonomous=True,
                    opens_pr=True,
                )
            )

    if blueprint.branch_protection_required and not (current and current.branch_protection):
        plan.actions.append(
            PlanAction(
                action="configure_branch_protection",
                target=blueprint.default_branch,
                reason="Main branch protection is required.",
                dangerous=True,
                command_preview=branch_protection_command(blueprint),
            )
        )

    plan.visibility_items.append("Autonomous mode is enabled; actions are not blocked on manual gates.")
    for direction in sorted(registry.directions, key=lambda item: item.priority, reverse=True):
        if direction.status == "active" and direction.scope in ("global", blueprint.name, f"{blueprint.owner}/{blueprint.name}"):
            plan.visibility_items.append(
                f"Direction priority {direction.priority}: {direction.title} - {direction.desired_outcome}"
            )
    if any(action.dangerous for action in plan.actions):
        plan.visibility_items.append("High-impact actions are highlighted in logs and dashboard before and after execution.")
    if any(action.opens_pr for action in plan.actions):
        plan.visibility_items.append("Repository file changes are queued for PR creation by the GitHub adapter.")

    write_audit_event("reconcile_plan", plan.blueprint, dry_run=dry_run, action_count=len(plan.actions))
    return plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Plan or apply repository reconciliation.")
    sub = parser.add_subparsers(dest="command", required=True)
    plan_parser = sub.add_parser("plan")
    plan_parser.add_argument("blueprint")
    plan_parser.add_argument("--registry", default="registry/repos.yaml")
    plan_parser.add_argument("--json", action="store_true")
    apply_parser = sub.add_parser("apply")
    apply_parser.add_argument("blueprint")
    apply_parser.add_argument("--registry", default="registry/repos.yaml")
    apply_parser.add_argument("--execute", action="store_true", help="Run in autonomous write mode instead of dry-run.")
    args = parser.parse_args()

    if args.command == "plan":
        plan = build_plan(args.blueprint, args.registry, dry_run=True)
        if args.json:
            print(plan.model_dump_json(indent=2))
        else:
            print(json.dumps(plan.model_dump(mode="json"), indent=2))
    if args.command == "apply":
        dry_run = not args.execute
        plan = build_plan(args.blueprint, args.registry, dry_run=dry_run)
        result = execute_plan(plan, args.blueprint, dry_run=dry_run)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
