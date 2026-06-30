from pathlib import Path

from repo_foundry.cycle_summary import append_summary, sample_summary


def test_cycle_summary_markdown_contains_required_sections() -> None:
    markdown = sample_summary().to_markdown()

    assert "Founder/Strategist activity" in markdown
    assert "Architect activity" in markdown
    assert "Builder activity" in markdown
    assert "Reviewer/Debugger activity" in markdown
    assert "Research Scout activity" in markdown
    assert "PRs opened/updated" in markdown
    assert "Failed checks" in markdown
    assert "Artifacts/logs" in markdown
    assert "Autonomous watch items" in markdown
    assert "Next recommended action" in markdown


def test_append_summary_writes_to_target(tmp_path: Path) -> None:
    target = tmp_path / "agent-cycle-log.md"

    append_summary(sample_summary(), target)

    content = target.read_text(encoding="utf-8")
    assert "Repo Foundry priorities" in content
    assert "Next recommended action" in content
