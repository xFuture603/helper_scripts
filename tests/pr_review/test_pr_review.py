"""Tests for the pr_review script."""
# pylint: disable=redefined-outer-name,import-error,too-few-public-methods
from unittest.mock import patch, MagicMock

import pytest

from pr_review import pr_review


@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get."""
    with patch("requests.get") as mock_get:
        yield mock_get


def test_get_user_repos(mock_requests_get):
    """Test the get_user_repos function."""
    mock_response = MagicMock()
    mock_response.json.return_value = [{"full_name": "user/repo1"}]
    mock_requests_get.return_value = mock_response

    repos = pr_review.get_user_repos({})
    assert repos == [{"full_name": "user/repo1"}]


def test_get_org_repos(mock_requests_get):
    """Test the get_org_repos function."""
    mock_response = MagicMock()
    mock_response.json.return_value = [{"full_name": "org/repo1"}]
    mock_requests_get.return_value = mock_response

    repos = pr_review.get_org_repos("org", {})
    assert repos == [{"full_name": "org/repo1"}]


def test_get_open_pull_requests(mock_requests_get):
    """Test the get_open_pull_requests function."""
    mock_response = MagicMock()
    mock_response.json.return_value = [{"number": 1, "html_url": "url"}]
    mock_requests_get.return_value = mock_response

    prs = pr_review.get_open_pull_requests("user/repo", {})
    assert prs == [{"number": 1, "html_url": "url"}]


def test_needs_review():
    """Test the needs_review function."""
    pr_needs_review = {"requested_reviewers": ["user"], "requested_teams": []}
    pr_no_review = {"requested_reviewers": [], "requested_teams": []}

    assert pr_review.needs_review(pr_needs_review) is True
    assert pr_review.needs_review(pr_no_review) is False


@patch("pr_review.pr_review.get_user_repos")
@patch("pr_review.pr_review.get_org_repos")
@patch("pr_review.pr_review.get_open_pull_requests")
def test_main(mock_get_prs, mock_get_org_repos, mock_get_user_repos):
    """Test the main function."""
    mock_get_user_repos.return_value = [{"full_name": "user/repo1"}]
    mock_get_org_repos.return_value = [{"full_name": "org/repo1"}]
    mock_get_prs.return_value = [
        {"number": 1, "html_url": "url1", "requested_reviewers": ["user"], "requested_teams": []},
        {"number": 2, "html_url": "url2", "requested_reviewers": [], "requested_teams": []},
    ]

    with patch("builtins.print") as mock_print:
        pr_review.main("user", "token", ["user", "org"])
        mock_print.assert_called()
