"""Tests for the gitlab_return_repositories_with_older_commits script."""
# pylint: disable=redefined-outer-name,import-error,too-few-public-methods
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

import pytest

from gitlab_return_repositories_with_older_commits import (
    gitlab_return_repositories_with_older_commits as grr,
)


@pytest.fixture
def mock_gitlab():
    """Fixture to mock gitlab.Gitlab."""
    with patch("gitlab.Gitlab") as mock_gitlab_class:
        yield mock_gitlab_class


class MockProject:
    """A mock class for a GitLab project."""

    def __init__(self, project_id, path_with_namespace, last_commit_date=None):
        """Initialize the MockProject."""
        self.id = project_id
        self.path_with_namespace = path_with_namespace
        self.web_url = f"https://gitlab.com/{path_with_namespace}"
        self.commits = MagicMock()
        if last_commit_date:
            mock_commit = MagicMock()
            mock_commit.committed_date = last_commit_date.isoformat()
            self.commits.list.return_value = [mock_commit]
        else:
            self.commits.list.return_value = []


def test_get_all_projects(mock_gitlab):
    """Test the get_all_projects function."""
    mock_gl = mock_gitlab.return_value
    mock_gl.projects.list.side_effect = [[MockProject(1, "user/repo1")], []]

    projects = grr.get_all_projects(mock_gl)
    assert len(projects) == 1
    assert projects[0].id == 1


def test_get_group_projects(mock_gitlab):
    """Test the get_group_projects function."""
    mock_gl = mock_gitlab.return_value
    mock_group = MagicMock()
    mock_group.projects.list.side_effect = [[MockProject(1, "group/repo1")], []]
    mock_group.subgroups.list.return_value = []
    mock_gl.groups.get.return_value = mock_group

    projects = grr.get_group_projects(mock_gl, "group_id")
    assert len(projects) == 1
    assert projects[0].id == 1


def test_repository_last_commit_date():
    """Test the repository_last_commit_date function."""
    now = datetime.now()
    project_with_commit = MockProject(1, "user/repo1", now)
    project_no_commit = MockProject(2, "user/repo2")

    assert grr.repository_last_commit_date(project_with_commit) == now
    assert grr.repository_last_commit_date(project_no_commit) is None


@patch("argparse.ArgumentParser")
@patch("gitlab.Gitlab")
def test_main(mock_gitlab_class, mock_argparse):
    """Test the main function."""
    now = datetime.now()
    threshold = now - timedelta(days=10)

    mock_args = mock_argparse.return_value.parse_args.return_value
    mock_args.gitlab_url = "https://gitlab.com"
    mock_args.access_token = "token"
    mock_args.timestamp = threshold.isoformat()
    mock_args.group = None

    mock_gl = mock_gitlab_class.return_value

    projects = [
        MockProject(1, "user/repo1", now - timedelta(days=20)),
        MockProject(2, "user/repo2", now - timedelta(days=5)),
        MockProject(3, "user/repo3"),
    ]

    def get_project_side_effect(project_id):
        for p in projects:
            if p.id == project_id:
                return p
        return None

    mock_gl.projects.get.side_effect = get_project_side_effect
    mock_gl.projects.list.side_effect = [projects, []]

    with patch("builtins.print") as mock_print:
        grr.main()
        mock_print.assert_called()
