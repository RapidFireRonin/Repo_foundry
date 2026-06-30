from __future__ import annotations

from repo_foundry.pr_status import dependency_files_changed, snapshot_from_gh_item, write_pr_status_artifacts


def test_pr_status_snapshot_recommends_fix_checks():
    item = {
        "number": 5,
        "title": "Fix adapter",
        "url": "https://example.test/pr/5",
        "mergeable": "MERGEABLE",
        "isDraft": False,
        "changedFiles": 1,
        "files": [{"path": "repo_foundry/api.py"}],
        "statusCheckRollup": [{"name": "secret-scan", "status": "COMPLETED", "conclusion": "FAILURE"}],
    }

    snapshot = snapshot_from_gh_item("owner/repo", item)

    assert snapshot["check_status"] == "failed"
    assert snapshot["failed_checks"] == ["secret-scan"]
    assert snapshot["shipper_recommendation"] == "fix_checks"


def test_pr_status_artifacts_written(tmp_path):
    payload = {"generated_at": "now", "summary": "No open PRs.", "pull_requests": []}

    paths = write_pr_status_artifacts(payload, tmp_path)

    assert (tmp_path / "latest.json").exists()
    assert (tmp_path / "latest.md").exists()
    assert paths["json"].endswith("latest.json")


def test_dependency_file_detection():
    assert dependency_files_changed(["dashboard/frontend/package.json"])
    assert not dependency_files_changed(["repo_foundry/api.py"])
