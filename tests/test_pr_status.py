from __future__ import annotations

from repo_foundry.pr_status import dependency_files_changed, operator_summary, snapshot_from_gh_item, write_pr_status_artifacts


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


def test_operator_summary_clear_when_no_open_prs():
    summary = operator_summary([])

    assert summary["status"] == "clear"
    assert "No open PRs" in summary["summary"]
    assert "issue #13" in summary["next_action"]


def test_operator_summary_blocks_dirty_or_failed_prs():
    summary = operator_summary([
        {"number": 7, "shipper_recommendation": "rebuild", "failed_checks": []},
        {"number": 8, "shipper_recommendation": "fix_checks", "failed_checks": ["Security Checks"]},
    ])

    assert summary["status"] == "blocked"
    assert "need repair" in summary["summary"]


def test_pr_status_artifacts_written(tmp_path):
    payload = {"generated_at": "now", "summary": "No open PRs.", "operator_summary": {"status": "clear", "summary": "No open PRs are waiting on the completion loop.", "next_action": "Pick one safe improvement."}, "pull_requests": []}

    paths = write_pr_status_artifacts(payload, tmp_path)

    assert (tmp_path / "latest.json").exists()
    assert (tmp_path / "latest.md").exists()
    assert "Operator Summary" in (tmp_path / "latest.md").read_text(encoding="utf-8")
    assert paths["json"].endswith("latest.json")


def test_dependency_file_detection():
    assert dependency_files_changed(["dashboard/frontend/package.json"])
    assert not dependency_files_changed(["repo_foundry/api.py"])
