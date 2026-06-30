from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repo_foundry.models import repo_root


IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


def collect_visual_evidence(root: Path | None = None) -> dict[str, Any]:
    base = root or repo_root()
    visual_root = base / "artifacts" / "visuals"
    items: list[dict[str, Any]] = []
    if visual_root.exists():
        for path in sorted(visual_root.rglob("*"), key=lambda item: item.stat().st_mtime, reverse=True):
            if path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue
            rel = path.relative_to(base).as_posix()
            items.append({
                "title": path.stem.replace("-", " ").replace("_", " ").title(),
                "path": rel,
                "url": f"/{rel}",
                "kind": "screenshot",
                "captured_at": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                "verdict": "Visual proof artifact is available.",
            })

    expected = [
        {
            "title": "Mission Control mobile proof",
            "path": "artifacts/visuals/mission-control-mobile.png",
            "purpose": "Shows the phone view Garrett uses to direct agents and inspect status.",
        },
        {
            "title": "Mission Control desktop proof",
            "path": "artifacts/visuals/mission-control-desktop.png",
            "purpose": "Shows the full control-room layout with scorecard, activity, and evidence.",
        },
    ]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": f"{len(items)} visual proof artifact(s) available." if items else "No visual proof screenshots found yet.",
        "items": items[:8],
        "expected": expected,
        "next_action": "Run the dashboard smoke test and save screenshots under artifacts/visuals/.",
    }
