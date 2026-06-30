from __future__ import annotations

import argparse
from pathlib import Path

from repo_foundry.audit import write_audit_event
from repo_foundry.models import CycleSummary, repo_root


def sample_summary() -> CycleSummary:
    return CycleSummary(
        founder_strategist="Confirmed Repo Foundry priorities: autonomous execution, visibility, audit trails, and hourly reporting.",
        architect="Maintained desired-state blueprint model and local dashboard architecture.",
        builder="Updated scaffolding, validation, reconcile planning, dashboard data, and tests.",
        reviewer_debugger="Checked validation and planning behavior for dangerous operations and missing repo state.",
        research_scout="Added security backlog for Actions permissions, runner safety, OIDC, artifacts, audit trails, and PR-only rules.",
        prs_opened_updated=[],
        failed_checks=[],
        artifacts_logs=["docs/agent-cycle-log.md", "logs/audit.jsonl"],
        autonomous_watch_items=["Monitor high-impact autonomous actions in the dashboard watchlist."],
        next_recommended_action="Run autonomous reconcile apply from a scheduled workflow after GitHub credentials are configured.",
    )


def append_summary(summary: CycleSummary, path: Path | None = None) -> Path:
    target = path or repo_root() / "docs" / "agent-cycle-log.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as fh:
        fh.write(summary.to_markdown())
    write_audit_event("cycle_summary_append", str(target), timestamp=summary.timestamp.isoformat())
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description="Append hourly cycle summaries.")
    sub = parser.add_subparsers(dest="command", required=True)
    append = sub.add_parser("append")
    append.add_argument("--from-sample", action="store_true")
    args = parser.parse_args()

    if args.command == "append":
        if not args.from_sample:
            raise SystemExit("--from-sample is currently required until live cycle ingestion is connected")
        target = append_summary(sample_summary())
        print(f"appended cycle summary: {target}")


if __name__ == "__main__":
    main()
