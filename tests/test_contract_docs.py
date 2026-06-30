from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "AGENT_CONTEXT.md",
    "DECISIONS.md",
    "ROADMAP.md",
    "NEXT_STEPS.md",
    "KNOWN_ISSUES.md",
    "ARCHITECTURE.md",
    "AGENT_CYCLE_LOG.md",
    "contracts/AUTONOMOUS_GOAL_CONTROL_CONTRACT.md",
    "contracts/DASHBOARD_DIRECTION_CONTROL_CONTRACT.md",
]

REQUIRED_AUTONOMOUS_SECTIONS = [
    "## Purpose",
    "## Allowed routine actions",
    "## Guarded actions",
    "## Denied actions",
    "## Required log fields",
    "## Stop conditions",
    "## Dashboard requirements",
    "## Definition of done",
]

REQUIRED_DASHBOARD_SECTIONS = [
    "## Purpose",
    "## Required input fields",
    "## Direction lifecycle",
    "## Backend requirements",
    "## Dashboard requirements",
    "## Agent consumption requirements",
    "## Audit requirements",
    "## Safety requirements",
    "## Definition of done",
]


def test_required_memory_and_contract_files_exist():
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    assert not missing, f"Missing required files: {missing}"


def test_autonomous_contract_has_required_sections():
    contract = (ROOT / "contracts/AUTONOMOUS_GOAL_CONTROL_CONTRACT.md").read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_AUTONOMOUS_SECTIONS if section not in contract]
    assert not missing, f"Missing required autonomous contract sections: {missing}"


def test_dashboard_direction_contract_has_required_sections():
    contract = (ROOT / "contracts/DASHBOARD_DIRECTION_CONTROL_CONTRACT.md").read_text(encoding="utf-8")
    missing = [section for section in REQUIRED_DASHBOARD_SECTIONS if section not in contract]
    assert not missing, f"Missing required dashboard contract sections: {missing}"


def test_contracts_mention_visibility_and_auditability():
    combined = "\n".join(
        [
            (ROOT / "contracts/AUTONOMOUS_GOAL_CONTROL_CONTRACT.md").read_text(encoding="utf-8"),
            (ROOT / "contracts/DASHBOARD_DIRECTION_CONTROL_CONTRACT.md").read_text(encoding="utf-8"),
        ]
    ).lower()
    assert "audit" in combined
    assert "dashboard" in combined
    assert "rollback" in combined
    assert "direction" in combined
