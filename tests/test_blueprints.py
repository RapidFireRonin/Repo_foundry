from pathlib import Path

import pytest
from pydantic import ValidationError

from repo_foundry.blueprints import load_blueprint
from repo_foundry.models import STANDARD_MEMORY_FILES, RepoBlueprint


def test_example_blueprint_validates() -> None:
    blueprint = load_blueprint(Path("blueprints/example-repo.yaml"))

    assert blueprint.name == "example-managed-repo"
    assert blueprint.visibility == "private"
    assert blueprint.allow_agent_main_writes is False
    assert set(STANDARD_MEMORY_FILES).issubset(set(blueprint.memory_files))


def test_blueprint_rejects_missing_memory_file() -> None:
    data = {
        "owner": "RapidFireRonin",
        "name": "unsafe",
        "memory_files": ["AGENT_CONTEXT.md"],
    }

    with pytest.raises(ValidationError, match="missing standard memory files"):
        RepoBlueprint.model_validate(data)


def test_blueprint_rejects_agent_main_writes() -> None:
    data = {
        "owner": "RapidFireRonin",
        "name": "unsafe",
        "allow_agent_main_writes": True,
    }

    with pytest.raises(ValidationError, match="agents may not write directly to main"):
        RepoBlueprint.model_validate(data)

