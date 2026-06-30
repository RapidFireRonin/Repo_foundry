from __future__ import annotations

from pathlib import Path
from typing import Any

from repo_foundry.models import repo_root


def cycle_log_paths(root: Path | None = None) -> list[Path]:
    base = root or repo_root()
    return [base / "AGENT_CYCLE_LOG.md", base / "docs" / "agent-cycle-log.md"]


def parse_cycle_entries(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    body: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## "):
            if current is not None:
                current["body"] = "\n".join(body).strip()
                entries.append(current)
            current = {"timestamp": line.removeprefix("## ").strip(), "path": str(path)}
            body = []
        elif current is not None:
            body.append(line)
    if current is not None:
        current["body"] = "\n".join(body).strip()
        entries.append(current)
    return entries


def latest_cycle_summary(root: Path | None = None) -> dict[str, Any]:
    all_entries: list[dict[str, Any]] = []
    checked: list[str] = []
    for path in cycle_log_paths(root):
        checked.append(str(path))
        all_entries.extend(parse_cycle_entries(path))
    if not all_entries:
        return {
            "found": False,
            "timestamp": None,
            "path": None,
            "summary": "No cycle log found yet.",
            "body": "",
            "checked_paths": checked,
        }
    latest = sorted(all_entries, key=lambda item: str(item.get("timestamp") or ""), reverse=True)[0]
    text = str(latest.get("body") or "")
    summary = "Latest cycle summary is available."
    for line in text.splitlines():
        if line.lower().startswith("**next recommended action:**"):
            summary = line.split(":", 1)[-1].strip()
            break
    return {
        "found": True,
        "timestamp": latest.get("timestamp"),
        "path": latest.get("path"),
        "summary": summary,
        "body": text,
        "checked_paths": checked,
    }
