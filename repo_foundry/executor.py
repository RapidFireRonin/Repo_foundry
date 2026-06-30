from __future__ import annotations

import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repo_foundry.audit import write_audit_event
from repo_foundry.blueprints import load_blueprint
from repo_foundry.github_client import (
    GitUnavailable,
    GitHubAuthUnavailable,
    GitHubCliUnavailable,
    branch_protection_payload,
    branch_protection_command,
    label_create_command,
    pr_create_command,
    repo_create_command,
    require_github_credentials,
    run_git,
    run_gh,
)
from repo_foundry.models import PlanAction, ReconcilePlan, RepoBlueprint, repo_root
from repo_foundry.templates import MEMORY_FILE_TEMPLATES, workflow_template


def execute_plan(plan: ReconcilePlan, blueprint_path: str | Path, dry_run: bool = True) -> dict[str, Any]:
    blueprint = load_blueprint(blueprint_path)
    results: list[dict[str, Any]] = []
    pr_actions: list[PlanAction] = []

    if not dry_run:
        try:
            credential_status = require_github_credentials()
            write_audit_event(
                "github_credential_preflight",
                plan.blueprint,
                available=True,
                method=credential_status.method,
            )
        except (GitHubAuthUnavailable, GitHubCliUnavailable) as exc:
            result = {
                "action": "github_credential_preflight",
                "target": plan.blueprint,
                "dry_run": dry_run,
                "status": "blocked",
                "error": str(exc),
                "remediation": "Run `gh auth login` locally or set `REPO_FOUNDRY_GH_TOKEN`, `GH_TOKEN`, or `GITHUB_TOKEN` in the runtime environment.",
            }
            write_audit_event("github_credential_preflight", plan.blueprint, available=False, result=result)
            return {"blueprint": plan.blueprint, "dry_run": dry_run, "results": [result]}

    for action in plan.actions:
        result: dict[str, Any] = {
            "action": action.action,
            "target": action.target,
            "dry_run": dry_run,
            "status": "planned" if dry_run else "skipped",
        }

        try:
            if action.action == "create_repo":
                command = repo_create_command(blueprint)
                result["command"] = command
                if not dry_run:
                    completed = run_gh(command)
                    result.update(completed.__dict__)
                    result["status"] = "complete" if completed.returncode == 0 else "failed"
            elif action.action == "create_label":
                label = next(item for item in blueprint.labels if item.name == action.target)
                command = label_create_command(blueprint.owner, blueprint.name, label)
                result["command"] = command
                if not dry_run:
                    completed = run_gh(command)
                    result.update(completed.__dict__)
                    result["status"] = "complete" if completed.returncode == 0 else "failed"
            elif action.action == "configure_branch_protection":
                command = branch_protection_command(blueprint)
                result["command"] = command
                result["payload"] = branch_protection_payload()
                if not dry_run:
                    completed = run_gh(command, input_text=branch_protection_payload())
                    result.update(completed.__dict__)
                    result["status"] = "complete" if completed.returncode == 0 else "failed"
            elif action.opens_pr:
                pr_actions.append(action)
                result["status"] = "planned" if dry_run else "batched-for-pr"
                result["artifact"] = write_pr_change_artifact(plan.blueprint, action.action, action.target)
            else:
                result["status"] = "unknown-action"
        except (GitHubCliUnavailable, GitUnavailable, StopIteration) as exc:
            result["status"] = "failed"
            result["error"] = str(exc)

        write_audit_event("execute_action", action.target, planned_action=action.action, result=result)
        results.append(result)

    if pr_actions:
        pr_result = apply_pr_actions(blueprint, pr_actions, dry_run=dry_run)
        write_audit_event("execute_pr_batch", plan.blueprint, result=pr_result)
        results.append(pr_result)

    return {"blueprint": plan.blueprint, "dry_run": dry_run, "results": results}


