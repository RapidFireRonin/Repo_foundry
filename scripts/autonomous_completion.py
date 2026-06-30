#!/usr/bin/env python3
"""Autonomous PR completion loop for Repo Foundry.

This script is intentionally dependency-free so it can run inside GitHub Actions.
It observes open PRs, classifies status, merges low-risk passing PRs when policy
allows, and writes human-readable and machine-readable run artifacts.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

API = "https://api.github.com"
ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "policies" / "autonomous-completion-policy.json"
ARTIFACT_DIR = ROOT / "artifacts" / "autonomous-completion"


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log(lines: list[str], message: str) -> None:
    entry = f"[{now()}] {message}"
    print(entry, flush=True)
    lines.append(entry)


def load_policy() -> dict[str, Any]:
    if not POLICY_PATH.exists():
        return {"enabled": False, "execute": False, "reason": "policy file missing"}
    return json.loads(POLICY_PATH.read_text(encoding="utf-8"))


def request_json(method: str, path: str, credential: str, body: dict[str, Any] | None = None) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {credential}",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "repo-foundry-autonomous-completion",
        },
    )
    with urlopen(req, timeout=30) as response:
        raw = response.read().decode("utf-8")
        if not raw:
            return None
        return json.loads(raw)


def paged(method: str, path: str, credential: str) -> list[Any]:
    sep = "&" if "?" in path else "?"
    page = 1
    out: list[Any] = []
    while True:
        chunk = request_json(method, f"{path}{sep}per_page=100&page={page}", credential)
        if not chunk:
            return out
        out.extend(chunk)
        if len(chunk) < 100:
            return out
        page += 1


def safe_get(method: str, path: str, credential: str, body: dict[str, Any] | None = None) -> tuple[bool, Any]:
    try:
        return True, request_json(method, path, credential, body)
    except HTTPError as exc:
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = str(exc)
        return False, {"status": exc.code, "error": detail}
    except Exception as exc:  # noqa: BLE001 - artifact should capture unexpected runtime failures.
        return False, {"error": str(exc)}


def changed_dependency_files(files: list[dict[str, Any]], policy: dict[str, Any]) -> list[str]:
    dependency_names = set(policy.get("dependency_files", []))
    changed: list[str] = []
    for item in files:
        filename = item.get("filename", "")
        if filename in dependency_names or any(filename.endswith(f"/{name}") for name in dependency_names):
            changed.append(filename)
    return changed


def blocked_files(files: list[dict[str, Any]], policy: dict[str, Any]) -> list[str]:
    prefixes = policy.get("blocked_path_prefixes", [])
    contains = policy.get("blocked_path_contains", [])
    blocked: list[str] = []
    for item in files:
        filename = item.get("filename", "")
        if any(filename.startswith(prefix) for prefix in prefixes):
            blocked.append(filename)
            continue
        if any(fragment in filename for fragment in contains):
            blocked.append(filename)
    return blocked


def summarize_checks(repo: str, sha: str, credential: str, dependency_files_changed: bool, policy: dict[str, Any]) -> dict[str, Any]:
    failed: list[str] = []
    pending: list[str] = []
    passed: list[str] = []
    ignored: list[str] = []

    ok, check_payload = safe_get("GET", f"/repos/{repo}/commits/{sha}/check-runs", credential)
    if ok:
        for run in check_payload.get("check_runs", []):
            name = run.get("name") or "unnamed-check"
            status = run.get("status")
            conclusion = run.get("conclusion")
            if status != "completed":
                pending.append(name)
            elif conclusion in ("success", "neutral", "skipped"):
                passed.append(name)
            else:
                failed.append(name)
    else:
        pending.append("check-run-lookup")

    ok, status_payload = safe_get("GET", f"/repos/{repo}/commits/{sha}/status", credential)
    if ok:
        for status in status_payload.get("statuses", []):
            context = status.get("context") or "unnamed-status"
            state = status.get("state")
            if state == "success":
                passed.append(context)
            elif state in ("pending", "expected"):
                pending.append(context)
            else:
                failed.append(context)
    else:
        pending.append("combined-status-lookup")

    ignore_names = set(policy.get("ignorable_failed_checks_without_dependency_changes", []))
    remaining_failed: list[str] = []
    for name in sorted(set(failed)):
        if name in ignore_names and not dependency_files_changed:
            ignored.append(name)
        else:
            remaining_failed.append(name)

    return {
        "passed": sorted(set(passed)),
        "pending": sorted(set(pending)),
        "failed": remaining_failed,
        "ignored": sorted(set(ignored)),
    }


def update_branch(repo: str, number: int, credential: str) -> tuple[bool, Any]:
    return safe_get("PUT", f"/repos/{repo}/pulls/{number}/update-branch", credential, {})


def merge_pr(repo: str, number: int, title: str, credential: str) -> tuple[bool, Any]:
    body = {
        "commit_title": f"Merge PR #{number}: {title}",
        "commit_message": "Merged by Repo Foundry autonomous completion loop.",
        "merge_method": "squash",
    }
    return safe_get("PUT", f"/repos/{repo}/pulls/{number}/merge", credential, body)


def main() -> int:
    lines: list[str] = []
    decisions: list[dict[str, Any]] = []
    policy = load_policy()
    repo = os.environ.get("GITHUB_REPOSITORY", "RapidFireRonin/Repo_foundry")
    credential = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or os.environ.get("REPO_FOUNDRY_GH_TOKEN")
    execute_env = os.environ.get("SWEEPER_EXECUTE", "true").lower() in {"1", "true", "yes"}
    max_merges = int(os.environ.get("MAX_MERGES_PER_RUN", str(policy.get("max_merges_per_run", 3))))
    update_stale = os.environ.get("UPDATE_STALE_BRANCHES", str(policy.get("update_stale_branches", True))).lower() in {"1", "true", "yes"}

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    json_path = ARTIFACT_DIR / f"run-{run_id}.json"
    md_path = ARTIFACT_DIR / f"run-{run_id}.md"

    log(lines, f"Repo Foundry autonomous completion started for {repo}.")

    if not credential:
        log(lines, "No GitHub credential available; fail closed.")
        json_path.write_text(json.dumps({"decisions": decisions, "error": "missing credential"}, indent=2), encoding="utf-8")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 1

    if not policy.get("enabled", False):
        log(lines, "Policy disabled; report-only exit.")
        json_path.write_text(json.dumps({"decisions": decisions, "policy": policy}, indent=2), encoding="utf-8")
        md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return 0

    execute = execute_env and bool(policy.get("execute", False))
    log(lines, f"Execute mode: {execute}")

    prs = paged("GET", f"/repos/{repo}/pulls?state=open", credential)
    prs = sorted(prs, key=lambda item: item.get("number", 0))
    log(lines, f"Open PRs found: {len(prs)}")

    merges = 0
    for pr in prs:
        number = int(pr["number"])
        title = pr.get("title", "")
        decision: dict[str, Any] = {"pr": number, "title": title, "timestamp": now(), "action": "skip", "reasons": []}
        decisions.append(decision)
        log(lines, f"---- PR #{number}: {title}")

        ok, fresh = safe_get("GET", f"/repos/{repo}/pulls/{number}", credential)
        if not ok:
            decision["reasons"].append("could not refresh PR metadata")
            log(lines, f"Skip #{number}: metadata lookup failed")
            continue

        if policy.get("require_non_draft", True) and fresh.get("draft"):
            decision["reasons"].append("draft PR")
            log(lines, f"Skip #{number}: draft")
            continue

        head_sha = fresh.get("head", {}).get("sha")
        mergeable_state = fresh.get("mergeable_state") or "unknown"
        decision["mergeable_state"] = mergeable_state

        ok, files = safe_get("GET", f"/repos/{repo}/pulls/{number}/files?per_page=100", credential)
        if not ok:
            decision["reasons"].append("could not read changed files")
            log(lines, f"Skip #{number}: changed-file lookup failed")
            continue

        total_additions = sum(int(item.get("additions", 0)) for item in files)
        total_deletions = sum(int(item.get("deletions", 0)) for item in files)
        decision.update({"files_changed": len(files), "additions": total_additions, "deletions": total_deletions})

        blocked = blocked_files(files, policy)
        if blocked:
            decision["reasons"].append(f"blocked paths: {blocked}")
            log(lines, f"Skip #{number}: blocked paths {blocked}")
            continue

        if len(files) > int(policy.get("max_files_changed", 30)):
            decision["reasons"].append("too many changed files")
            log(lines, f"Skip #{number}: too many files")
            continue
        if total_additions > int(policy.get("max_additions", 1500)) or total_deletions > int(policy.get("max_deletions", 1000)):
            decision["reasons"].append("diff too large")
            log(lines, f"Skip #{number}: diff too large")
            continue

        dependency_changed = bool(changed_dependency_files(files, policy))
        checks = summarize_checks(repo, head_sha, credential, dependency_changed, policy)
        decision["checks"] = checks
        decision["dependency_changed"] = dependency_changed

        if checks["failed"]:
            decision["reasons"].append(f"failed checks: {checks['failed']}")
            log(lines, f"Skip #{number}: failed checks {checks['failed']}")
            continue
        if checks["pending"]:
            decision["reasons"].append(f"pending checks: {checks['pending']}")
            log(lines, f"Skip #{number}: pending checks {checks['pending']}")
            continue

        allowed_states = set(policy.get("require_mergeable_state", ["clean", "has_hooks", "unstable"]))
        if mergeable_state not in allowed_states:
            decision["reasons"].append(f"mergeable_state={mergeable_state}")
            log(lines, f"Skip #{number}: mergeable_state={mergeable_state}")
            if update_stale and mergeable_state in {"behind", "unknown"}:
                ok, payload = update_branch(repo, number, credential)
                decision["branch_update_attempted"] = True
                decision["branch_update_ok"] = ok
                if ok:
                    log(lines, f"Requested branch update for #{number}")
                else:
                    log(lines, f"Branch update failed for #{number}: {payload}")
            continue

        if merges >= max_merges:
            decision["reasons"].append("max merges reached")
            log(lines, f"Skip #{number}: max merges reached")
            continue

        if not execute:
            decision["action"] = "would_merge"
            log(lines, f"Would merge #{number}: policy and checks passed")
            continue

        ok, payload = merge_pr(repo, number, title, credential)
        if ok:
            merges += 1
            decision["action"] = "merged"
            decision["merge_payload"] = payload
            log(lines, f"Merged #{number}")
        else:
            decision["action"] = "merge_failed"
            decision["error"] = payload
            log(lines, f"Merge failed for #{number}: {payload}")

    result = {"repo": repo, "timestamp": now(), "execute": execute, "merges": merges, "policy": policy, "decisions": decisions}
    json_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary_path:
        with open(summary_path, "a", encoding="utf-8") as handle:
            handle.write("# Repo Foundry autonomous completion\n\n")
            handle.write("\n".join(f"- {line}" for line in lines[-40:]))
            handle.write("\n")

    log(lines, f"Done. Merged {merges} PR(s). Artifacts: {json_path}, {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
