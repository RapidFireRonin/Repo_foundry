import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_autonomous_completion_policy_is_bounded():
    policy = json.loads((ROOT / "policies" / "autonomous-completion-policy.json").read_text(encoding="utf-8"))
    assert policy["enabled"] is True
    assert policy["execute"] is True
    assert policy["max_merges_per_run"] <= 3
    assert policy["max_files_changed"] <= 30
    assert "dependency-review" in policy["ignorable_failed_checks_without_dependency_changes"]
    assert ".env" in policy["blocked_path_prefixes"]


def test_autonomous_completion_script_exists_and_fails_closed():
    script = (ROOT / "scripts" / "autonomous_completion.py").read_text(encoding="utf-8")
    assert "No GitHub credential available; fail closed." in script
    assert "merge_pr" in script
    assert "blocked_files" in script
    assert "changed_dependency_files" in script


def test_autonomous_completion_workflow_is_report_only_by_default():
    workflow = (ROOT / ".github" / "workflows" / "autonomous-completion.yml").read_text(encoding="utf-8")
    assert "schedule:" in workflow
    assert "SWEEPER_EXECUTE: \"false\"" in workflow
    assert "contents: read" in workflow
