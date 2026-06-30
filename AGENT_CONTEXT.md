# Agent Context

Repo Foundry coordinates safe repository creation and maintenance through blueprints, dry-run reconciliation, PR-only changes, local runtime support, dashboard visibility, audit logs, and hourly cycle summaries.

Current architecture direction: complete the autonomous work loop without sacrificing safety. Agents should continue creating PR-based, auditable changes, but future Builder/Reviewer work should prioritize the Autonomous Completion Loop contract so safe PRs can move from proposed to merged through dry-run-first policy evaluation, explicit execute mode, check-state verification, and visible completion logs.