def write_pr_change_artifact(repo_name: str, action: str, target: str) -> str:
    safe_repo = repo_name.replace("/", "__")
    artifact_dir = repo_root() / "artifacts" / "queued-pr-changes" / safe_repo
    artifact_dir.mkdir(parents=True, exist_ok=True)
    target_name = target.replace("/", "__").replace("\\", "__")
    path = artifact_dir / f"{action}__{target_name}.md"
    path.write_text(
        f"# Queued PR Change\n\n"
        f"- Repository: `{repo_name}`\n"
        f"- Action: `{action}`\n"
        f"- Target: `{target}`\n"
        f"- Mode: autonomous\n\n"
        "This artifact records a repo file change that should be applied by the GitHub PR adapter.\n",
        encoding="utf-8",
    )
    return str(path)


def apply_pr_actions(blueprint: RepoBlueprint, actions: list[PlanAction], dry_run: bool = True) -> dict[str, Any]:
    repo = f"{blueprint.owner}/{blueprint.name}"
    branch = f"repo-foundry/autonomous-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    result: dict[str, Any] = {
        "action": "open_or_update_pr",
        "target": repo,
        "branch": branch,
        "dry_run": dry_run,
        "planned_files": [action.target for action in actions],
        "status": "planned" if dry_run else "running",
    }

    if dry_run:
        return result

    with tempfile.TemporaryDirectory(prefix="repo-foundry-") as tmp:
        checkout = Path(tmp) / blueprint.name
        clone = run_gh(["repo", "clone", repo, str(checkout), "--", "--depth", "1"])
        result["clone"] = clone.__dict__
        if clone.returncode != 0:
            result["status"] = "failed"
            return result

        checkout_branch = run_git(["checkout", "-b", branch], cwd=checkout)
        result["checkout_branch"] = checkout_branch.__dict__
        if checkout_branch.returncode != 0:
            result["status"] = "failed"
            return result

        written = materialize_pr_actions(checkout, blueprint, actions)
        result["written_files"] = written

        status = run_git(["status", "--short"], cwd=checkout)
        result["git_status"] = status.__dict__
        if not status.stdout.strip():
            result["status"] = "no_changes"
            return result

        add = run_git(["add", "."], cwd=checkout)
        commit = run_git(["commit", "-m", "chore: apply Repo Foundry desired state"], cwd=checkout)
        push = run_git(["push", "-u", "origin", branch], cwd=checkout)
        result["add"] = add.__dict__
        result["commit"] = commit.__dict__
        result["push"] = push.__dict__
        if any(step.returncode != 0 for step in (add, commit, push)):
            result["status"] = "failed"
            return result

        body = (
            "Repo Foundry applied desired-state files autonomously.\n\n"
            "Changed files:\n"
            + "\n".join(f"- `{path}`" for path in written)
            + "\n\nLogs and artifacts are recorded by Repo Foundry."
        )
        pr = run_gh(pr_create_command(repo, branch, "chore: apply Repo Foundry desired state", body))
        result["pr"] = pr.__dict__
        result["status"] = "complete" if pr.returncode == 0 else "failed"
        if pr.stdout:
            result["url"] = pr.stdout.splitlines()[-1]
        return result


def materialize_pr_actions(checkout: Path, blueprint: RepoBlueprint, actions: list[PlanAction]) -> list[str]:
    written: list[str] = []
    workflow_by_path = {workflow.path: workflow for workflow in blueprint.workflows}
    for action in actions:
        relative = Path(action.target)
        target = checkout / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if action.action == "open_pr_add_workflow":
            content = workflow_template(workflow_by_path[action.target])
        elif action.action == "open_pr_add_memory_file":
            content = MEMORY_FILE_TEMPLATES.get(action.target, f"# {action.target}\n\nManaged by Repo Foundry.\n")
        else:
            continue
        if not target.exists() or target.read_text(encoding="utf-8") != content:
            target.write_text(content, encoding="utf-8")
            written.append(action.target)
    return written
