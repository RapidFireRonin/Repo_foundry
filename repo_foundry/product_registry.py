"""Validation helpers for launchable product registry entries.

Repo Foundry can be asked to build games, business apps, dashboards, tools,
or automation systems. The product registry is the reusable contract that makes
those deliverables visible in Mission Control instead of buried in PR text.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


REQUIRED_PRODUCT_FIELDS = (
    "id",
    "title",
    "status",
    "kind",
    "description",
    "launch_url",
    "repo_url",
    "visual_proof",
    "test_evidence",
    "quality",
    "next_action",
    "last_verified",
)

VALID_STATUSES = {"planned", "in-progress", "playable", "usable", "blocked", "shipped"}


@dataclass(frozen=True)
class ProductRegistryIssue:
    """Human-readable registry validation issue."""

    product_id: str
    message: str


def load_product_registry(path: Path | str = "registry/products.yaml") -> dict[str, Any]:
    """Load the product registry YAML file."""

    registry_path = Path(path)
    with registry_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    if not isinstance(loaded, dict):
        raise ValueError("Product registry must be a YAML mapping with a products list.")
    return loaded


def validate_product_registry(registry: dict[str, Any]) -> list[ProductRegistryIssue]:
    """Return contract issues for product registry entries.

    The contract is intentionally product-agnostic. A text RPG, CRM, dashboard,
    browser utility, or automation deliverable all need the same visible proof:
    where to launch it, how it was verified, what quality verdict it earned,
    and what the next product-improving action is.
    """

    issues: list[ProductRegistryIssue] = []
    products = registry.get("products")
    if not isinstance(products, list) or not products:
        return [ProductRegistryIssue("<registry>", "products must be a non-empty list")]

    seen_ids: set[str] = set()
    for index, product in enumerate(products):
        product_id = _product_id(product, index)
        if not isinstance(product, dict):
            issues.append(ProductRegistryIssue(product_id, "product entry must be a mapping"))
            continue

        for field in REQUIRED_PRODUCT_FIELDS:
            if field not in product:
                issues.append(ProductRegistryIssue(product_id, f"missing required field: {field}"))

        raw_id = product.get("id")
        if isinstance(raw_id, str) and raw_id.strip():
            if raw_id in seen_ids:
                issues.append(ProductRegistryIssue(raw_id, "duplicate product id"))
            seen_ids.add(raw_id)
        else:
            issues.append(ProductRegistryIssue(product_id, "id must be a non-empty string"))

        status = product.get("status")
        if status not in VALID_STATUSES:
            issues.append(
                ProductRegistryIssue(
                    product_id,
                    f"status must be one of: {', '.join(sorted(VALID_STATUSES))}",
                )
            )

        for field in ("title", "kind", "description", "quality", "next_action", "last_verified"):
            if field in product and not _is_non_empty_string(product.get(field)):
                issues.append(ProductRegistryIssue(product_id, f"{field} must be a non-empty string"))

        for field in ("launch_url", "repo_url", "visual_proof"):
            if field in product and not _is_non_empty_string(product.get(field)):
                issues.append(ProductRegistryIssue(product_id, f"{field} must be a non-empty string"))

        evidence = product.get("test_evidence")
        if "test_evidence" in product and not _is_non_empty_string_list(evidence):
            issues.append(ProductRegistryIssue(product_id, "test_evidence must be a non-empty list of strings"))

    return issues


def assert_valid_product_registry(path: Path | str = "registry/products.yaml") -> None:
    """Raise a readable error when the registry violates the product contract."""

    issues = validate_product_registry(load_product_registry(path))
    if issues:
        details = "\n".join(f"- {issue.product_id}: {issue.message}" for issue in issues)
        raise AssertionError(f"Product registry contract failed:\n{details}")


def _product_id(product: Any, index: int) -> str:
    if isinstance(product, dict) and _is_non_empty_string(product.get("id")):
        return str(product["id"])
    return f"<product #{index + 1}>"


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_string(item) for item in value)
