from repo_foundry.github_client import GitHubCredentialStatus, token_env_status


def test_token_env_status_prefers_repo_foundry_token() -> None:
    status = token_env_status(
        {
            "GH_TOKEN": "gh-token",
            "GITHUB_TOKEN": "github-token",
            "REPO_FOUNDRY_GH_TOKEN": "repo-foundry-token",
        }
    )

    assert status == GitHubCredentialStatus(
        True,
        "REPO_FOUNDRY_GH_TOKEN",
        "GitHub token available from `REPO_FOUNDRY_GH_TOKEN`.",
    )


def test_token_env_status_accepts_standard_gh_token() -> None:
    status = token_env_status({"GH_TOKEN": "gh-token"})

    assert status is not None
    assert status.available is True
    assert status.method == "GH_TOKEN"


def test_token_env_status_returns_none_when_no_token_is_present() -> None:
    assert token_env_status({}) is None
