from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from repo_foundry.completion_policy import PolicyDecision, PullRequestSnapshot
from repo_foundry.models import repo_root


def completion_markdown(pr: PullRequestSnapshot, decision: PolicyDecision, merged: bool, rollback_note: str) -> str:
    checks = ", ".join(f"{check.name}:{check.conclusion or check.status}" for check in pr.checks) or "none"
    return (
        f"\n## Completion {datetime.now(timezone.utc).isoformat()}\n\n"
        f"- PR: [{pr.title}]({pr.url})\n"
        f"- PR number: #{pr.number}\n"
        f"- Commit SHA: `{pr.commit_sha or 'unknown'}`\n"
        f"- Merged: `{str(merged).lower()}`\n"
        f"- Checks: {checks}\n"
        f"- Risk: {decision.risk}\n"
        f"- Policy: {'allowed' if decision.allowed else 'blocked'}\n"
        f"- Reasons: {', '.join(decision.reasons) if decision.reasons else 'none'}\n"
        f"- Rollback note: {rollback_note}\n"
    )


def append_completion_log(
    pr: PullRequestSnapshot,
    decision: PolicyDecision,
    merged: bool,
    rollback_note: str,
    path: Path | None = None,
) -> Path:
    target = path or repo_root() / "AGENT_CYCLE_LOG.md"
    with target.open("a", encoding="utf-8") as fh:
        fh.write(completion_markdown(pr, decision, merged, rollback_note))
    return target

