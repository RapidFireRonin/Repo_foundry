from __future__ import annotations

from repo_foundry.models import WorkflowSpec


MEMORY_FILE_TEMPLATES: dict[str, str] = {
    "AGENT_CONTEXT.md": "# Agent Context\n\nThis repository is managed by Repo Foundry.\n",
    "DECISIONS.md": "# Decisions\n\nRecord durable architecture and workflow decisions here.\n",
    "KNOWN_ISSUES.md": "# Known Issues\n\nTrack known bugs, risks, and operational gaps here.\n",
    "NEXT_STEPS.md": "# Next Steps\n\nTrack the next useful autonomous tasks here.\n",
    "ROADMAP.md": "# Roadmap\n\nDescribe near-term and long-term repo direction here.\n",
    "ARCHITECTURE.md": "# Architecture\n\nDescribe the repository structure, runtime, and boundaries here.\n",
    "AGENT_CYCLE_LOG.md": "# Agent Cycle Log\n\nAutonomous cycle summaries are appended here.\n",
}


def workflow_template(workflow: WorkflowSpec) -> str:
    if workflow.template == "ci":
        return """name: CI

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  run-contract:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Show run contract
        run: |
          echo "Run contract expected: setup, test, build, run, bench, agent-report, cycle-summary"
"""
    if workflow.template == "agent-report":
        return """name: Agent Report

on:
  workflow_dispatch:
  pull_request:

permissions:
  contents: read

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: |
          echo "## Agent Report" >> "$GITHUB_STEP_SUMMARY"
          echo "Autonomous work remains visible through PRs, logs, and artifacts." >> "$GITHUB_STEP_SUMMARY"
"""
    if workflow.template == "cycle-summary":
        return """name: Cycle Summary Validation

on:
  pull_request:
    paths:
      - AGENT_CYCLE_LOG.md
      - docs/agent-cycle-log.md

permissions:
  contents: read

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: test -f AGENT_CYCLE_LOG.md || test -f docs/agent-cycle-log.md
"""
    return f"""name: {workflow.name}

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  placeholder:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: echo "Managed by Repo Foundry"
"""

