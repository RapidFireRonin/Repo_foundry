from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_TSX = ROOT / "dashboard" / "frontend" / "src" / "main.tsx"
STYLES_CSS = ROOT / "dashboard" / "frontend" / "src" / "styles.css"
API_PY = ROOT / "repo_foundry" / "api.py"


def test_build_console_has_direct_goal_composer() -> None:
    source = MAIN_TSX.read_text(encoding="utf-8")

    assert "function BuildConsole" in source
    assert "Describe what you want built" in source
    assert "DirectionComposer onCreated={onCreated} compact" in source
    assert "Direct Agents" in source
    assert "Build this" in source


def test_direction_composer_posts_required_operator_fields() -> None:
    source = MAIN_TSX.read_text(encoding="utf-8")

    assert "fetch(`${apiBase}/api/directions`" in source
    assert 'method: "POST"' in source
    assert "title: cleanTitle" in source
    assert "desired_outcome: cleanTitle" in source
    assert "details: details.trim()" in source
    assert "priority" in source
    assert 'scope: "global"' in source


def test_backend_accepts_dashboard_direction_requests() -> None:
    source = API_PY.read_text(encoding="utf-8")

    assert "class DirectionCreateRequest" in source
    assert '@app.post("/api/directions")' in source
    assert 'source="dashboard"' in source
    assert '"registry"' in source
    assert '"repos.yaml"' in source


def test_build_console_is_mobile_visible_and_styled() -> None:
    source = STYLES_CSS.read_text(encoding="utf-8")

    assert ".build-console" in source
    assert ".build-custom-goal" in source
    assert ".direction-composer.compact" in source
    assert "@media (max-width: 980px)" in source
    mobile_css = source[source.index("@media (max-width: 980px)"):]
    assert ".build-custom-goal" in mobile_css
