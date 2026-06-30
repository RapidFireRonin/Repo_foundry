from pathlib import Path

import yaml

from repo_foundry.directions import add_direction, list_directions


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
