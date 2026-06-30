# Security

Repo Foundry defaults to dry-run mode and private repositories. Autonomous execution should be enabled intentionally with `--execute` or scheduled runner configuration.

Do not commit secrets. Use `.env` locally and GitHub secrets for hosted execution. Prefer fine-grained GitHub tokens scoped to the owner and repositories Repo Foundry manages.

Report sensitive findings privately. Do not paste tokens into issues, PRs, logs, cycle summaries, or screenshots.
