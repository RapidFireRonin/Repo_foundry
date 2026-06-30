from datetime import datetime, timezone
import json

from repo_foundry.completion_policy import CheckStatus, PullRequestSnapshot
from repo_foundry.pr_monitor import (
    checks_summary,
    normalize_mergeable,
    snapshot_artifact_path,
    status_snapshot_from_pr,
    write_snapshot_artifacts,
)


def make_pr(**overrides):
    values = {
        "number": 14,
        "title": "Add clean PR status snapshot schema",
        "url": "https://github.com/RapidFireRonin/Repo_foundry/pull/14",
        "branch": "builder/pr-snapshot-emitter",
        "base_branch": "main",
        "mergeable": "MERGEABLE",
        "changed_files": 2,
        "additions": 50,
        "deletions": 0,
        "files": ["repo_foundry/pr_monitor.py", "tests/test_pr_monitor_snapshots.py"],
        "checks": [CheckStatus(name="CI", status="COMPLETED", conclusion="SUCCESS")],
        "updated_at": datetime.now(timezone.utc),
        "commit_sha": "a" * 40,
    }
    values.update(overrides)
    return PullRequestSnapshot(**values)


def test_normalize_mergeable_matches_schema_type():
    assert normalize_mergeable("MERGEABLE") is True
    assert normalize_mergeable("CONFLICTING") is False
    assert normalize_mergeable("UNKNOWN") is None


def test_checks_summary_counts_success_failure_and_unknown():
    pr = make_pr(
        checks=[
            CheckStatus(name="CI", status="COMPLETED", conclusion="SUCCESS"),
            CheckStatus(name="Security", status="COMPLETED", conclusion="FAILURE"),
            CheckStatus(name="Queued", status="QUEUED", conclusion=None),
        ]
    )

    summary = checks_summary(pr)

    assert summary["total_count"] == 3
    assert summary["failing_count"] == 1
    assert summary["unknown_count"] == 1
    assert summary["conclusion"] == "failure"


def test_status_snapshot_from_pr_matches_core_schema_fields():
    snapshot = status_snapshot_from_pr("RapidFireRonin/Repo_foundry", make_pr())

    assert snapshot["schema_version"] == "pr-status-snapshot/v1"
    assert snapshot["repository"] == "RapidFireRonin/Repo_foundry"
    assert snapshot["pull_request"] == 14
    assert snapshot["head_sha"] == "a" * 40
    assert snapshot["mergeable"] is True
    assert snapshot["checks"]["conclusion"] == "success"
    assert snapshot["policy_decision"] in {"eligible", "blocked", "watch", "manual_review_required"}
    assert snapshot["risk_note"]
    assert snapshot["rollback_note"]


def test_write_snapshot_artifacts_uses_dashboard_contract_path(tmp_path):
    pr = make_pr()
    paths = write_snapshot_artifacts("RapidFireRonin/Repo_foundry", [pr], tmp_path, "policies/auto-merge.yaml")

    assert paths == [snapshot_artifact_path(tmp_path, "RapidFireRonin/Repo_foundry", pr)]
    written = json.loads(paths[0].read_text(encoding="utf-8"))
    assert written["schema_version"] == "pr-status-snapshot/v1"
    assert written["display_url"].endswith("/pull/14")
