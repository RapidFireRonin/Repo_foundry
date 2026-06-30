from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_CONTRACTS = [
    "contracts/AUTONOMOUS_GOAL_CONTROL_CONTRACT.md",
    "contracts/DASHBOARD_DIRECTION_CONTROL_CONTRACT.md",
]

REQUIRED_AUTONOMY_SECTIONS = [
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


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_required_contract_files_exist():
    missing = [path for path in REQUIRED_CONTRACTS if not (ROOT / path).exists()]
    assert not missing, f"Missing required contract files: {missing}"


def test_autonomous_contract_has_required_sections():
    contract = read("contracts/AUTONOMOUS_GOAL_CONTROL_CONTRACT.md")
    missing = [section for section in REQUIRED_AUTONOMY_SECTIONS if section not in contract]
    assert not missing, f"Missing required autonomous contract sections: {missing}"


def test_dashboard_contract_has_required_sections():
    contract = read("contracts/DASHBOARD_DIRECTION_CONTROL_CONTRACT.md")
    missing = [section for section in REQUIRED_DASHBOARD_SECTIONS if section not in contract]
    assert not missing, f"Missing required dashboard direction contract sections: {missing}"


def test_contracts_preserve_visibility_and_directability():
    combined = "\n".join(read(path).lower() for path in REQUIRED_CONTRACTS)
    for expected in ["audit", "dashboard", "direction", "rollback", "stop condition"]:
        assert expected in combined
