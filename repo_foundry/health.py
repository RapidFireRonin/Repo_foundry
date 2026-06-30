from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from repo_foundry.models import repo_root
from repo_foundry.shipper_logs import latest_shipper_status, shipper_log_files


def _run(command: list[str], cwd: Path, timeout: int = 12) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout)
    except FileNotFoundError:
        return {"ok": False, "summary": f"{command[0]} not found", "stdout": "", "stderr": ""}
    except subprocess.TimeoutExpired:
        return {"ok": False, "summary": f"{command[0]} timed out", "stdout": "", "stderr": ""}
    output = (completed.stdout or completed.stderr or "").strip()
    return {
        "ok": completed.returncode == 0,
        "summary": output.splitlines()[0] if output else "ok" if completed.returncode == 0 else "failed",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def _tool(name: str) -> dict[str, Any]:
    path = shutil.which(name)
    if not path and os.name == "nt":
        candidates = {
            "git": [
                r"C:\Program Files\Git\cmd\git.exe",
                r"C:\Program Files\Git\bin\git.exe",
                r"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe",
            ],
            "gh": [r"C:\Program Files\GitHub CLI\gh.exe"],
            "pnpm": [r"C:\Users\Garrett\.cache\codex-runtimes\codex-primary-runtime\dependencies\bin\pnpm.cmd"],
            "node": [r"C:\Users\Garrett\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"],
        }
        for candidate in candidates.get(name, []):
            if Path(candidate).exists():
                path = candidate
                break
    return {"ok": bool(path), "path": path, "summary": path or f"{name} not found"}


def _scheduled_task_status() -> dict[str, Any]:
    if os.name != "nt":
        return {"ok": False, "summary": "Windows scheduled task check only runs on Windows."}
    result = _run(["powershell", "-NoProfile", "-Command", "Get-ScheduledTask -TaskName 'RepoFoundry PR Shipper' -ErrorAction SilentlyContinue | ConvertTo-Json -Compress"], repo_root())
    ok = result["ok"] and bool(result["stdout"].strip())
    return {"ok": ok, "summary": "RepoFoundry PR Shipper task exists." if ok else "RepoFoundry PR Shipper task not found."}


def collect_health(root: Path | None = None) -> dict[str, Any]:
    base = root or repo_root()
    git = _tool("git")
    gh = _tool("gh")
    node = _tool("node")
    pnpm = _tool("pnpm")
    git_cmd = git.get("path") or "git"
    gh_cmd = gh.get("path") or "gh"
    branch = _run([git_cmd, "branch", "--show-current"], base) if git["ok"] else {"ok": False, "summary": "git unavailable", "stdout": ""}
    git_status = _run([git_cmd, "status", "--short"], base) if git["ok"] else {"ok": False, "summary": "git unavailable", "stdout": ""}
    gh_auth = _run([gh_cmd, "auth", "status"], base) if gh["ok"] else {"ok": False, "summary": "gh unavailable", "stdout": "", "stderr": ""}

    checks = {
        "python": {"ok": True, "path": sys.executable, "summary": sys.executable},
        "backend_import": _run([sys.executable, "-c", "import fastapi, uvicorn, pydantic, yaml, repo_foundry.api; print('backend imports ok')"], base),
        "git": git,
        "node": node,
        "pnpm": pnpm,
        "github_cli": gh,
        "github_auth": {"ok": gh_auth["ok"], "summary": "GitHub CLI authenticated." if gh_auth["ok"] else gh_auth["summary"]},
        "repo_root": {"ok": (base / "pyproject.toml").exists(), "summary": str(base)},
        "current_branch": {"ok": branch["ok"], "summary": (branch.get("stdout") or branch["summary"]).strip()},
        "git_status": {"ok": git_status["ok"] and not (git_status.get("stdout") or "").strip(), "summary": "clean" if git_status["ok"] and not (git_status.get("stdout") or "").strip() else "dirty or unavailable", "details": (git_status.get("stdout") or "").strip()},
        "frontend_dir": {"ok": (base / "dashboard" / "frontend").exists(), "summary": str(base / "dashboard" / "frontend")},
        "shipper_script": {"ok": (base / "scripts" / "repo_foundry_pr_shipper.ps1").exists(), "summary": str(base / "scripts" / "repo_foundry_pr_shipper.ps1")},
        "shipper_task": _scheduled_task_status(),
        "recent_shipper_logs": {"ok": bool(shipper_log_files(base / "logs")), "summary": latest_shipper_status(base / "logs").get("summary")},
    }

    failed = [name for name, item in checks.items() if not item.get("ok")]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy" if not failed else "attention",
        "summary": "All local checks passed." if not failed else f"{len(failed)} local check(s) need attention.",
        "failed_checks": failed,
        "checks": checks,
    }


def write_health_artifact(payload: dict[str, Any], output_path: str | Path | None = None) -> Path:
    path = Path(output_path) if output_path else repo_root() / "artifacts" / "health" / "latest-health.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def main() -> None:
    payload = collect_health()
    path = write_health_artifact(payload)
    print(f"Repo Foundry health: {payload['summary']}")
    for name, item in payload["checks"].items():
        marker = "OK" if item.get("ok") else "WARN"
        print(f"[{marker}] {name}: {item.get('summary')}")
    print(f"JSON artifact: {path}")


if __name__ == "__main__":
    main()
