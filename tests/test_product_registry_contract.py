from pathlib import Path

import pytest

from repo_foundry.product_registry import (
    ProductRegistryIssue,
    assert_valid_product_registry,
    load_product_registry,
    validate_product_registry,
)


ROOT = Path(__file__).resolve().parents[1]


def test_current_product_registry_satisfies_launchable_product_contract() -> None:
    assert_valid_product_registry(ROOT / "registry" / "products.yaml")


def test_product_registry_requires_launch_proof_and_test_evidence() -> None:
    issues = validate_product_registry(
        {
            "products": [
                {
                    "id": "thin-demo",
                    "title": "Thin Demo",
                    "status": "playable",
                    "kind": "game",
                    "description": "A demo missing proof fields.",
                    "launch_url": "/thin-demo.html",
                }
            ]
        }
    )

    messages = {issue.message for issue in issues}
    assert "missing required field: visual_proof" in messages
    assert "missing required field: test_evidence" in messages
    assert "missing required field: quality" in messages
    assert "missing required field: next_action" in messages


def test_product_registry_rejects_duplicate_product_ids() -> None:
    base_product = {
        "id": "chrono-rift",
        "title": "Chrono Rift",
        "status": "playable",
        "kind": "game",
        "description": "Playable text RPG.",
        "launch_url": "/chrono-rift.html",
        "repo_url": "https://github.com/RapidFireRonin/Repo_foundry",
        "visual_proof": "/artifacts/visuals/chrono-rift-gallery.png",
        "test_evidence": ["Browser smoke opens the game."],
        "quality": "Playable first slice.",
        "next_action": "Add a second playable chapter slice.",
        "last_verified": "2026-06-30",
    }

    issues = validate_product_registry({"products": [base_product, dict(base_product)]})

    assert ProductRegistryIssue("chrono-rift", "duplicate product id") in issues


def test_product_registry_loader_requires_mapping(tmp_path: Path) -> None:
    registry_path = tmp_path / "products.yaml"
    registry_path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Product registry must be a YAML mapping"):
        load_product_registry(registry_path)
