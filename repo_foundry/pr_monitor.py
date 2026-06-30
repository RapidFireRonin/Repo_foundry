from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repo_foundry.audit import write_audit_event
from repo_foundry.completion_policy import CheckStatus, PullRequestSnapshot, evaluate_policy, load_policy
from repo_foundry.db import fetch_completion_prs, upsert_completion_pr
from repo_foundry.github_client import run_gh

SNAPSHOT_SCHEMA_VERSION = "pr-status-snapshot/v1"


def fetch_open_prs(repo: str) -> list[PullRequestSnapshot]:
    result = run_gh([
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--json",
        "number,title,url,headRefName,baseRefName,mergeable,changedFiles,additions,deletions,files,statusCheckRollup,updatedAt,headRefOid",
    ])
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    return [snapshot_from_gh(item) for item in json.loads(result.stdout or "[]")]


def snapshot_from_gh(item: dict[str, Any]) -> PullRequestSnapshot:
    files = [entry["path"] for entry in item.get("files", []) if entry.get("path")]
    checks = [
        CheckStatus(
            name=entry.get("name") or entry.get("workflowName") or entry.get("context") or "unknown",
            status=entry.get("status") or "UNKNOWN",
            conclusion=entry.get("conclusion"),
        )
        for entry in item.get("statusCheckRollup", [])
    ]
    updated = item.get("updatedAt")
    updated_at = datetime.fromisoformat(updated.replace("Z", "+00:00")) if updated else datetime.now(timezone.utc)
    return PullRequestSnapshot(
        number=item["number"],
        title=item["title"],
        url=item.get("url", ""),
        branch=item.get("headRefName", ""),
        base_branch=item.get("baseRefName", "main"),
        mergeable=item.get("mergeable"),
        changed_files=item.get("changedFiles", 0),
        additions=item.get("additions", 0),
        deletions=item.get("deletions", 0),
        files=files,
        checks=checks,
        updated_at=updated_at,
        commit_sha=item.get("headRefOid", ""),
    )


def failed_check_names(pr: PullRequestSnapshot) -> list[str]:
    return [check.name for check in pr.checks if check.is_failure]


def unknown_check_names(pr: PullRequestSnapshot) -> list[str]:
    return [check.name for check in pr.checks if not check.is_success and not check.is_failure]


def is_stale(pr: PullRequestSnapshot, stale_after_hours: int) -> bool:
    age = datetime.now(timezone.utc) - pr.updated_at
    return age.total_seconds() > stale_after_hours * 3600


def annotate_superseded(prs: list[PullRequestSnapshot]) -> list[PullRequestSnapshot]:
    by_title: dict[str, PullRequestSnapshot] = {}
    for pr in sorted(prs, key=lambda item: item.updated_at, reverse=True):
        if pr.title in by_title:
            pr.superseded_by = by_title[pr.title].number
        else:
            by_title[pr.title] = pr
    return prs


def normalize_check_value(value: str | None) -> str | None:
    return value.lower() if isinstance(value, str) else value


def normalize_mergeable(value: str | bool | None) -> bool | None:
    if isinstance(value, bool) or value is None:
        return value
    normalized = value.upper()
    if normalized in {"TRUE", "MERGEABLE"}:
        return True
    if normalized in {"FALSE", "CONFLICTING", "DIRTY", "BLOCKED"}:
        return False
    return None


def checks_summary(pr: PullRequestSnapshot) -> dict[str, Any]:
    failing = failed_check_names(pr)
    unknown = unknown_check_names(pr)
    all_success = bool(pr.checks) and not failing and not unknown
    status = "completed" if pr.checks and not unknown else "unknown"
    conclusion: str | None = "success" if all_success else "failure" if failing else None
    return {
        "status": status,
        "conclusion": conclusion,
        "total_count": len(pr.checks),
        "failing_count": len(failing),
        "unknown_count": len(unknown),
        "runs": [
            {
                "name": check.name,
                "status": normalize_check_value(check.status) or "unknown",
                "conclusion": normalize_check_value(check.conclusion),
                "url": None,
            }
            for check in pr.checks
        ],
    }


