from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from repo_foundry.audit import write_audit_event
from repo_foundry.models import DirectionItem, Registry
from repo_foundry.reconcile import load_registry


def list_directions(registry_path: str | Path = "registry/repos.yaml") -> list[DirectionItem]:
    return load_registry(registry_path).directions


def add_direction(
    title: str,
    desired_outcome: str,
    priority: int = 80,
    scope: str = "global",
    details: str = "",
    avoid: list[str] | None = None,
    source: str = "manual",
    registry_path: str | Path = "registry/repos.yaml",
) -> DirectionItem:
    path = Path(registry_path)
    registry = load_registry(path)
    item = DirectionItem(
        title=title,
        desired_outcome=desired_outcome,
        priority=priority,
        scope=scope,
        details=details,
        avoid=avoid or [],
        source=source,
    )
    registry.directions.append(item)
    path.write_text(yaml.safe_dump(registry.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
    write_audit_event("direction_add", title, priority=priority, scope=scope, source=source)
    return item


def mark_matching_direction_done(pr_title: str, registry_path: str | Path = "registry/repos.yaml") -> str | None:
    path = Path(registry_path)
    registry = load_registry(path)
    for item in registry.directions:
        if item.status == "active" and (
            item.title.lower() in pr_title.lower() or pr_title.lower() in item.title.lower()
        ):
            item.status = "done"
            path.write_text(yaml.safe_dump(registry.model_dump(mode="json"), sort_keys=False), encoding="utf-8")
            write_audit_event("direction_done", item.title, source="completion_loop", pr_title=pr_title)
            return item.title
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage human direction for autonomous agents.")
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--registry", default="registry/repos.yaml")
    add_parser = sub.add_parser("add")
    add_parser.add_argument("title")
    add_parser.add_argument("desired_outcome")
    add_parser.add_argument("--priority", type=int, default=80)
    add_parser.add_argument("--scope", default="global")
    add_parser.add_argument("--details", default="")
    add_parser.add_argument("--avoid", action="append", default=[])
    add_parser.add_argument("--registry", default="registry/repos.yaml")
    args = parser.parse_args()

    if args.command == "list":
        for item in list_directions(args.registry):
            print(f"{item.priority:03d} {item.scope} {item.title}: {item.desired_outcome}")
    if args.command == "add":
        item = add_direction(args.title, args.desired_outcome, args.priority, args.scope, args.details, args.avoid, "cli", args.registry)
        print(item.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
