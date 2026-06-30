from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass

from repo_foundry.models import LabelSpec, RepoBlueprint


class GitHubCliUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str


class GitUnavailable(RuntimeError):
    pass


def git_path() -> str:
    configured = os.environ.get("REPO_FOUNDRY_GIT")
    if configured:
        return configured
    path = shutil.which("git")
    if path:
        return path
    for candidate in (
        r"C:\Program Files\Git\cmd\git.exe",
        r"C:\Program Files\Git\bin\git.exe",
    ):
        if os.path.exists(candidate):
            return candidate
    raise GitUnavailable("Git was not found on PATH.")


def gh_path() -> str:
    path = shutil.which("gh")
    if not path:
        raise GitHubCliUnavailable("GitHub CLI `gh` was not found on PATH.")
    return path


def run_gh(args: list[str], input_text: str | None = None) -> CommandResult:
    command = [gh_path(), *args]
    completed = subprocess.run(command, input=input_text, capture_output=True, text=True, check=False)
    return CommandResult(command, completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def run_git(args: list[str], cwd: str | os.PathLike[str] | None = None) -> CommandResult:
    command = [git_path(), *args]
    completed = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    return CommandResult(command, completed.returncode, completed.stdout.strip(), completed.stderr.strip())


def repo_create_command(blueprint: RepoBlueprint) -> list[str]:
    visibility = "--private" if blueprint.visibility == "private" else "--public"
    return [
        "repo",
        "create",
        f"{blueprint.owner}/{blueprint.name}",
        visibility,
        "--description",
        blueprint.description or f"Managed by Repo Foundry: {blueprint.name}",
    ]


def label_create_command(owner: str, repo: str, label: LabelSpec) -> list[str]:
    return [
        "label",
        "create",
        label.name,
        "--repo",
        f"{owner}/{repo}",
        "--color",
        label.color,
        "--description",
        label.description,
        "--force",
    ]


def branch_protection_command(blueprint: RepoBlueprint) -> list[str]:
    return [
        "api",
        "-X",
        "PUT",
        f"repos/{blueprint.owner}/{blueprint.name}/branches/{blueprint.default_branch}/protection",
        "--input",
        "-",
    ]


def branch_protection_payload() -> str:
    payload = {
        "required_status_checks": None,
        "enforce_admins": False,
        "required_pull_request_reviews": None,
        "restrictions": None,
        "required_linear_history": False,
        "allow_force_pushes": False,
        "allow_deletions": False,
    }
    return json.dumps(payload)


def pr_create_command(repo: str, branch: str, title: str, body: str) -> list[str]:
    return [
        "pr",
        "create",
        "--repo",
        repo,
        "--head",
        branch,
        "--base",
        "main",
        "--title",
        title,
        "--body",
        body,
    ]
