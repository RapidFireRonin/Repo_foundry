from __future__ import annotations

import fnmatch
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


class AutoMergePolicy(BaseModel):
    allowed_branches: list[str] = Field(default_factory=lambda: ["repo-foundry/*"])
    required_checks: list[str] = Field(default_factory=list)
    max_changed_files: int = 25
    max_additions: int = 1200
    max_deletions: int = 600
    blocked_paths: list[str] = Field(default_factory=list)
    dangerous_operations: list[str] = Field(default_factory=list)
    require_clean_mergeable: bool = True
    require_no_failing_checks: bool = True
    require_audit_entry_before_merge: bool = True
    stale_after_hours: int = 48


class CheckStatus(BaseModel):
    name: str
    status: str = "UNKNOWN"
    conclusion: str | None = None

    @property
    def is_success(self) -> bool:
        value = (self.conclusion or self.status).upper()
        return value in {"SUCCESS", "PASSED", "COMPLETED", "NEUTRAL", "SKIPPED"}

    @property
    def is_failure(self) -> bool:
        value = (self.conclusion or self.status).upper()
        return value in {"FAILURE", "FAILED", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}


class PullRequestSnapshot(BaseModel):
    number: int
    title: str
    url: str = ""
    branch: str
    base_branch: str = "main"
    mergeable: str | bool | None = None
    changed_files: int = 0
    additions: int = 0
    deletions: int = 0
    files: list[str] = Field(default_factory=list)
    checks: list[CheckStatus] = Field(default_factory=list)
    dangerous_operations: list[str] = Field(default_factory=list)
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    commit_sha: str = ""
    state: str = "OPEN"
    superseded_by: int | None = None


class PolicyDecision(BaseModel):
    allowed: bool
    risk: str
    reasons: list[str] = Field(default_factory=list)


def load_policy(path: str | Path = "policies/auto-merge.yaml") -> AutoMergePolicy:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return AutoMergePolicy.model_validate(data)


def evaluate_policy(pr: PullRequestSnapshot, policy: AutoMergePolicy, audit_present: bool = False) -> PolicyDecision:
    reasons: list[str] = []

    if not any(fnmatch.fnmatch(pr.branch, pattern) for pattern in policy.allowed_branches):
        reasons.append(f"branch `{pr.branch}` is not allowed")

    if policy.require_clean_mergeable and str(pr.mergeable).upper() not in {"TRUE", "MERGEABLE"}:
        reasons.append(f"mergeable state is `{pr.mergeable}`")

    failed = [check.name for check in pr.checks if check.is_failure]
    unknown = [check.name for check in pr.checks if not check.is_success and not check.is_failure]
    if policy.require_no_failing_checks and failed:
        reasons.append(f"failing checks: {', '.join(failed)}")
    if unknown:
        reasons.append(f"unknown checks: {', '.join(unknown)}")

    successful_names = {check.name for check in pr.checks if check.is_success}
    missing_required = [name for name in policy.required_checks if name not in successful_names]
    if missing_required:
        reasons.append(f"missing required checks: {', '.join(missing_required)}")

    blocked = [
        path
        for path in pr.files
        if any(fnmatch.fnmatch(path, pattern) for pattern in policy.blocked_paths)
    ]
    if blocked:
        reasons.append(f"blocked paths changed: {', '.join(blocked)}")

    if pr.changed_files > policy.max_changed_files:
        reasons.append(f"changed files {pr.changed_files} exceeds {policy.max_changed_files}")
    if pr.additions > policy.max_additions:
        reasons.append(f"additions {pr.additions} exceeds {policy.max_additions}")
    if pr.deletions > policy.max_deletions:
        reasons.append(f"deletions {pr.deletions} exceeds {policy.max_deletions}")

    denied_ops = [op for op in pr.dangerous_operations if op in policy.dangerous_operations]
    if denied_ops:
        reasons.append(f"dangerous operations denied: {', '.join(denied_ops)}")

    if policy.require_audit_entry_before_merge and not audit_present:
        reasons.append("missing pre-merge audit entry")

    risk = "low" if not reasons and pr.deletions < 100 else "blocked" if reasons else "medium"
    return PolicyDecision(allowed=not reasons, risk=risk, reasons=reasons)
