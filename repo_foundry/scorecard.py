from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


BASELINES = {
    "Foundation": 7,
    "Agent coordination": 6,
    "Actual UI control": 6,
    "Logging and visibility": 7,
    "Shipping loop": 7,
    "Safety": 5,
    "Usefulness today": 7,
    "Future potential": 9,
}


def status_for(score: int) -> str:
    if score >= 9:
        return "excellent"
    if score >= 7:
        return "stable"
    if score >= 5:
        return "needs_work"
    return "critical"


def build_scorecard(context: dict[str, Any]) -> dict[str, Any]:
    health = context.get("health", {})
    shipper = context.get("shipper", {})
    pr_status = context.get("pr_status", {})
    cycle = context.get("cycle", {})
    directions = context.get("directions", [])

    scores = dict(BASELINES)
    if health.get("overall_status") == "healthy":
        scores["Foundation"] += 1
    if shipper.get("exists") and shipper.get("last_run_at"):
        scores["Shipping loop"] += 1
    if pr_status.get("degraded"):
        scores["Logging and visibility"] -= 1
        scores["Shipping loop"] -= 1
    if pr_status.get("open_pr_count", 0) == 0:
        scores["Agent coordination"] += 1
        scores["Shipping loop"] += 1
    if any(item.get("status") == "active" for item in directions):
        scores["Actual UI control"] += 1
    if cycle.get("found"):
        scores["Logging and visibility"] += 1
        scores["Usefulness today"] += 1
    if context.get("token_warning", {}).get("detected"):
        scores["Safety"] -= 1

    metrics = []
    for name, raw_score in scores.items():
        score = max(0, min(10, raw_score))
        blockers: list[str] = []
        if name == "Safety" and context.get("token_warning", {}).get("detected"):
            blockers.append("Current GitHub credential appears broad.")
        if name == "Shipping loop" and pr_status.get("failed_check_count", 0):
            blockers.append("Some PR checks are failing.")
        if name == "Foundation" and health.get("failed_checks"):
            blockers.append(f"Local health warnings: {', '.join(health['failed_checks'][:4])}.")
        metrics.append({
            "name": name,
            "score": score,
            "status": status_for(score),
            "verdict": _verdict(name, score),
            "evidence": _evidence(name, context),
            "blocking_issues": blockers,
            "next_action": _next_action(name, blockers),
            "last_evaluated": datetime.now(timezone.utc).isoformat(),
        })

    overall = round(sum(item["score"] for item in metrics) / len(metrics), 1)
    return {"overall_score": overall, "metrics": metrics, "last_evaluated": datetime.now(timezone.utc).isoformat()}


def _verdict(name: str, score: int) -> str:
    if score >= 9:
        return f"{name} is strong and close to the 10/10 target."
    if score >= 7:
        return f"{name} is usable now, with clear next hardening steps."
    if score >= 5:
        return f"{name} works but needs attention before it feels dependable."
    return f"{name} is a blocker for autonomous operation."


def _evidence(name: str, context: dict[str, Any]) -> list[str]:
    common = ["Issue #13 scorecard", "dashboard Mission Control"]
    if name == "Shipping loop":
        return common + ["artifacts/pr-status/latest.json", str(context.get("shipper", {}).get("log_file") or "logs/repo-foundry-pr-shipper-*.log")]
    if name == "Logging and visibility":
        return common + ["docs/agent-cycle-log.md", "logs/repo-foundry-pr-shipper-*.log"]
    if name == "Safety":
        return common + ["docs/security/automation-credential-hardening.md", "policies/auto-merge.yaml"]
    return common


def _next_action(name: str, blockers: list[str]) -> str:
    if blockers:
        return blockers[0]
    if name == "Actual UI control":
        return "Use dashboard directions to steer the next agent cycle and verify agents respond."
    if name == "Safety":
        return "Rotate to a narrow GitHub automation credential."
    if name == "Usefulness today":
        return "Keep Mission Control as the first screen and add richer run history."
    return "Keep improving this metric with the next concrete deliverable."
