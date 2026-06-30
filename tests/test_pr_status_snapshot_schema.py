import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "pr-status-snapshot.schema.json"


def load_schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def test_pr_status_snapshot_schema_is_valid_json():
    schema = load_schema()
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["title"] == "Repo Foundry PR Status Snapshot"
    assert schema["additionalProperties"] is False


def test_pr_status_snapshot_schema_requires_policy_and_visibility_fields():
    schema = load_schema()
    required = set(schema["required"])

    assert "repository" in required
    assert "pull_request" in required
    assert "head_sha" in required
    assert "mergeable" in required
    assert "checks" in required
    assert "policy_decision" in required
    assert "risk_note" in required
    assert "rollback_note" in required


def test_pr_status_snapshot_policy_decisions_are_bounded():
    schema = load_schema()
    decisions = schema["properties"]["policy_decision"]["enum"]

    assert decisions == [
        "eligible",
        "blocked",
        "watch",
        "manual_review_required",
    ]


def test_pr_status_snapshot_checks_summary_is_required_and_bounded():
    schema = load_schema()
    checks = schema["properties"]["checks"]

    assert checks["additionalProperties"] is False
    assert set(checks["required"]) == {
        "status",
        "conclusion",
        "total_count",
        "failing_count",
        "unknown_count",
        "runs",
    }
    assert checks["properties"]["status"]["enum"] == [
        "queued",
        "in_progress",
        "completed",
        "unknown",
    ]
