from __future__ import annotations

import argparse
import json
import os
import sqlite3
from pathlib import Path
from typing import Any


def db_path() -> Path:
    return Path(os.environ.get("REPO_FOUNDRY_DB", "./data/repo_foundry.sqlite3"))


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with connect() as conn:
        conn.executescript(
            """
            create table if not exists dashboard_items (
              id integer primary key autoincrement,
              kind text not null,
              title text not null,
              status text not null,
              payload text not null default '{}',
              created_at text not null default current_timestamp
            );
            """
        )


def upsert_seed(kind: str, title: str, status: str, payload: dict[str, Any]) -> None:
    with connect() as conn:
        conn.execute(
            "insert into dashboard_items(kind, title, status, payload) values (?, ?, ?, ?)",
            (kind, title, status, json.dumps(payload)),
        )


def fetch_dashboard_items() -> list[dict[str, Any]]:
    init_db()
    with connect() as conn:
        rows = conn.execute("select * from dashboard_items order by id desc limit 200").fetchall()
    return [
        {
            "id": row["id"],
            "kind": row["kind"],
            "title": row["title"],
            "status": row["status"],
            "payload": json.loads(row["payload"]),
            "created_at": row["created_at"],
        }
        for row in rows
    ]


def seed() -> None:
    init_db()
    with connect() as conn:
        conn.execute("delete from dashboard_items")
    samples = [
        ("repo", "RapidFireRonin/Repo_foundry", "planning", {"visibility": "private", "branch": "main"}),
        ("blueprint", "example-repo.yaml", "valid", {"missing": ["CI workflow", "memory files"]}),
        ("run", "hourly-cycle-local", "autonomous", {"agents": 5, "duration": "12m"}),
        ("pr", "Add standard repo workflows", "auto-queued", {"checks": "pending"}),
        ("log", "reconcile dry-run", "complete", {"path": "logs/audit.jsonl"}),
        ("artifact", "reconcile-plan.json", "available", {"path": "artifacts/reconcile-plan.json"}),
        ("watch", "Branch protection edit highlighted", "visible", {"impact": "high"}),
        ("watch", "Follow active direction queue", "visible", {"impact": "priority"}),
        ("cycle", "Latest hourly summary", "complete", {"path": "docs/agent-cycle-log.md"}),
    ]
    for kind, title, status, payload in samples:
        upsert_seed(kind, title, status, payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "seed"])
    args = parser.parse_args()
    if args.command == "init":
        init_db()
    if args.command == "seed":
        seed()


if __name__ == "__main__":
    main()
