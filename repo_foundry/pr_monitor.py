from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from typing import Any

from repo_foundry.audit import write_audit_event
from repo_foundry.completion_policy import CheckStatus, PullRequestSnapshot, evaluate_policy, load_policy
from repo_foundry.db import fetch_completion_prs, upsert_completion_pr
from repo_foundry.github_client import run_gh


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


def poll_prs(repo: str, policy_path: str = "policies/auto-merge.yaml") -> list[dict[str, Any]]:
    policy = load_policy(policy_path)
    stored: list[dict[str, Any]] = []
    for pr in annotate_superseded(fetch_open_prs(repo)):
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
    write_audit_event("pr_poll", repo, count=len(stored))
    return stored


def main() -> None:
    parser = argparse.ArgumentParser(description="Poll GitHub PRs for autonomous completion.")
    parser.add_argument("repo")
    parser.add_argument("--policy", default="policies/auto-merge.yaml")
    args = parser.parse_args()
    print(json.dumps(poll_prs(args.repo, args.policy), indent=2))


if __name__ == "__main__":
    main()
