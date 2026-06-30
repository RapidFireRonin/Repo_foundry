from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repo_foundry.github_client import GitHubCliUnavailable, GitUnavailable, run_gh, run_git
from repo_foundry.models import repo_root


AGENT_ROLES = [
    "Founder/Strategist",
    "Architect",
    "Builder",
    "Reviewer/Debugger",
    "Research Scout",
]


def _degraded(message: str) -> dict[str, Any]:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "degraded": True,
        "summary": f"Live GitHub activity degraded: {message}",
        "recent_runs": [],
        "recent_merged_prs": [],
        "recent_commits": [],
        "agent_lanes": _empty_lanes("No live activity available yet."),
        "quality_verdicts": [],
    }


def _empty_lanes(message: str) -> list[dict[str, Any]]:
    return [{"role": role, "status": "waiting", "summary": message, "evidence": [], "next_action": "Wait for the next scheduled cycle or add a direction."} for role in AGENT_ROLES]


def _run_gh_json(args: list[str]) -> list[dict[str, Any]]:
    result = run_gh(args)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "GitHub CLI command failed.")
    return json.loads(result.stdout or "[]")


def _recent_commits(limit: int = 8) -> list[dict[str, Any]]:
    try:
        result = run_git(["log", f"--max-count={limit}", "--pretty=format:%h%x09%ct%x09%s"], cwd=repo_root())
    except GitUnavailable:
        return []
    if result.returncode != 0:
        return []
    commits: list[dict[str, Any]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\t", 2)
        if len(parts) != 3:
            continue
        sha, epoch, subject = parts
        commits.append({
            "sha": sha,
            "timestamp": datetime.fromtimestamp(int(epoch), timezone.utc).isoformat(),
            "title": subject,
            "verdict": "Landed on main" if "(#" in subject else "Local commit history",
        })
    return commits


def _lane_from_cycle(role: str, cycle_body: str, fallback: str) -> dict[str, Any]:
    marker = f"**{role} activity:**"
    for line in cycle_body.splitlines():
        if line.startswith(marker):
            summary = line.removeprefix(marker).strip()
            return {
                "role": role,
                "status": "reported",
                "summary": summary or fallback,
                "evidence": ["docs/agent-cycle-log.md"],
                "next_action": "Compare this report against recent PRs, checks, and artifacts.",
            }
    return {"role": role, "status": "waiting", "summary": fallback, "evidence": [], "next_action": "Await the next cycle summary."}


def collect_agent_activity(repo: str = "RapidFireRonin/Repo_foundry", cycle: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        runs = _run_gh_json([
            "run",
            "list",
            "--repo",
            repo,
            "--limit",
            "12",
            "--json",
            "databaseId,workflowName,status,conclusion,createdAt,updatedAt,headBranch,event,url",
        ])
        merged = _run_gh_json([
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "merged",
            "--limit",
            "8",
            "--json",
            "number,title,url,mergedAt,headRefName,baseRefName",
        ])
    except (GitHubCliUnavailable, RuntimeError, subprocess.SubprocessError) as exc:
        return _degraded(str(exc))

    commits = _recent_commits()
    cycle_body = str((cycle or {}).get("body") or "")
    fallback = "No explicit role report in the latest cycle summary."
    lanes = [_lane_from_cycle(role, cycle_body, fallback) for role in AGENT_ROLES]

    quality_verdicts: list[dict[str, Any]] = []
    for pr in merged[:5]:
        quality_verdicts.append({
            "title": f"#{pr.get('number')} {pr.get('title')}",
            "status": "landed",
            "verdict": "Merged to main. Check workflow status and dashboard evidence for quality.",
            "evidence": [pr.get("url")],
            "timestamp": pr.get("mergedAt"),
        })
    for run in runs[:6]:
        quality_verdicts.append({
            "title": run.get("workflowName") or "Workflow run",
            "status": run.get("conclusion") or run.get("status") or "unknown",
            "verdict": f"{run.get('event')} on {run.get('headBranch')} finished as {run.get('conclusion') or run.get('status')}.",
            "evidence": [run.get("url")],
            "timestamp": run.get("updatedAt"),
        })

    failures = [run for run in runs if run.get("conclusion") not in (None, "success") and run.get("status") == "completed"]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "degraded": False,
        "summary": "Recent GitHub activity is visible." if not failures else f"{len(failures)} recent workflow run(s) need attention.",
        "recent_runs": runs,
        "recent_merged_prs": merged,
        "recent_commits": commits,
        "agent_lanes": lanes,
        "quality_verdicts": quality_verdicts,
    }
