from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from repo_foundry.audit import write_audit_event
from repo_foundry.models import DirectionItem
from repo_foundry.reconcile import load_registry


ALLOWED_DIRECTION_STATUSES = {"active", "paused", "done"}


def _write_registry(registry_path: str | Path, registry) -> None:
    Path(registry_path).write_text(yaml.safe_dump(registry.model_dump(mode="json"), sort_keys=False), encoding="utf-8")


def _find_direction(registry, created_at: str) -> DirectionItem | None:
    for item in registry.directions:
        if item.created_at.isoformat() == created_at:
            return item
    return None


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
    _write_registry(path, registry)
    write_audit_event("direction_add", title, priority=priority, scope=scope, source=source)
    return item


def update_direction_status(
    created_at: str,
    status: str,
    registry_path: str | Path = "registry/repos.yaml",
    source: str = "dashboard",
) -> DirectionItem | None:
    if status not in ALLOWED_DIRECTION_STATUSES:
        raise ValueError(f"unsupported direction status: {status}")

    path = Path(registry_path)
    registry = load_registry(path)
    item = _find_direction(registry, created_at)
    if item is None:
        return None
    item.status = status
    _write_registry(path, registry)
    write_audit_event("direction_status", item.title, status=status, scope=item.scope, source=source)
    return item


def update_direction(
    created_at: str,
    *,
    title: str | None = None,
    desired_outcome: str | None = None,
    details: str | None = None,
    priority: int | None = None,
    scope: str | None = None,
    avoid: list[str] | None = None,
    status: str | None = None,
    registry_path: str | Path = "registry/repos.yaml",
    source: str = "dashboard",
) -> DirectionItem | None:
    if status is not None and status not in ALLOWED_DIRECTION_STATUSES:
        raise ValueError(f"unsupported direction status: {status}")

    path = Path(registry_path)
    registry = load_registry(path)
    item = _find_direction(registry, created_at)
    if item is None:
        return None

    before = item.model_dump(mode="json")
    if title is not None:
        item.title = title.strip()
    if desired_outcome is not None:
        item.desired_outcome = desired_outcome.strip()
    if details is not None:
        item.details = details.strip()
    if priority is not None:
        item.priority = priority
    if scope is not None:
        item.scope = scope.strip() or "global"
    if avoid is not None:
        item.avoid = [entry.strip() for entry in avoid if entry.strip()]
    if status is not None:
        item.status = status

    _write_registry(path, registry)
    write_audit_event(
        "direction_update",
        item.title,
        created_at=created_at,
        before_title=before["title"],
        priority=item.priority,
        status=item.status,
        scope=item.scope,
        source=source,
    )
    return item


def reorder_direction(
    created_at: str,
    direction: str,
    registry_path: str | Path = "registry/repos.yaml",
    source: str = "dashboard",
) -> DirectionItem | None:
    if direction not in {"up", "down", "top", "bottom"}:
        raise ValueError(f"unsupported reorder direction: {direction}")

    path = Path(registry_path)
    registry = load_registry(path)
    directions = registry.directions
    index = next((idx for idx, item in enumerate(directions) if item.created_at.isoformat() == created_at), None)
    if index is None:
        return None

    item = directions[index]
    if direction == "up":
        target = max(0, index - 1)
    elif direction == "down":
        target = min(len(directions) - 1, index + 1)
    elif direction == "top":
        target = 0
    else:
        target = len(directions) - 1

    if target != index:
        directions.pop(index)
        directions.insert(target, item)
        _write_registry(path, registry)
    write_audit_event("direction_reorder", item.title, direction=direction, from_index=index, to_index=target, source=source)
    return item


def mark_matching_direction_done(pr_title: str, registry_path: str | Path = "registry/repos.yaml") -> str | None:
    path = Path(registry_path)
    registry = load_registry(path)
    for item in registry.directions:
        if item.status == "active" and (
            item.title.lower() in pr_title.lower() or pr_title.lower() in item.title.lower()
        ):
            item.status = "done"
            _write_registry(path, registry)
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
    status_parser = sub.add_parser("status")
    status_parser.add_argument("created_at")
    status_parser.add_argument("status", choices=sorted(ALLOWED_DIRECTION_STATUSES))
    status_parser.add_argument("--registry", default="registry/repos.yaml")
    edit_parser = sub.add_parser("edit")
    edit_parser.add_argument("created_at")
    edit_parser.add_argument("--title")
    edit_parser.add_argument("--desired-outcome")
    edit_parser.add_argument("--details")
    edit_parser.add_argument("--priority", type=int)
    edit_parser.add_argument("--scope")
    edit_parser.add_argument("--avoid", action="append")
    edit_parser.add_argument("--status", choices=sorted(ALLOWED_DIRECTION_STATUSES))
    edit_parser.add_argument("--registry", default="registry/repos.yaml")
    reorder_parser = sub.add_parser("reorder")
    reorder_parser.add_argument("created_at")
    reorder_parser.add_argument("direction", choices=["up", "down", "top", "bottom"])
    reorder_parser.add_argument("--registry", default="registry/repos.yaml")
    args = parser.parse_args()

    if args.command == "list":
        for item in list_directions(args.registry):
            print(f"{item.priority:03d} {item.status} {item.scope} {item.title}: {item.desired_outcome}")
    if args.command == "add":
        item = add_direction(args.title, args.desired_outcome, args.priority, args.scope, args.details, args.avoid, "cli", args.registry)
        print(item.model_dump_json(indent=2))
    if args.command == "status":
        item = update_direction_status(args.created_at, args.status, args.registry, source="cli")
        if item is None:
            raise SystemExit(f"No direction found for created_at={args.created_at}")
        print(item.model_dump_json(indent=2))
    if args.command == "edit":
        item = update_direction(
            args.created_at,
            title=args.title,
            desired_outcome=args.desired_outcome,
            details=args.details,
            priority=args.priority,
            scope=args.scope,
            avoid=args.avoid,
            status=args.status,
            registry_path=args.registry,
            source="cli",
        )
        if item is None:
            raise SystemExit(f"No direction found for created_at={args.created_at}")
        print(item.model_dump_json(indent=2))
    if args.command == "reorder":
        item = reorder_direction(args.created_at, args.direction, args.registry, source="cli")
        if item is None:
            raise SystemExit(f"No direction found for created_at={args.created_at}")
        print(item.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
