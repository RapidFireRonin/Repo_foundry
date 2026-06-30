from __future__ import annotations

from repo_foundry.health import collect_health, write_health_artifact


def test_health_json_shape(tmp_path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / "dashboard" / "frontend").mkdir(parents=True)
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "repo_foundry_pr_shipper.ps1").write_text("", encoding="utf-8")

    payload = collect_health(tmp_path)

    assert "generated_at" in payload
    assert "checks" in payload
    assert "python" in payload["checks"]
    assert "backend_import" in payload["checks"]


def test_health_artifact_written(tmp_path):
    path = write_health_artifact({"ok": True}, tmp_path / "latest-health.json")

    assert path.exists()
    assert "ok" in path.read_text(encoding="utf-8")
