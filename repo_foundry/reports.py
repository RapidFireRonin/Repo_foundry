from __future__ import annotations

import argparse
from pathlib import Path


def write_agent_report(path: str = "artifacts/agent-report.md") -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "# Agent Report\n\n"
        "- Status: scaffold ready\n"
        "- Safety: dry-run default, PR-oriented source changes, readable audit logs\n"
        "- Next: connect live GitHub adapters to autonomous scheduled runs\n",
        encoding="utf-8",
    )
    return target


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["agent-report"])
    args = parser.parse_args()
    if args.command == "agent-report":
        print(write_agent_report())


if __name__ == "__main__":
    main()
