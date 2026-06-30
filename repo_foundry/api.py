from __future__ import annotations

from collections import defaultdict
import json
import os
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from repo_foundry.cycle_summary import append_summary, sample_summary
from repo_foundry.db import fetch_completion_prs, fetch_dashboard_items, init_db
from repo_foundry.directions import add_direction, list_directions, update_direction_status
from repo_foundry.health import collect_health
from repo_foundry.mission_control import build_mission_control
from repo_foundry.models import DashboardState, repo_root
from repo_foundry.pr_status import collect_pr_status, write_pr_status_artifacts
from repo_foundry.reconcile import build_plan, load_registry
from repo_foundry.shipper_logs import latest_shipper_status
from repo_foundry.visual_evidence import collect_visual_evidence


app = FastAPI(title="Repo Foundry API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:5174",
        "http://localhost:5174",
        "http://127.0.0.1:5274",
        "http://localhost:5274",
    ],
    allow_origin_regex=r"https?://.*:(5173|5174|5274)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/artifacts", StaticFiles(directory=str(repo_root() / "artifacts"), check_dir=False), name="artifacts")


class DirectionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    desired_outcome: str = Field(min_length=1, max_length=1000)
    details: str = Field(default="", max_length=2000)
    priority: int = Field(default=80, ge=0, le=100)
    scope: str = Field(default="global", max_length=160)


class DirectionStatusRequest(BaseModel):
    created_at: str = Field(min_length=1)
    status: str = Field(pattern="^(active|paused|done)$")


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/health/local")
def local_health() -> dict:
    return collect_health()


@app.get("/api/mission-control")
def mission_control() -> dict:
    return build_mission_control()


@app.get("/api/scorecard")
def scorecard() -> dict:
    return build_mission_control()["scorecard"]


@app.get("/api/shipper/status")
def shipper_status() -> dict:
    return latest_shipper_status()


@app.get("/api/changes")
def changes() -> dict:
    mission = build_mission_control()
    return {"changes": mission["changes"]}


@app.get("/api/visual-evidence")
def visual_evidence() -> dict:
    return collect_visual_evidence()


@app.get("/api/directions")
def directions() -> list[dict]:
    return [item.model_dump(mode="json") for item in list_directions(repo_root() / "registry" / "repos.yaml")]


@app.get("/api/pr-status")
def pr_status() -> dict:
    snapshot = collect_pr_status()
    snapshot["artifacts"] = write_pr_status_artifacts(snapshot)
    return snapshot


@app.get("/api/dashboard", response_model=DashboardState)
def dashboard() -> DashboardState:
    buckets: dict[str, list[dict]] = defaultdict(list)
    for item in fetch_dashboard_items():
        buckets[item["kind"]].append(item)
    return DashboardState(
        repos=buckets["repo"],
        blueprints=buckets["blueprint"],
        runs=buckets["run"],
        prs=buckets["pr"],
        logs=buckets["log"],
        artifacts=buckets["artifact"],
        directions=[item.model_dump(mode="json") for item in load_registry(repo_root() / "registry" / "repos.yaml").directions],
        watch_items=buckets["watch"],
        cycle_entries=buckets["cycle"],
        completion=completion_state(),
    )


def snapshot_operator_verdict(snapshot: dict[str, Any]) -> dict[str, str]:
    checks = snapshot.get("checks") or {}
    failing_count = int(checks.get("failing_count") or 0)
    unknown_count = int(checks.get("unknown_count") or 0)
    mergeable = snapshot.get("mergeable")
    policy_decision = str(snapshot.get("policy_decision") or "unknown")
    merge_state = str(snapshot.get("merge_state") or "unknown")

    if snapshot.get("merged"):
        return {"status": "merged", "summary": "Already merged.", "next_action": "Record the merge in the cycle log and continue with the next issue #13 metric."}
    if failing_count:
        return {"status": "blocked", "summary": f"Blocked by {failing_count} failing check{'s' if failing_count != 1 else ''}.", "next_action": "Fix or rerun the failing check before attempting merge."}
    if unknown_count:
        return {"status": "watch", "summary": f"Waiting on {unknown_count} unknown check{'s' if unknown_count != 1 else ''}.", "next_action": "Wait for checks to finish, then refresh the PR status snapshot."}
    if mergeable is False:
        return {"status": "blocked", "summary": f"Not mergeable: {merge_state}.", "next_action": "Rebuild the branch from current main or close it with a replacement PR reference."}
    if policy_decision == "eligible" and mergeable is True:
        return {"status": "ready", "summary": "Eligible for merge under the current policy snapshot.", "next_action": "Merge using the configured safe merge method and record the completion log entry."}
    return {"status": "review", "summary": f"Policy decision is {policy_decision}.", "next_action": "Review the risk note and policy reasons before changing PR state."}


