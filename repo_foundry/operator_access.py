from __future__ import annotations

import os
import socket
import subprocess
from datetime import datetime, timezone
from typing import Any


def _lan_ip() -> str:
    override = os.environ.get("REPO_FOUNDRY_LAN_IP")
    if override:
        return override
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def _tailscale_ip() -> str | None:
    override = os.environ.get("REPO_FOUNDRY_TAILSCALE_IP")
    if override:
        return override
    try:
        result = subprocess.run(["tailscale", "ip", "-4"], check=False, capture_output=True, text=True, timeout=4)
    except (OSError, subprocess.SubprocessError):
        return None
    for line in result.stdout.splitlines():
        candidate = line.strip()
        if candidate.startswith("100."):
            return candidate
    return None


def collect_operator_access(frontend_port: int = 5274, api_port: int = 8765) -> dict[str, Any]:
    lan_ip = _lan_ip()
    tailscale_ip = _tailscale_ip()
    urls = [
        {
            "label": "This PC",
            "url": f"http://127.0.0.1:{frontend_port}",
            "network": "local",
            "use_for": "Open from PEREGRIN itself.",
        },
        {
            "label": "iPhone on home Wi-Fi",
            "url": f"http://{lan_ip}:{frontend_port}",
            "network": "lan",
            "use_for": "Open from your phone while it is on the same Wi-Fi as PEREGRIN.",
        },
    ]
    if tailscale_ip:
        urls.append({
            "label": "iPhone through Tailscale",
            "url": f"http://{tailscale_ip}:{frontend_port}",
            "network": "tailscale",
            "use_for": "Open from your phone away from home when Tailscale is connected.",
        })
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "frontend_port": frontend_port,
        "api_port": api_port,
        "lan_ip": lan_ip,
        "tailscale_ip": tailscale_ip,
        "primary_phone_url": f"http://{lan_ip}:{frontend_port}",
        "api_url": f"http://{lan_ip}:{api_port}",
        "urls": urls,
        "launch_command": ".\\scripts\\rf.ps1 phone",
        "status": "phone-ready" if lan_ip != "127.0.0.1" else "local-only",
        "note": "Use the LAN URL on home Wi-Fi. Use the Tailscale URL when off-LAN.",
    }
