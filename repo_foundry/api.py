from __future__ import annotations

from collections import defaultdict
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from repo_foundry.cycle_summary import append_summary, sample_summary
from repo_foundry.db import fetch_completion_prs, fetch_dashboard_items, init_db
from repo_foundry.directions import add_direction
from repo_foundry.models import DashboardState, repo_root
from repo_foundry.reconcile import build_plan, load_registry


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


class DirectionCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    desired_outcome: str = Field(min_length=1, max_length=1000)
    details: str = Field(default="", max_length=2000)
    priority: int = Field(default=80, ge=0, le=100)
    scope: str = Field(default="global", max_length=160)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


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


def completion_state() -> dict:
    prs = fetch_completion_prs()
    ready = [pr for pr in prs if pr.get("decision", {}).get("allowed")]
    blocked = [pr for pr in prs if not pr.get("decision", {}).get("allowed")]
    failed = [pr for pr in prs if pr.get("failed_checks")]
    stale = [pr for pr in prs if pr.get("stale")]
    merged = [pr for pr in prs if pr.get("payload", {}).get("merged")]
    next_action = "Merge ready PRs" if ready else "Fix blocked PRs" if blocked else "Poll open PRs"
    return {
        "ready": ready,
        "blocked": blocked,
        "failed_checks": failed,
        "stale": stale,
        "recently_merged": merged[:5],
        "next_action": next_action,
        "mode": "dry-run",
    }


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
    item = add_direction(
        title=request.title.strip(),
        desired_outcome=request.desired_outcome.strip(),
        priority=request.priority,
        scope=request.scope.strip() or "global",
        details=request.details.strip(),
        source="dashboard",
        registry_path=repo_root() / "registry" / "repos.yaml",
    )
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
