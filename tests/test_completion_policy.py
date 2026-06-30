from repo_foundry.completion_log import completion_markdown
from repo_foundry.completion_policy import AutoMergePolicy, CheckStatus, PullRequestSnapshot, evaluate_policy


def base_policy() -> AutoMergePolicy:
    return AutoMergePolicy(
        allowed_branches=["repo-foundry/*"],
        required_checks=["CI"],
        max_changed_files=3,
        max_additions=100,
        max_deletions=50,
        blocked_paths=[".env", "secrets/**"],
        dangerous_operations=["delete-repo"],
    )


def base_pr() -> PullRequestSnapshot:
    return PullRequestSnapshot(
        number=7,
        title="Safe change",
        url="https://github.com/RapidFireRonin/Repo_foundry/pull/7",
        branch="repo-foundry/safe-change",
        mergeable="MERGEABLE",
        changed_files=1,
        additions=10,
        deletions=2,
        files=["README.md"],
        checks=[CheckStatus(name="CI", conclusion="SUCCESS")],
        commit_sha="abc123",
    )


def test_policy_allows_safe_pr_with_audit() -> None:
    decision = evaluate_policy(base_pr(), base_policy(), audit_present=True)

    assert decision.allowed is True
    assert decision.reasons == []


def test_failed_checks_block_merge() -> None:
    pr = base_pr()
    pr.checks = [CheckStatus(name="CI", conclusion="FAILURE")]

    decision = evaluate_policy(pr, base_policy(), audit_present=True)

    assert decision.allowed is False
    assert "failing checks" in " ".join(decision.reasons)


def test_unknown_checks_block_merge() -> None:
    pr = base_pr()
    pr.checks = [CheckStatus(name="CI", status="IN_PROGRESS")]

    decision = evaluate_policy(pr, base_policy(), audit_present=True)

    assert decision.allowed is False
    assert "unknown checks" in " ".join(decision.reasons)


def test_path_denylist_blocks_merge() -> None:
    pr = base_pr()
    pr.files = [".env"]

    decision = evaluate_policy(pr, base_policy(), audit_present=True)

    assert decision.allowed is False
    assert "blocked paths" in " ".join(decision.reasons)


def test_oversized_pr_blocks_merge() -> None:
    pr = base_pr()
    pr.changed_files = 10
    pr.additions = 200

    decision = evaluate_policy(pr, base_policy(), audit_present=True)

    assert decision.allowed is False
    assert "changed files" in " ".join(decision.reasons)
    assert "additions" in " ".join(decision.reasons)


def test_missing_audit_blocks_merge() -> None:
    decision = evaluate_policy(base_pr(), base_policy(), audit_present=False)

    assert decision.allowed is False
    assert "audit" in " ".join(decision.reasons)


def test_completion_log_entry_contains_required_fields() -> None:
    pr = base_pr()
    decision = evaluate_policy(pr, base_policy(), audit_present=True)

    markdown = completion_markdown(pr, decision, merged=True, rollback_note="Revert abc123.")

    assert "Commit SHA" in markdown
    assert "abc123" in markdown
    assert "Rollback note" in markdown
    assert "Checks" in markdown
