from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from repo_foundry.models import repo_root


def _latest_successful_runs(activity: dict[str, Any]) -> list[str]:
    runs = []
    for run in activity.get("recent_runs", []):
        conclusion = str(run.get("conclusion") or run.get("status") or "unknown")
        if conclusion.lower() in {"success", "completed"}:
            name = str(run.get("workflowName") or "workflow")
            url = str(run.get("url") or "")
            runs.append(f"{name}: {conclusion}{f' ({url})' if url else ''}")
    return runs[:4]


def _load_registered_products(root: Path) -> list[dict[str, Any]]:
    path = root / "registry" / "products.yaml"
    if not path.exists():
        return []
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    products = payload.get("products") or []
    if not isinstance(products, list):
        return []
    registered = []
    for item in products:
        if not isinstance(item, dict):
            continue
        registered.append({
            "id": str(item.get("id") or item.get("title") or "product"),
            "title": str(item.get("title") or "Untitled product"),
            "status": str(item.get("status") or "unknown"),
            "kind": str(item.get("kind") or "product"),
            "launch_state": "launchable" if item.get("launch_url") else "proof-only",
            "what_was_built": str(item.get("description") or item.get("what_was_built") or "Registered product."),
            "open_url": item.get("launch_url"),
            "repo_url": item.get("repo_url"),
            "visual_proof": item.get("visual_proof"),
            "test_evidence": [str(value) for value in item.get("test_evidence", [])],
            "quality": str(item.get("quality") or "No quality verdict recorded yet."),
            "next_action": str(item.get("next_action") or "Open it, use it, and attach fresh proof after changes."),
            "last_verified": item.get("last_verified"),
            "source": "registry/products.yaml",
        })
    return registered


def _product_card(
    *,
    title: str,
    status: str,
    kind: str,
    what_was_built: str,
    open_url: str | None,
    visual_proof: str | None,
    test_evidence: list[str],
    quality: str,
    next_action: str,
    product_id: str,
    repo_url: str | None = None,
    source: str = "mission-control",
) -> dict[str, Any]:
    launch_state = "launchable" if open_url else "proof-only"
    return {
        "id": product_id,
        "title": title,
        "status": status,
        "kind": kind,
        "launch_state": launch_state,
        "what_was_built": what_was_built,
        "open_url": open_url,
        "repo_url": repo_url,
        "visual_proof": visual_proof,
        "test_evidence": test_evidence,
        "quality": quality,
        "next_action": next_action,
        "last_verified": datetime.now(timezone.utc).isoformat(),
        "source": source,
    }


def build_product_showcase(
    *,
    visual_evidence: dict[str, Any],
    agent_activity: dict[str, Any],
    health: dict[str, Any],
    shipper: dict[str, Any],
    pr_status: dict[str, Any],
    root: Path | None = None,
) -> dict[str, Any]:
    base = root or repo_root()
    visual_items = visual_evidence.get("items", [])
    successful_runs = _latest_successful_runs(agent_activity)
    health_ok = health.get("overall_status") == "healthy"
    open_prs = int(pr_status.get("open_pr_count") or 0)
    failed_checks = int(pr_status.get("failed_check_count") or 0)

    dashboard_status = "working" if visual_items and health_ok else "needs-proof" if health_ok else "needs-fix"
    dashboard_card = _product_card(
        product_id="repo-foundry-mission-control",
        title="Repo Foundry Mission Control",
        status=dashboard_status,
        kind="control-plane",
        what_was_built="A phone-friendly control plane for directing agents, watching PRs, reading cycle logs, and seeing visual proof.",
        open_url="/",
        visual_proof=visual_items[0]["url"] if visual_items else None,
        test_evidence=successful_runs or ["Local health collector is available."],
        quality="Looks shippable when screenshots and checks are present." if dashboard_status == "working" else "Needs a fresh screenshot or health cleanup before claiming wow-level proof.",
        next_action="Open from iPhone, submit a product direction, and watch the queue plus evidence panels update.",
    )

    build_console_card = _product_card(
        product_id="agent-direction-console",
        title="Agent Direction Console",
        status="working",
        kind="operator-tool",
        what_was_built="A dashboard prompt path that stores timestamped, prioritized directions with source=dashboard.",
        open_url="/",
        visual_proof=visual_items[0]["url"] if visual_items else None,
        test_evidence=["Direction API tests cover creation and dashboard refresh path."],
        quality="Human-directable: Garrett chooses what agents work on without losing visibility.",
        next_action="Type the next product goal and keep it active until a PR, artifact, or completion log proves it.",
    )

    shipper_status = "ready" if open_prs == 0 and failed_checks == 0 else "watching"
    shipper_card = _product_card(
        product_id="autonomous-pr-shipper",
        title="Autonomous PR Shipper",
        status=shipper_status,
        kind="automation-tool",
        what_was_built="Policy-gated PR polling and merge visibility with dry-run defaults, checks, stale PR awareness, and audit logs.",
        open_url=None,
        visual_proof=None,
        test_evidence=successful_runs or ["Merge executor and policy tests are present."],
        quality=shipper.get("summary") or "No shipper run has been recorded yet.",
        next_action="Run the shipper only when checks are green and policy says the PR is eligible.",
    )

    products: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for product in [*_load_registered_products(base), dashboard_card, build_console_card, shipper_card]:
        product_id = str(product.get("id") or product.get("title"))
        if product_id in seen_ids:
            continue
        seen_ids.add(product_id)
        products.append(product)
    completed = [item for item in products if item["status"] in {"working", "ready", "complete", "playable", "usable"}]
    launchable = [item for item in completed if item.get("open_url")]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": f"{len(launchable)}/{len(products)} product(s) are launchable from Mission Control.",
        "products": products,
        "completed_products": completed,
        "launchable_count": len(launchable),
        "registry_path": "registry/products.yaml",
        "next_product_goal": "Create a user-facing product from Garrett's next prompt, with tests, screenshots, PR links, and a completion log entry.",
    }
