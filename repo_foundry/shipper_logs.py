from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from repo_foundry.models import repo_root


LINE_RE = re.compile(r"^\[(?P<stamp>[^\]]+)\]\s*(?P<message>.*)$")
PR_RE = re.compile(r"PR #(?P<number>\d+)")


def shipper_log_files(log_dir: str | Path | None = None) -> list[Path]:
    root = Path(log_dir) if log_dir else repo_root() / "logs"
    if not root.exists():
        return []
    return sorted(root.glob("repo-foundry-pr-shipper-*.log"), key=lambda path: path.stat().st_mtime, reverse=True)


def parse_shipper_log(path: str | Path) -> dict[str, Any]:
    log_path = Path(path)
    result: dict[str, Any] = {
        "exists": log_path.exists(),
        "log_file": str(log_path),
        "last_run_at": None,
        "merged_prs": [],
        "skipped_prs": [],
        "conflicts": [],
        "failed_checks": [],
        "dependency_review_overrides": [],
        "final_merged_count": 0,
        "summary": "No shipper log found yet.",
    }
    if not log_path.exists():
        return result

    current_pr: int | None = None
    for raw_line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = LINE_RE.match(raw_line)
        stamp = match.group("stamp") if match else None
        message = match.group("message") if match else raw_line
        if stamp:
            result["last_run_at"] = stamp

        pr_match = PR_RE.search(message)
        if pr_match:
            current_pr = int(pr_match.group("number"))

        if "Merged PR #" in message or "Admin-merged PR #" in message:
            if current_pr is not None and current_pr not in result["merged_prs"]:
                result["merged_prs"].append(current_pr)
        if "dependency-review" in message and ("override" in message.lower() or "Admin-merging" in message):
            result["dependency_review_overrides"].append(message)
        if "conflicted" in message.lower() or "dirty" in message.lower():
            result["conflicts"].append(message)
            if current_pr is not None:
                result["skipped_prs"].append({"number": current_pr, "reason": message})
        if "failing checks:" in message:
            result["failed_checks"].append(message)
            if current_pr is not None:
                result["skipped_prs"].append({"number": current_pr, "reason": message})
        if "Skipping" in message or "Skipping." in message:
            if current_pr is not None:
                result["skipped_prs"].append({"number": current_pr, "reason": message})

        done_match = re.search(r"Done\. Merged (?P<count>\d+) PR", message)
        if done_match:
            result["final_merged_count"] = int(done_match.group("count"))

    merged_count = result["final_merged_count"] or len(result["merged_prs"])
    if merged_count:
        result["summary"] = f"Shipper merged {merged_count} PR(s) in the last run."
    elif result["skipped_prs"]:
        result["summary"] = f"Shipper skipped {len(result['skipped_prs'])} PR decision(s); attention may be needed."
    else:
        result["summary"] = "Shipper ran and found nothing to merge."
    return result


def latest_shipper_status(log_dir: str | Path | None = None) -> dict[str, Any]:
    files = shipper_log_files(log_dir)
    if not files:
        return parse_shipper_log((Path(log_dir) if log_dir else repo_root() / "logs") / "repo-foundry-pr-shipper-missing.log")
    status = parse_shipper_log(files[0])
    status["available_logs"] = [str(path) for path in files[:10]]
    return status