def read_pr_status_snapshots(artifact_root: Path | None = None, limit: int = 20) -> list[dict[str, Any]]:
    root = artifact_root or repo_root() / "artifacts" / "pr-status"
    if not root.exists():
        return []

    snapshots: list[dict[str, Any]] = []
    for path in root.glob("*/pr-*/*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if payload.get("schema_version") != "pr-status-snapshot/v1":
            continue
        payload["artifact_path"] = str(path)
        payload["operator_verdict"] = snapshot_operator_verdict(payload)
        snapshots.append(payload)

    return sorted(snapshots, key=lambda item: (str(item.get("captured_at") or ""), int(item.get("pull_request") or 0)), reverse=True)[:limit]


def completion_state() -> dict:
    prs = fetch_completion_prs()
    ready = [pr for pr in prs if pr.get("decision", {}).get("allowed")]
    blocked = [pr for pr in prs if not pr.get("decision", {}).get("allowed")]
    failed = [pr for pr in prs if pr.get("failed_checks")]
    stale = [pr for pr in prs if pr.get("stale")]
    merged = [pr for pr in prs if pr.get("payload", {}).get("merged")]
    snapshots = read_pr_status_snapshots()
    next_action = "Merge ready PRs" if ready else "Fix blocked PRs" if blocked else "Poll open PRs"
    return {"ready": ready, "blocked": blocked, "failed_checks": failed, "stale": stale, "recently_merged": merged[:5], "latest_snapshots": snapshots, "next_action": next_action, "mode": "dry-run"}


@app.get("/api/cycle-log")
def cycle_log() -> dict[str, str]:
    path = repo_root() / "docs" / "agent-cycle-log.md"
    return {"path": str(path), "content": path.read_text(encoding="utf-8") if path.exists() else ""}


@app.post("/api/cycle-log/sample")
def append_sample_cycle() -> dict[str, str]:
    path = append_summary(sample_summary())
    return {"path": str(path), "status": "appended"}


@app.post("/api/directions")
def create_direction(request: DirectionCreateRequest) -> dict:
    item = add_direction(title=request.title.strip(), desired_outcome=request.desired_outcome.strip(), priority=request.priority, scope=request.scope.strip() or "global", details=request.details.strip(), source="dashboard", registry_path=repo_root() / "registry" / "repos.yaml")
    return item.model_dump(mode="json")


@app.patch("/api/directions/status")
def set_direction_status(request: DirectionStatusRequest) -> dict:
    item = update_direction_status(created_at=request.created_at, status=request.status, source="dashboard", registry_path=repo_root() / "registry" / "repos.yaml")
    if item is None:
        raise HTTPException(status_code=404, detail="Direction not found")
    return item.model_dump(mode="json")


@app.get("/api/reconcile/example")
def reconcile_example() -> dict:
    plan = build_plan(repo_root() / "blueprints" / "example-repo.yaml", repo_root() / "registry" / "repos.yaml")
    return plan.model_dump(mode="json")


def main() -> None:
    host = os.environ.get("REPO_FOUNDRY_API_HOST", "127.0.0.1")
    port = int(os.environ.get("REPO_FOUNDRY_API_PORT", "8765"))
    uvicorn.run("repo_foundry.api:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
