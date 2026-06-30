from __future__ import annotations

from repo_foundry.scorecard import build_scorecard


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
