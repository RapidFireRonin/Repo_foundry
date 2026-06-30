from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from repo_foundry.models import RepoBlueprint


def load_blueprint(path: str | Path) -> RepoBlueprint:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return RepoBlueprint.model_validate(data)


def main() -> None:
    parser = argparse.ArgumentParser(description="Blueprint utilities")
    sub = parser.add_subparsers(dest="command", required=True)
    validate = sub.add_parser("validate")
    validate.add_argument("path")
    args = parser.parse_args()

    if args.command == "validate":
        blueprint = load_blueprint(args.path)
        print(f"valid blueprint: {blueprint.owner}/{blueprint.name}")


if __name__ == "__main__":
    main()

