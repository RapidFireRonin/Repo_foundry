from __future__ import annotations

from repo_foundry.scorecard import build_scorecard
from repo_foundry.mission_control import product_controls


def test_scorecard_generation_shape():
    scorecard = build_scorecard(
        {
            "health": {"overall_status": "healthy"},
            "shipper": {"exists": True, "last_run_at": "2026-06-30 01:00:00"},
            "pr_status": {"open_pr_count": 0, "failed_check_count": 0},
            "cycle": {"found": True},
            "directions": [{"status": "active"}],
            "token_warning": {"detected": True},
        }
    )

    assert scorecard["overall_score"] > 0
    assert len(scorecard["metrics"]) == 8
    assert {metric["name"] for metric in scorecard["metrics"]} >= {"Foundation", "Safety"}


def test_product_controls_offer_interactive_builds():
    scorecard = build_scorecard(
        {
            "health": {"overall_status": "healthy"},
            "shipper": {"exists": True, "last_run_at": "2026-06-30 01:00:00"},
            "pr_status": {"open_pr_count": 0, "failed_check_count": 0},
            "cycle": {"found": True},
            "directions": [],
            "token_warning": {"detected": False},
            "agent_activity": {"quality_verdicts": [{"title": "CI", "status": "success"}]},
            "visual_evidence": {"items": []},
        }
    )

    controls = product_controls(scorecard, [], {"items": []})

    assert controls["operator_prompt"] == "What product should the agents build next?"
    assert controls["suggested_builds"][0]["title"] == "Generate visual proof for Mission Control"
    assert controls["suggested_builds"][1]["title"] == "Build the agent proof stream"
