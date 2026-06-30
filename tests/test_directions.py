from pathlib import Path

import yaml

from repo_foundry.directions import add_direction, list_directions, mark_matching_direction_done, reorder_direction, update_direction


def test_add_direction_updates_registry(tmp_path: Path) -> None:
    registry = tmp_path / "repos.yaml"
    registry.write_text(yaml.safe_dump({"repos": [], "directions": []}), encoding="utf-8")

    add_direction(
        "Focus tests",
        "Improve confidence",
        priority=88,
        scope="global",
        details="Add coverage for direction creation",
        source="dashboard",
        registry_path=registry,
    )

    directions = list_directions(registry)
    assert len(directions) == 1
    assert directions[0].title == "Focus tests"
    assert directions[0].priority == 88
    assert directions[0].details == "Add coverage for direction creation"
    assert directions[0].source == "dashboard"
    assert directions[0].created_at is not None


def test_update_direction_edits_goal_fields(tmp_path: Path) -> None:
    registry = tmp_path / "repos.yaml"
    registry.write_text(yaml.safe_dump({"repos": [], "directions": []}), encoding="utf-8")
    original = add_direction("Old goal", "Old outcome", priority=40, details="thin", registry_path=registry)

    updated = update_direction(
        original.created_at.isoformat(),
        title="Ship real queue controls",
        desired_outcome="Garrett can edit and reorder goals from Mission Control",
        details="Make the dashboard queue non append-only",
        priority=95,
        scope="mission-control",
        avoid=["placeholder UI", "manual YAML edits"],
        status="active",
        registry_path=registry,
    )

    assert updated is not None
    directions = list_directions(registry)
    assert directions[0].title == "Ship real queue controls"
    assert directions[0].desired_outcome == "Garrett can edit and reorder goals from Mission Control"
    assert directions[0].details == "Make the dashboard queue non append-only"
    assert directions[0].priority == 95
    assert directions[0].scope == "mission-control"
    assert directions[0].avoid == ["placeholder UI", "manual YAML edits"]
    assert directions[0].status == "active"


def test_reorder_direction_moves_goal_without_changing_created_at(tmp_path: Path) -> None:
    registry = tmp_path / "repos.yaml"
    registry.write_text(yaml.safe_dump({"repos": [], "directions": []}), encoding="utf-8")
    first = add_direction("First", "one", registry_path=registry)
    second = add_direction("Second", "two", registry_path=registry)
    third = add_direction("Third", "three", registry_path=registry)

    moved = reorder_direction(third.created_at.isoformat(), "top", registry)

    assert moved is not None
    directions = list_directions(registry)
    assert [item.title for item in directions] == ["Third", "First", "Second"]
    assert directions[0].created_at == third.created_at
    assert directions[1].created_at == first.created_at
    assert directions[2].created_at == second.created_at


def test_mark_matching_direction_done(tmp_path: Path) -> None:
    registry = tmp_path / "repos.yaml"
    registry.write_text(yaml.safe_dump({"repos": [], "directions": []}), encoding="utf-8")
    add_direction("Improve dashboard", "Polish UI", registry_path=registry)

    matched = mark_matching_direction_done("Improve dashboard with completion panel", registry)

    assert matched == "Improve dashboard"
    assert list_directions(registry)[0].status == "done"
