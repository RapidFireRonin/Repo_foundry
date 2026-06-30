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


def test_direction_status_route_updates_registry_and_returns_item(tmp_path: Path, monkeypatch) -> None:
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    registry = registry_dir / "repos.yaml"
    registry.write_text(
        yaml.safe_dump(
            {
                "repos": [],
                "directions": [
                    {
                        "title": "Direct the agents",
                        "priority": 95,
                        "scope": "global",
                        "desired_outcome": "Let Garrett pause and complete directions from the dashboard.",
                        "details": "",
                        "avoid": [],
                        "status": "active",
                        "source": "dashboard",
                        "created_at": "2026-06-30T13:24:00+00:00",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(api, "repo_root", lambda: tmp_path)

    client = TestClient(api.app)
    response = client.patch(
        "/api/directions/status",
        json={"created_at": "2026-06-30T13:24:00+00:00", "status": "paused"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "paused"
    saved = yaml.safe_load(registry.read_text(encoding="utf-8"))
    assert saved["directions"][0]["status"] == "paused"


def test_direction_status_route_returns_404_for_missing_direction(tmp_path: Path, monkeypatch) -> None:
    registry_dir = tmp_path / "registry"
    registry_dir.mkdir()
    (registry_dir / "repos.yaml").write_text(yaml.safe_dump({"repos": [], "directions": []}), encoding="utf-8")
    monkeypatch.setattr(api, "repo_root", lambda: tmp_path)

    client = TestClient(api.app)
    response = client.patch(
        "/api/directions/status",
        json={"created_at": "2026-06-30T13:24:00+00:00", "status": "done"},
    )

    assert response.status_code == 404


def test_read_pr_status_snapshots_adds_operator_verdict(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "RapidFireRonin_Repo_foundry" / "pr-22"
    snapshot_dir.mkdir(parents=True)
    snapshot_path = snapshot_dir / "20260630T120000Z.json"
    snapshot_path.write_text(
        """
        {
          "schema_version": "pr-status-snapshot/v1",
          "captured_at": "2026-06-30T12:00:00Z",
          "repository": "RapidFireRonin/Repo_foundry",
          "pull_request": 22,
          "display_url": "https://github.com/RapidFireRonin/Repo_foundry/pull/22",
          "head_sha": "abc123",
          "base_branch": "main",
          "head_branch": "builder/example",
          "mergeable": true,
          "merge_state": "clean",
          "merged": false,
          "checks": {
            "status": "completed",
            "conclusion": "success",
            "total_count": 3,
            "failing_count": 0,
            "unknown_count": 0,
            "runs": []
          },
          "policy_decision": "eligible",
          "risk_note": "low risk",
          "rollback_note": "revert PR",
          "linked_task": "#13",
          "direction_item": null
        }
        """,
        encoding="utf-8",
    )

    snapshots = api.read_pr_status_snapshots(tmp_path)

    assert snapshots[0]["artifact_path"] == str(snapshot_path)
    assert snapshots[0]["operator_verdict"] == {
        "status": "ready",
        "summary": "Eligible for merge under the current policy snapshot.",
        "next_action": "Merge using the configured safe merge method and record the completion log entry.",
    }


def test_snapshot_operator_verdict_blocks_failing_checks() -> None:
    verdict = api.snapshot_operator_verdict(
        {
            "merged": False,
            "mergeable": True,
            "merge_state": "clean",
            "policy_decision": "eligible",
            "checks": {"failing_count": 2, "unknown_count": 0},
        }
    )

    assert verdict["status"] == "blocked"
    assert verdict["summary"] == "Blocked by 2 failing checks."
    assert verdict["next_action"] == "Fix or rerun the failing check before attempting merge."


def test_mission_control_endpoint_returns_collector_payload(monkeypatch) -> None:
    monkeypatch.setattr(api, "build_mission_control", lambda: {"executive_status": {"status": "Healthy"}, "scorecard": {"metrics": []}})

    client = TestClient(api.app)
    response = client.get("/api/mission-control")

    assert response.status_code == 200
    assert response.json()["executive_status"]["status"] == "Healthy"


def test_local_health_endpoint_degrades_as_json(monkeypatch) -> None:
    monkeypatch.setattr(api, "collect_health", lambda: {"overall_status": "attention", "checks": {"git": {"ok": False}}})

    client = TestClient(api.app)
    response = client.get("/api/health/local")

    assert response.status_code == 200
    assert response.json()["checks"]["git"]["ok"] is False
