from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repo_foundry.github_client import GitHubCliUnavailable, run_gh
from repo_foundry.models import repo_root


DEPENDENCY_FILES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "requirements.txt",
    "pyproject.toml",
    "poetry.lock",
    "Pipfile",
    "Pipfile.lock",
}


def _check_name(check: dict[str, Any]) -> str:
    return check.get("name") or check.get("workflowName") or check.get("context") or "unknown"


def _check_bucket(check: dict[str, Any]) -> str:
    text = " ".join(str(check.get(key) or "") for key in ("status", "conclusion", "state")).upper()
    if any(token in text for token in ("FAILURE", "FAILED", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED")):
        return "failed"
    if any(token in text for token in ("PENDING", "QUEUED", "IN_PROGRESS", "WAITING", "REQUESTED")) or not text.strip():
        return "pending"
    return "passed"


def dependency_files_changed(files: list[str]) -> bool:
    return any(path in DEPENDENCY_FILES or any(path.endswith(f"/{name}") for name in DEPENDENCY_FILES) for path in files)


def recommend_pr(item: dict[str, Any], files: list[str], failed: list[str], pending: list[str]) -> tuple[str, str]:
    mergeable = str(item.get("mergeable") or "UNKNOWN").upper()
    if item.get("isDraft"):
        return "wait", "Draft PR; wait until it is marked ready for review."
    if mergeable in {"CONFLICTING", "DIRTY", "FALSE"}:
        return "rebuild", "PR is dirty or conflicted; rebuild from current main."
    if pending or mergeable == "UNKNOWN":
        return "wait", "Mergeability or checks are still pending."
    if failed:
        return "fix_checks", f"Failing checks: {', '.join(failed)}."
    if any(path.startswith((".github/", "policies/", "secrets/")) for path in files):
        return "manual_attention", "Sensitive workflow/policy paths changed."
    return "merge", "Checks are clean and the PR appears safe for the shipper policy."


def snapshot_from_gh_item(repo: str, item: dict[str, Any]) -> dict[str, Any]:
    files = [entry.get("path", "") for entry in item.get("files", []) if entry.get("path")]
    checks = item.get("statusCheckRollup", [])
    failed = [_check_name(check) for check in checks if _check_bucket(check) == "failed"]
    pending = [_check_name(check) for check in checks if _check_bucket(check) == "pending"]
    recommendation, verdict = recommend_pr(item, files, failed, pending)
    return {
        "number": item.get("number"),
        "title": item.get("title"),
        "url": item.get("url"),
        "mergeability": item.get("mergeable") or "UNKNOWN",
        "draft": bool(item.get("isDraft")),
        "changed_file_count": item.get("changedFiles", len(files)),
        "check_status": "failed" if failed else "pending" if pending else "passed" if checks else "unknown",
        "failed_checks": failed,
        "pending_checks": pending,
        "dependency_files_changed": dependency_files_changed(files),
        "shipper_recommendation": recommendation,
        "verdict": verdict,
        "repository": repo,
        "updated_at": item.get("updatedAt"),
    }


def collect_pr_status(repo: str = "RapidFireRonin/Repo_foundry") -> dict[str, Any]:
    try:
        result = run_gh([
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "open",
            "--limit",
            "50",
            "--json",
            "number,title,url,isDraft,mergeable,changedFiles,files,statusCheckRollup,updatedAt",
        ])
    except GitHubCliUnavailable as exc:
        result = type("Result", (), {"returncode": 1, "stderr": str(exc), "stdout": ""})()
    generated_at = datetime.now(timezone.utc).isoformat()
    if result.returncode != 0:
        message = (result.stderr or result.stdout or "GitHub CLI unavailable").strip()
        return {
            "generated_at": generated_at,
            "repository": repo,
            "degraded": True,
            "error": message,
            "open_pr_count": 0,
            "pull_requests": [],
            "summary": f"PR status degraded: {message}",
        }
    items = json.loads(result.stdout or "[]")
    prs = [snapshot_from_gh_item(repo, item) for item in items]
    failed_count = sum(len(pr["failed_checks"]) for pr in prs)
    return {
        "generated_at": generated_at,
        "repository": repo,
        "degraded": False,
        "open_pr_count": len(prs),
        "failed_check_count": failed_count,
        "pull_requests": prs,
        "summary": "No open PRs." if not prs else f"{len(prs)} open PR(s), {failed_count} failing check(s).",
    }


def write_pr_status_artifacts(payload: dict[str, Any], output_dir: str | Path | None = None) -> dict[str, str]:
    root = Path(output_dir) if output_dir else repo_root() / "artifacts" / "pr-status"
    root.mkdir(parents=True, exist_ok=True)
    json_path = root / "latest.json"
    md_path = root / "latest.md"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [f"# PR Status Snapshot", "", f"Generated: {payload['generated_at']}", "", payload.get("summary", "")]
    for pr in payload.get("pull_requests", []):
        lines.extend([
            "",
            f"## #{pr['number']} {pr['title']}",
            f"- URL: {pr['url']}",
            f"- Mergeability: {pr['mergeability']}",
            f"- Checks: {pr['check_status']}",
            f"- Failed: {', '.join(pr['failed_checks']) if pr['failed_checks'] else 'none'}",
            f"- Pending: {', '.join(pr['pending_checks']) if pr['pending_checks'] else 'none'}",
            f"- Recommendation: {pr['shipper_recommendation']}",
            f"- Verdict: {pr['verdict']}",
        ])
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def main() -> None:
    payload = collect_pr_status()
    paths = write_pr_status_artifacts(payload)
    print(payload["summary"])
    print(f"JSON artifact: {paths['json']}")
    print(f"Markdown artifact: {paths['markdown']}")


if __name__ == "__main__":
    main()
