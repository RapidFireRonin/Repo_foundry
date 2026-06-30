from __future__ import annotations

from repo_foundry.operator_access import collect_operator_access


def test_operator_access_uses_env_overrides(monkeypatch):
    monkeypatch.setenv("REPO_FOUNDRY_LAN_IP", "192.168.1.200")
    monkeypatch.setenv("REPO_FOUNDRY_TAILSCALE_IP", "100.126.113.112")

    payload = collect_operator_access()

    assert payload["primary_phone_url"] == "http://192.168.1.200:5274"
    assert payload["api_url"] == "http://192.168.1.200:8765"
    assert any(item["url"] == "http://100.126.113.112:5274" for item in payload["urls"])
    assert payload["launch_command"] == ".\\scripts\\rf.ps1 phone"
