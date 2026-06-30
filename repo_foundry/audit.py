from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def audit_log_path() -> Path:
    return Path(os.environ.get("REPO_FOUNDRY_AUDIT_LOG", "./logs/audit.jsonl"))


def write_audit_event(action: str, target: str, actor: str = "repo-foundry", **details: Any) -> dict[str, Any]:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "target": target,
        "details": details,
    }
    path = audit_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")
    return event

