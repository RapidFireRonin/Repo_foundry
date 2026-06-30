# Autonomous Goal-Control Contract v1

This contract defines how Repo Foundry agents may act without requiring a human approval step for every routine change.

## Purpose

Enable useful autonomous work while preserving direct human control over goals, durable logs, UI visibility, and recovery paths.

## Allowed routine actions

Agents may perform these actions when they match the active goal and repository policy:

- Read repository files, issues, pull requests, workflow status, and logs.
- Create or update documentation, contracts, blueprints, tests, and workflows.
- Open or update issues and pull requests.
- Add validation checks that improve safety and visibility.
- Append cycle summaries and audit entries.
- Make low-risk configuration changes when a policy explicitly allows them.

## Guarded actions

These require explicit policy flags before execution:

- Creating repositories.
- Deleting repositories, branches, files, artifacts, logs, or issues.
- Changing secrets, credentials, tokens, or runner registration.
- Editing branch protection or repository visibility.
- Enabling direct main-branch writes.
- Running scripts that modify the local machine outside the configured workspace.
- Installing system packages or services on the local machine.

## Denied actions

Agents must not:

- Hide changes from logs or dashboard surfaces.
- Commit secrets or private credentials.
- Disable audit logging.
- Suppress failures from cycle summaries.
- Rewrite history unless an explicit recovery policy allows it.
- Continue execution after a configured stop condition is reached.

## Required log fields

Every write action must produce a human-readable audit entry with:

- Timestamp
- Agent name
- Active goal
- Action taken
- Files or resources changed
- Reason
- Risk level
- Rollback note
- Links to PRs, issues, runs, logs, or artifacts when available

## Stop conditions

Agents must stop or downgrade to report-only mode when:

- Required credentials are missing.
- A validation check fails and no safe fix is obvious.
- The active goal conflicts with repository policy.
- A dangerous action is requested without the required policy flag.
- The same failure repeats across cycles.

## Dashboard requirements

The dashboard should show:

- Current active goals
- Agent status
- Recent autonomous actions
- Failed runs
- Human control options
- Open PRs and issues
- Audit log entries
- Cycle summaries
- Artifacts and logs
- Current risk warnings
- Playable or usable products registered in `registry/products.yaml`

## Definition of done

A repo is compliant with this contract when it has:

- Contract documentation
- Core memory files
- Cycle log
- Audit requirements
- Validation workflow
- Test coverage for required sections
- Dashboard-ready status fields

A user-facing product, game, tool, or usable repository is not done until it is registered in `registry/products.yaml` and appears in Mission Control's Playable / Usable Products gallery with launch or inspection links, proof, tests, and a quality verdict.
