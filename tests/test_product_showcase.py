from __future__ import annotations

from repo_foundry.product_showcase import build_product_showcase


def test_product_showcase_surfaces_working_products_with_proof(tmp_path):
    payload = build_product_showcase(
        visual_evidence={"items": [{"url": "/artifacts/visuals/mission-control-mobile.png"}]},
        agent_activity={"recent_runs": [{"workflowName": "CI", "conclusion": "success", "url": "https://example.test/run"}]},
        health={"overall_status": "healthy"},
        shipper={"summary": "No open PRs waiting."},
        pr_status={"open_pr_count": 0, "failed_check_count": 0},
        root=tmp_path,
    )

    assert payload["summary"].startswith("2/3")
    assert payload["products"][0]["status"] == "working"
    assert payload["products"][0]["launch_state"] == "launchable"
    assert payload["products"][0]["visual_proof"] == "/artifacts/visuals/mission-control-mobile.png"
    assert "CI: success" in payload["products"][0]["test_evidence"][0]


def test_product_showcase_loads_registered_launchable_products(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "products.yaml").write_text(
        """
        products:
          - id: playable-demo
            title: Playable Demo
            status: playable
            kind: game
            description: A playable test product.
            launch_url: http://127.0.0.1:7777
            visual_proof: /artifacts/visuals/demo.png
            test_evidence:
              - smoke test passed
        """,
        encoding="utf-8",
    )

    payload = build_product_showcase(
        visual_evidence={"items": []},
        agent_activity={"recent_runs": []},
        health={"overall_status": "healthy"},
        shipper={"summary": "No open PRs waiting."},
        pr_status={"open_pr_count": 0, "failed_check_count": 0},
        root=tmp_path,
    )

    assert payload["registry_path"] == "registry/products.yaml"
    assert payload["completed_products"][0]["title"] == "Playable Demo"
    assert payload["completed_products"][0]["launch_state"] == "launchable"
    assert payload["launchable_count"] >= 1
