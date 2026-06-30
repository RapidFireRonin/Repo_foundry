from __future__ import annotations

from repo_foundry.shipper_logs import parse_shipper_log


def test_parse_shipper_log_merged_and_skipped(tmp_path):
    path = tmp_path / "repo-foundry-pr-shipper-20260630-010101.log"
    path.write_text(
        "\n".join(
            [
                "[2026-06-30 01:01:01] Inspecting PR #20: Add dashboard buttons",
                "[2026-06-30 01:01:02] Merged PR #20.",
                "[2026-06-30 01:01:03] Inspecting PR #21: Risky work",
                "[2026-06-30 01:01:04] PR #21 has failing checks: secret-scan. Skipping.",
                "[2026-06-30 01:01:05] Done. Merged 1 PR(s).",
            ]
        ),
        encoding="utf-8",
    )

    parsed = parse_shipper_log(path)

    assert parsed["last_run_at"] == "2026-06-30 01:01:05"
    assert parsed["merged_prs"] == [20]
    assert parsed["final_merged_count"] == 1
    assert parsed["failed_checks"]
    assert parsed["skipped_prs"][0]["number"] == 21


def test_parse_missing_shipper_log_degrades(tmp_path):
    parsed = parse_shipper_log(tmp_path / "missing.log")

    assert parsed["exists"] is False
    assert parsed["summary"] == "No shipper log found yet."
