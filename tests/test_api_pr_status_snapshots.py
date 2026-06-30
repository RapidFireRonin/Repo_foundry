import json
from datetime import datetime, timedelta, timezone

from repo_foundry.api import read_pr_status_snapshots


def write_snapshot(root, repo_dir, pr_number, sha, captured_at, **overrides):
    path = root / repo_dir / f"pr-{pr_number}" / f"{sha}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "pr-status-snapshot/v1",
        "captured_at": captured_at.isoformat(),
        "repository": "RapidFireRonin/Repo_foundry",
        "pull_request": pr_number,
        "display_url": f"https://github.com/RapidFireRonin/Repo_foundry/pull/{pr_number}",
        "head_sha": sha,
        "head_branch": "builder/example",
        "policy_decision": "watch",
        "risk_note": "checks are still pending",
    }
    payload.update(overrides)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_read_pr_status_snapshots_returns_newest_valid_artifacts_first(tmp_path):
    now = datetime.now(timezone.utc)
    older = write_snapshot(tmp_path, "RapidFireRonin_Repo_foundry", 14, "a" * 40, now - timedelta(hours=1))
    newer = write_snapshot(tmp_path, "RapidFireRonin_Repo_foundry", 15, "b" * 40, now)
    ignored = tmp_path / "RapidFireRonin_Repo_foundry" / "pr-16" / "bad.json"
    ignored.parent.mkdir(parents=True, exist_ok=True)
    ignored.write_text("not-json", encoding="utf-8")

    snapshots = read_pr_status_snapshots(tmp_path)

    assert [snapshot["pull_request"] for snapshot in snapshots] == [15, 14]
    assert snapshots[0]["artifact_path"] == str(newer)
    assert snapshots[1]["artifact_path"] == str(older)


def test_read_pr_status_snapshots_respects_limit(tmp_path):
    now = datetime.now(timezone.utc)
    for pr_number in range(1, 5):
        write_snapshot(tmp_path, "RapidFireRonin_Repo_foundry", pr_number, str(pr_number) * 40, now + timedelta(minutes=pr_number))

    snapshots = read_pr_status_snapshots(tmp_path, limit=2)

    assert [snapshot["pull_request"] for snapshot in snapshots] == [4, 3]
