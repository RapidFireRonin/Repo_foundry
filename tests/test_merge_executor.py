from repo_foundry.completion_policy import CheckStatus, PullRequestSnapshot
from repo_foundry.db import upsert_completion_pr
from repo_foundry.merge_executor import plan_or_merge


def test_successful_dry_run_merge_plan(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("REPO_FOUNDRY_DB", str(tmp_path / "rf.sqlite3"))
    pr = PullRequestSnapshot(
        number=9,
        title="Safe completion",
        url="https://github.com/RapidFireRonin/Repo_foundry/pull/9",
        branch="repo-foundry/safe",
        mergeable="MERGEABLE",
        changed_files=1,
        additions=5,
        deletions=1,
        files=["README.md"],
        checks=[
            CheckStatus(name="test", conclusion="SUCCESS"),
            CheckStatus(name="quality", conclusion="SUCCESS"),
            CheckStatus(name="secret-scan", conclusion="SUCCESS"),
        ],
        commit_sha="def456",
    )
    upsert_completion_pr(
        {
            "number": 9,
            "title": pr.title,
            "url": pr.url,
            "branch": pr.branch,
            "mergeable": pr.mergeable,
            "check_status": "ready",
            "failed_checks": [],
            "stale": False,
            "superseded_by": None,
            "decision": {"allowed": True},
            "payload": pr.model_dump(mode="json"),
        }
    )

    result = plan_or_merge("RapidFireRonin/Repo_foundry", 9, execute=False)

    assert result["status"] == "planned"
    assert result["decision"]["allowed"] is True
    assert "--squash" in result["command"]
