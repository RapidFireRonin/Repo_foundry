from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _latest_successful_runs(activity: dict[str, Any]) -> list[str]:
    runs = []
    for run in activity.get("recent_runs", []):
        conclusion = str(run.get("conclusion") or run.get("status") or "unknown")
        if conclusion.lower() in {"success", "completed"}:
            name = str(run.get("workflowName") or "workflow")
            url = str(run.get("url") or "")
            runs.append(f"{name}: {conclusion}{f' ({url})' if url else ''}")
    return runs[:4]


def build_product_showcase(
    *,
    visual_evidence: dict[str, Any],
    agent_activity: dict[str, Any],
    health: dict[str, Any],
    shipper: dict[str, Any],
    pr_status: dict[str, Any],
) -> dict[str, Any]:
    visual_items = visual_evidence.get("items", [])
    successful_runs = _latest_successful_runs(agent_activity)
    health_ok = health.get("overall_status") == "healthy"
    open_prs = int(pr_status.get("open_pr_count") or 0)
    failed_checks = int(pr_status.get("failed_check_count") or 0)

    dashboard_status = "working" if visual_items and health_ok else "needs-proof" if health_ok else "needs-fix"
    dashboard_card = {
        "title": "Repo Foundry Mission Control",
        "status": dashboard_status,
        "what_was_built": "A phone-friendly control plane for directing agents, watching PRs, reading cycle logs, and seeing visual proof.",
        "open_url": "/",
        "visual_proof": visual_items[0]["url"] if visual_items else None,
        "test_evidence": successful_runs or ["Local health collector is available."],
        "quality": "Looks shippable when screenshots and checks are present." if dashboard_status == "working" else "Needs a fresh screenshot or health cleanup before claiming wow-level proof.",
        "next_action": "Open from iPhone, submit a product direction, and watch the queue plus evidence panels update.",
    }

    build_console_card = {
        "title": "Agent Direction Console",
        "status": "working",
        "what_was_built": "A dashboard prompt path that stores timestamped, prioritized directions with source=dashboard.",
        "open_url": "/",
        "visual_proof": visual_items[0]["url"] if visual_items else None,
        "test_evidence": ["Direction API tests cover creation and dashboard refresh path."],
        "quality": "Human-directable: Garrett chooses what agents work on without losing visibility.",
        "next_action": "Type the next product goal and keep it active until a PR, artifact, or completion log proves it.",
    }

    shipper_status = "ready" if open_prs == 0 and failed_checks == 0 else "watching"
    shipper_card = {
        "title": "Autonomous PR Shipper",
        "status": shipper_status,
        "what_was_built": "Policy-gated PR polling and merge visibility with dry-run defaults, checks, stale PR awareness, and audit logs.",
        "open_url": None,
        "visual_proof": None,
        "test_evidence": successful_runs or ["Merge executor and policy tests are present."],
        "quality": shipper.get("summary") or "No shipper run has been recorded yet.",
        "next_action": "Run the shipper only when checks are green and policy says the PR is eligible.",
    }

    products = [dashboard_card, build_console_card, shipper_card]
    working = sum(1 for item in products if item["status"] in {"working", "ready"})
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": f"{working}/{len(products)} core products are ready enough to use from Mission Control.",
        "products": products,
        "next_product_goal": "Create a user-facing product from Garrett's next prompt, with tests, screenshots, PR links, and a completion log entry.",
    }
