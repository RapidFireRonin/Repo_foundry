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
    assert payload["completed_products"][0]["quality_gate"]["status"] == "blocked"
    assert "Quality verdict" in " ".join(payload["completed_products"][0]["quality_gate"]["blockers"])
    assert payload["launchable_count"] >= 1


def test_product_showcase_quality_gate_passes_strong_playable_product(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "products.yaml").write_text(
        """
        products:
          - id: playable-demo
            title: Playable Demo
            status: playable
            kind: game
            description: A playable loop with controls, restart, and a puzzle goal.
            launch_url: /playable-demo.html
            visual_proof: /artifacts/visuals/demo.png
            test_evidence:
              - Browser smoke opened the playable route.
              - Playtest covered controls, restart, and puzzle completion.
            quality: A real playable slice with a clear loop, visible proof, and enough evidence to judge the experience.
            next_action: Add a second level and automated regression playtest.
            last_verified: "2026-06-30"
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

    product = payload["completed_products"][0]
    assert product["quality_gate"]["can_claim_done"] is True
    assert product["quality_gate"]["score"] == 10
    assert payload["quality_passed_count"] >= 1


def test_product_showcase_quality_gate_blocks_fake_done_product(tmp_path):
    registry = tmp_path / "registry"
    registry.mkdir()
    (registry / "products.yaml").write_text(
        """
        products:
          - id: fake-demo
            title: Fake Demo
            status: playable
            kind: game
            description: A vague idea.
            quality: Looks shippable.
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

    gate = payload["completed_products"][0]["quality_gate"]
    assert gate["can_claim_done"] is False
    assert gate["status"] == "blocked"
    assert "Missing launch URL" in " ".join(gate["blockers"])
    assert "Missing screenshot" in " ".join(gate["blockers"])
    assert "Missing test" in " ".join(gate["blockers"])
