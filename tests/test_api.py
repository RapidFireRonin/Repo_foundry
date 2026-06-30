from pathlib import Path

import yaml
from fastapi.testclient import TestClient

from repo_foundry import api


def test_create_direction_route_writes_registry_and_returns_item(tmp_path: Path, monkeypatch) -> None:
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    registry = registry_dir / "repos.yaml"
    registry.write_text(yaml.safe_dump({"repos": [], "directions": []}), encoding="utf-8")
    monkeypatch.setattr(api, "repo_root", lambda: tmp_path)

    client = TestClient(api.app)
    response = client.post(
        "/api/directions",
        json={
            "title": "Focus on GitHub adapter",
            "desired_outcome": "Wire the live adapter",
            "details": "Prioritize apply and PR creation.",
            "priority": 91,
            "scope": "RapidFireRonin/Repo_foundry",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "dashboard"
    assert body["priority"] == 91
    assert body["status"] == "active"
    saved = yaml.safe_load(registry.read_text(encoding="utf-8"))
    assert saved["directions"][0]["title"] == "Focus on GitHub adapter"
