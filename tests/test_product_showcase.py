from __future__ import annotations

from repo_foundry.product_showcase import build_product_showcase


def test_product_showcase_surfaces_working_products_with_proof():
    payload = build_product_showcase(
        visual_evidence={"items": [{"url": "/artifacts/visuals/mission-control-mobile.png"}]},
        agent_activity={"recent_runs": [{"workflowName": "CI", "conclusion": "success", "url": "https://example.test/run"}]},
        health={"overall_status": "healthy"},
        shipper={"summary": "No open PRs waiting."},
        pr_status={"open_pr_count": 0, "failed_check_count": 0},
    )

    assert payload["summary"].startswith("3/3")
    assert payload["products"][0]["status"] == "working"
    assert payload["products"][0]["visual_proof"] == "/artifacts/visuals/mission-control-mobile.png"
    assert "CI: success" in payload["products"][0]["test_evidence"][0]
