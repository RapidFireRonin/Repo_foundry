from __future__ import annotations

import argparse
import json
from typing import Any

from repo_foundry.audit import write_audit_event
from repo_foundry.completion_log import append_completion_log
from repo_foundry.completion_policy import PullRequestSnapshot, evaluate_policy, load_policy
from repo_foundry.db import fetch_completion_prs, upsert_completion_pr
from repo_foundry.directions import mark_matching_direction_done
from repo_foundry.github_client import run_gh


def plan_or_merge(repo: str, number: int, execute: bool = False, policy_path: str = "policies/auto-merge.yaml") -> dict[str, Any]:
    row = next((item for item in fetch_completion_prs() if item["number"] == number), None)
    if row is None:
        raise ValueError(f"PR #{number} has not been polled into SQLite.")

    pr = PullRequestSnapshot.model_validate(row["payload"])
    policy = load_policy(policy_path)
    write_audit_event("pre_merge_policy_check", pr.url, pr_number=number, execute=execute)
    decision = evaluate_policy(pr, policy, audit_present=True)
    result: dict[str, Any] = {
        "repo": repo,
        "number": number,
        "execute": execute,
        "decision": decision.model_dump(mode="json"),
        "status": "planned" if decision.allowed else "blocked",
        "command": ["pr", "merge", str(number), "--repo", repo, "--squash", "--delete-branch=false"],
    }

    if decision.allowed and execute:
        completed = run_gh(["pr", "merge", str(number), "--repo", repo, "--squash", "--delete-branch=false"])
        result["merge"] = completed.__dict__
        result["status"] = "merged" if completed.returncode == 0 else "failed"
        append_completion_log(
            pr,
            decision,
            merged=completed.returncode == 0,
            rollback_note=f"Revert the squash merge commit for PR #{number} if rollback is needed.",
        )
        if completed.returncode == 0:
            result["completed_direction"] = mark_matching_direction_done(pr.title)
        row["payload"]["merged"] = completed.returncode == 0
        row["decision"] = decision.model_dump(mode="json")
        upsert_completion_pr(row)

    write_audit_event("post_merge_attempt", pr.url, pr_number=number, result=result)
    return result


def close_superseded(repo: str, number: int, execute: bool = False) -> dict[str, Any]:
    row = next((item for item in fetch_completion_prs() if item["number"] == number), None)
    if row is None:
        raise ValueError(f"PR #{number} has not been polled into SQLite.")
    if not row.get("superseded_by"):
        return {"repo": repo, "number": number, "execute": execute, "status": "not_superseded"}

    body = f"Closing as superseded by PR #{row['superseded_by']} via Repo Foundry autonomous completion policy."
    result: dict[str, Any] = {
        "repo": repo,
        "number": number,
        "execute": execute,
        "status": "planned",
        "comment": body,
    }
    write_audit_event("pre_close_superseded", row["url"], pr_number=number, superseded_by=row["superseded_by"])
    if execute:
        comment = run_gh(["pr", "comment", str(number), "--repo", repo, "--body", body])
        close = run_gh(["pr", "close", str(number), "--repo", repo])
        result["comment_result"] = comment.__dict__
        result["close_result"] = close.__dict__
        result["status"] = "closed" if comment.returncode == 0 and close.returncode == 0 else "failed"
    write_audit_event("post_close_superseded", row["url"], result=result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Safely merge policy-approved PRs.")
    parser.add_argument("repo")
    parser.add_argument("number", type=int)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy", default="policies/auto-merge.yaml")
    parser.add_argument("--close-superseded", action="store_true")
    args = parser.parse_args()
    if args.close_superseded:
        print(json.dumps(close_superseded(args.repo, args.number, args.execute), indent=2))
    else:
        print(json.dumps(plan_or_merge(args.repo, args.number, args.execute, args.policy), indent=2))


if __name__ == "__main__":
    main()
