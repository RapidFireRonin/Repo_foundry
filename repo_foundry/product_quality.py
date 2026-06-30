from __future__ import annotations

from typing import Any


DONE_STATUSES = {"usable", "playable", "complete"}
VISUAL_KINDS = {"game", "web-app", "tool", "operator-tool", "control-plane"}
WEAK_QUALITY_PHRASES = {
    "looks shippable",
    "no quality verdict",
    "todo",
    "tbd",
    "needs proof",
    "placeholder",
}


def evaluate_product_quality(product: dict[str, Any]) -> dict[str, Any]:
    """Return a blunt, dashboard-readable quality gate for a product card."""

    status = str(product.get("status") or "unknown").lower()
    kind = str(product.get("kind") or "product").lower()
    title = str(product.get("title") or "Untitled product")
    description = str(product.get("what_was_built") or product.get("description") or "")
    quality = str(product.get("quality") or "")
    test_evidence = [str(item) for item in product.get("test_evidence", []) if str(item).strip()]

    blockers: list[str] = []
    polish: list[str] = []
    strengths: list[str] = []
    score = 0

    if product.get("open_url"):
        score += 2
        strengths.append("launchable")
    elif status in DONE_STATUSES:
        blockers.append("Missing launch URL for a product marked done.")
    else:
        polish.append("Add a launch URL when this becomes usable.")

    if product.get("visual_proof"):
        score += 2
        strengths.append("visual proof")
    elif kind in VISUAL_KINDS:
        blockers.append("Missing screenshot or visual proof.")
    else:
        polish.append("Attach inspection proof.")

    if len(test_evidence) >= 2:
        score += 2
        strengths.append("multiple test/playtest evidence items")
    elif test_evidence:
        score += 1
        blockers.append("Only one test or playtest evidence item is recorded.")
    else:
        blockers.append("Missing test or playtest evidence.")

    if len(quality.strip()) >= 40 and not any(phrase in quality.lower() for phrase in WEAK_QUALITY_PHRASES):
        score += 2
        strengths.append("specific quality verdict")
    else:
        blockers.append("Quality verdict is missing, too vague, or placeholder-like.")

    if product.get("last_verified"):
        score += 1
        strengths.append("verification timestamp")
    else:
        polish.append("Add last_verified after a real smoke test or playtest.")

    if str(product.get("next_action") or "").strip():
        score += 1
        strengths.append("next action")
    else:
        polish.append("Add the next recommended action.")

    if status in DONE_STATUSES and not description.strip():
        blockers.append(f"{title} is marked {status} without a clear description of what was built.")

    if kind == "game":
        proof_text = " ".join([description, quality, *test_evidence]).lower()
        if not any(term in proof_text for term in ("play", "playable", "loop", "controls", "save", "restart", "level", "puzzle")):
            blockers.append("Game entry does not prove a real playable interaction loop.")

    score = min(score, 10)
    if blockers:
        gate_status = "blocked"
        verdict = "Not good enough to call done."
        can_claim_done = False
    elif score >= 8:
        gate_status = "passes"
        verdict = "Good enough to present as usable or playable."
        can_claim_done = True
    else:
        gate_status = "needs-polish"
        verdict = "Visible, but not strong enough yet."
        can_claim_done = False

    return {
        "status": gate_status,
        "score": score,
        "verdict": verdict,
        "can_claim_done": can_claim_done,
        "blockers": blockers,
        "polish": polish,
        "strengths": strengths,
    }
