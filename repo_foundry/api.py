from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from repo_foundry.cycle_summary import append_summary, sample_summary
from repo_foundry.db import fetch_dashboard_items, init_db
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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    )


@app.get("/api/cycle-log")
def cycle_log() -> dict[str, str]:
    path = repo_root() / "docs" / "agent-cycle-log.md"
    return {"path": str(path), "content": path.read_text(encoding="utf-8") if path.exists() else ""}


@app.post("/api/cycle-log/sample")
def append_sample_cycle() -> dict[str, str]:
    path = append_summary(sample_summary())
    return {"path": str(path), "status": "appended"}


@app.get("/api/reconcile/example")
def reconcile_example() -> dict:
    plan = build_plan(repo_root() / "blueprints" / "example-repo.yaml", repo_root() / "registry" / "repos.yaml")
    return plan.model_dump(mode="json")


def main() -> None:
    uvicorn.run("repo_foundry.api:app", host="127.0.0.1", port=8765, reload=False)


if __name__ == "__main__":
    main()
