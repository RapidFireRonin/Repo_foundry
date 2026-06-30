from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


STANDARD_MEMORY_FILES = [
    "AGENT_CONTEXT.md",
    "DECISIONS.md",
    "KNOWN_ISSUES.md",
    "NEXT_STEPS.md",
    "ROADMAP.md",
    "ARCHITECTURE.md",
    "AGENT_CYCLE_LOG.md",
]


class RepoVisibility(str, Enum):
    private = "private"
    public = "public"


class AutomationMode(str, Enum):
    autonomous = "autonomous"
    manual = "manual"


class LabelSpec(BaseModel):
    name: str
    color: str = Field(pattern=r"^[0-9a-fA-F]{6}$")
    description: str = ""


class WorkflowSpec(BaseModel):
    name: str
    template: str
    path: str = Field(pattern=r"^\.github/workflows/.+\.ya?ml$")


class RunContract(BaseModel):
    setup: str = "make setup"
    test: str = "make test"
    build: str = "make build"
    run: str = "make run"
    bench: str = "make bench"
    agent_report: str = "make agent-report"
    cycle_summary: str = "make cycle-summary"


class RepoBlueprint(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    owner: str = Field(pattern=r"^[A-Za-z0-9_.-]+$")
    description: str = ""
    visibility: RepoVisibility = RepoVisibility.private
    default_branch: str = "main"
    topics: list[str] = Field(default_factory=list)
    labels: list[LabelSpec] = Field(default_factory=list)
    workflows: list[WorkflowSpec] = Field(default_factory=list)
    memory_files: list[str] = Field(default_factory=lambda: STANDARD_MEMORY_FILES.copy())
    run_contract: RunContract = Field(default_factory=RunContract)
    branch_protection_required: bool = True
    automation_mode: AutomationMode = AutomationMode.autonomous
    allow_agent_main_writes: bool = False

    @field_validator("memory_files")
    @classmethod
    def memory_files_include_standard(cls, value: list[str]) -> list[str]:
        missing = [path for path in STANDARD_MEMORY_FILES if path not in value]
        if missing:
            raise ValueError(f"missing standard memory files: {', '.join(missing)}")
        return value

    @field_validator("allow_agent_main_writes")
    @classmethod
    def agents_may_not_write_main(cls, value: bool) -> bool:
        if value:
            raise ValueError("agents may not write directly to main")
        return value


class RegisteredRepo(BaseModel):
    owner: str
    name: str
    default_branch: str = "main"
    exists: bool = False
    labels: list[str] = Field(default_factory=list)
    workflows: list[str] = Field(default_factory=list)
    memory_files: list[str] = Field(default_factory=list)
    branch_protection: bool = False


class DirectionItem(BaseModel):
    title: str
    priority: int = Field(default=50, ge=0, le=100)
    scope: str = "global"
    desired_outcome: str
    avoid: list[str] = Field(default_factory=list)
    status: str = "active"


class Registry(BaseModel):
    repos: list[RegisteredRepo] = Field(default_factory=list)
    directions: list[DirectionItem] = Field(default_factory=list)


class PlanAction(BaseModel):
    action: str
    target: str
    reason: str
    dangerous: bool = False
    autonomous: bool = True
    command_preview: list[str] = Field(default_factory=list)
    opens_pr: bool = False


class ReconcilePlan(BaseModel):
    blueprint: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    dry_run: bool = True
    automation_mode: AutomationMode = AutomationMode.autonomous
    actions: list[PlanAction] = Field(default_factory=list)
    visibility_items: list[str] = Field(default_factory=list)


class CycleSummary(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    founder_strategist: str
    architect: str
    builder: str
    reviewer_debugger: str
    research_scout: str
    prs_opened_updated: list[str] = Field(default_factory=list)
    failed_checks: list[str] = Field(default_factory=list)
    artifacts_logs: list[str] = Field(default_factory=list)
    autonomous_watch_items: list[str] = Field(default_factory=list)
    next_recommended_action: str

    def to_markdown(self) -> str:
        def list_block(items: list[str]) -> str:
            return "\n".join(f"- {item}" for item in items) if items else "- None"

        stamp = self.timestamp.astimezone(timezone.utc).isoformat()
        return (
            f"\n## {stamp}\n\n"
            f"**Founder/Strategist activity:** {self.founder_strategist}\n\n"
            f"**Architect activity:** {self.architect}\n\n"
            f"**Builder activity:** {self.builder}\n\n"
            f"**Reviewer/Debugger activity:** {self.reviewer_debugger}\n\n"
            f"**Research Scout activity:** {self.research_scout}\n\n"
            f"**PRs opened/updated:**\n{list_block(self.prs_opened_updated)}\n\n"
            f"**Failed checks:**\n{list_block(self.failed_checks)}\n\n"
            f"**Artifacts/logs:**\n{list_block(self.artifacts_logs)}\n\n"
            f"**Autonomous watch items:**\n{list_block(self.autonomous_watch_items)}\n\n"
            f"**Next recommended action:** {self.next_recommended_action}\n"
        )


class DashboardState(BaseModel):
    repos: list[dict[str, Any]]
    blueprints: list[dict[str, Any]]
    runs: list[dict[str, Any]]
    prs: list[dict[str, Any]]
    logs: list[dict[str, Any]]
    artifacts: list[dict[str, Any]]
    directions: list[dict[str, Any]]
    watch_items: list[dict[str, Any]]
    cycle_entries: list[dict[str, Any]]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]