def policy_decision_value(pr: PullRequestSnapshot, allowed: bool) -> str:
    if allowed:
        return "eligible"
    if normalize_mergeable(pr.mergeable) is None or unknown_check_names(pr):
        return "watch"
    guarded_path_prefixes = (".github/", "policies/", "secrets/", "scripts/")
    if any(path.startswith(guarded_path_prefixes) for path in pr.files):
        return "manual_review_required"
    return "blocked"


def status_snapshot_from_pr(repo: str, pr: PullRequestSnapshot, policy_path: str = "policies/auto-merge.yaml") -> dict[str, Any]:
    policy = load_policy(policy_path)
    decision = evaluate_policy(pr, policy, audit_present=True)
    reasons = decision.reasons or ["all policy gates passed"]
    return {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "repository": repo,
        "pull_request": pr.number,
        "display_url": pr.url,
        "head_sha": pr.commit_sha,
        "base_branch": pr.base_branch,
        "head_branch": pr.branch,
        "mergeable": normalize_mergeable(pr.mergeable),
        "merge_state": str(pr.mergeable),
        "merged": pr.state.upper() == "MERGED",
        "merge_sha": None,
        "checks": checks_summary(pr),
        "policy_decision": policy_decision_value(pr, decision.allowed),
        "risk_note": "; ".join(reasons),
        "rollback_note": "Close or rebuild the PR from current main if checks, mergeability, or policy state changes.",
        "linked_task": None,
        "direction_item": None,
    }


def snapshot_artifact_path(output_dir: str | Path, repo: str, pr: PullRequestSnapshot) -> Path:
    safe_repo = repo.replace("/", "_")
    head_sha = pr.commit_sha or "unknown-head"
    return Path(output_dir) / safe_repo / f"pr-{pr.number}" / f"{head_sha}.json"


def write_snapshot_artifacts(repo: str, prs: list[PullRequestSnapshot], output_dir: str | Path, policy_path: str) -> list[Path]:
    written: list[Path] = []
    for pr in prs:
        path = snapshot_artifact_path(output_dir, repo, pr)
        path.parent.mkdir(parents=True, exist_ok=True)
        snapshot = status_snapshot_from_pr(repo, pr, policy_path)
        path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        written.append(path)
    write_audit_event("pr_status_snapshot_write", repo, count=len(written), output_dir=str(output_dir))
    return written


def poll_prs(repo: str, policy_path: str = "policies/auto-merge.yaml", snapshot_output_dir: str | None = None) -> list[dict[str, Any]]:
    policy = load_policy(policy_path)
    stored: list[dict[str, Any]] = []
    prs = annotate_superseded(fetch_open_prs(repo))
    for pr in prs:
        decision = evaluate_policy(pr, policy, audit_present=True)
        item = {
            "number": pr.number,
            "title": pr.title,
            "url": pr.url,
            "branch": pr.branch,
            "mergeable": pr.mergeable,
            "check_status": "failed" if failed_check_names(pr) else "ready" if decision.allowed else "blocked",
            "failed_checks": failed_check_names(pr),
            "stale": is_stale(pr, policy.stale_after_hours),
            "superseded_by": pr.superseded_by,
            "decision": decision.model_dump(mode="json"),
            "payload": pr.model_dump(mode="json"),
        }
        upsert_completion_pr(item)
        stored.append(item)
    if snapshot_output_dir:
        write_snapshot_artifacts(repo, prs, snapshot_output_dir, policy_path)
    write_audit_event("pr_poll", repo, count=len(stored), snapshot_output_dir=snapshot_output_dir)
    return stored


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll GitHub PRs for autonomous completion.")
    parser.add_argument("repo")
    parser.add_argument("--policy", default="policies/auto-merge.yaml")
    parser.add_argument(
        "--write-snapshots",
        metavar="DIR",
        help="Write schema-compatible PR status snapshots under DIR for dashboard/artifact visibility.",
    )
    args = parser.parse_args()
    print(json.dumps(poll_prs(args.repo, args.policy, args.write_snapshots), indent=2))


if __name__ == "__main__":
    main()
