"""Tests for the gitlab_remove_doubleton_members script."""
# pylint: disable=redefined-outer-name,import-error,too-few-public-methods
from unittest.mock import patch, MagicMock

import pytest
from gitlab.exceptions import GitlabDeleteError

from gitlab_remove_doubleton_members import gitlab_remove_doubleton_members as grd


@pytest.fixture
def mock_gitlab():
    """Fixture to mock gitlab.Gitlab."""
    with patch("gitlab.Gitlab") as mock_gitlab_class:
        yield mock_gitlab_class


@pytest.fixture(autouse=True)
def mock_colorama():
    """Fixture to mock colorama for suppressing terminal output."""
    with patch("colorama.Fore") as mock_fore, patch("colorama.Style") as mock_style:
        mock_fore.LIGHTBLUE_EX = ""
        mock_fore.YELLOW = ""
        mock_fore.GREEN = ""
        mock_fore.RED = ""
        mock_style.RESET_ALL = ""
        yield


class MockMember:
    """A mock class for a GitLab member."""

    def __init__(self, member_id, username):
        """Initialize the MockMember."""
        self.id = member_id
        self.username = username


class MockGroup:
    """A mock class for a GitLab group."""

    def __init__(self, group_id, web_url="https://gitlab.com/group"):
        """Initialize the MockGroup."""
        self.id = group_id
        self.web_url = web_url
        self.members = MagicMock()
        self.subgroups = MagicMock()
        self.projects = MagicMock() # Added projects mock


class MockProject:
    """A mock class for a GitLab project."""

    def __init__(self, project_id, name, path_with_namespace, web_url="https://gitlab.com/project"):
        """Initialize the MockProject."""
        self.id = project_id
        self.name = name
        self.path_with_namespace = path_with_namespace
        self.web_url = web_url
        self.members = MagicMock()


def test_get_paginated_data():
    """Test the get_paginated_data helper function."""
    mock_get_function = MagicMock(side_effect=[[1, 2], [3], []])
    data = grd.get_paginated_data(mock_get_function)
    assert data == [1, 2, 3]


def test_get_all_groups(mock_gitlab):
    """Test the get_all_groups function."""
    mock_gl = mock_gitlab.return_value
    mock_gl.groups.get.side_effect = [
        MockGroup(1),
        MockGroup(2),
    ]
    mock_gl.groups.get.return_value.subgroups.list.side_effect = [
        [MockGroup(2)],
        [],
    ]

    groups = grd.get_all_groups(mock_gl, 1)
    assert len(groups) == 2
    assert groups[0].id == 1
    assert groups[1].id == 2


def test_get_group_members(mock_gitlab):
    """Test the get_group_members function."""
    mock_gl = mock_gitlab.return_value
    mock_group = MockGroup(1)
    mock_group.members.list.side_effect = [[MockMember(1, "user1")], []]
    mock_gl.groups.get.return_value = mock_group

    members = grd.get_group_members(mock_gl, 1)
    assert len(members) == 1
    assert members[0].username == "user1"


def test_get_repo_members(mock_gitlab):
    """Test the get_repo_members function."""
    mock_gl = mock_gitlab.return_value
    mock_project = MockProject(1, "test-project", "test/test-project")
    mock_project.members.list.side_effect = [[MockMember(1, "user1")], []]
    mock_gl.projects.get.return_value = mock_project

    members = grd.get_repo_members(mock_gl, 1)
    assert len(members) == 1
    assert members[0].username == "user1"


def test_get_group_projects(mock_gitlab):
    """Test the get_group_projects function."""
    mock_gl = mock_gitlab.return_value
    mock_group = MockGroup(1)
    mock_group.projects.list.side_effect = [[MockProject(1, "proj1", "group/proj1")], []]
    mock_group.subgroups.list.side_effect = [[MockGroup(2)], []]
    mock_gl.groups.get.return_value = mock_group

    mock_subgroup = MockGroup(2)
    mock_subgroup.projects.list.side_effect = [[MockProject(2, "proj2", "group/subgroup/proj2")], []]
    mock_subgroup.subgroups.list.return_value = []
    mock_gl.groups.get.side_effect = [mock_group, mock_subgroup]

    projects = grd.get_group_projects(mock_gl, 1)
    assert len(projects) == 2
    assert projects[0].name == "proj1"
    assert projects[1].name == "proj2"


@patch("builtins.print")
def test_remove_direct_members_dry_run(mock_print, mock_gitlab):
    """Test remove_direct_members in dry-run mode."""
    mock_gl = mock_gitlab.return_value

    # Mock get_all_groups
    mock_gl.groups.get.side_effect = [MockGroup(1), MockGroup(2)]
    mock_gl.groups.get.return_value.subgroups.list.side_effect = [[MockGroup(2)], []]

    # Mock get_group_members
    mock_group_members = [MockMember(1, "user1"), MockMember(2, "user2")]
    mock_gl.groups.get.return_value.members.list.side_effect = [mock_group_members, []]

    # Mock get_group_projects
    mock_project = MockProject(1, "test-project", "group/test-project")
    mock_gl.projects.get.return_value = mock_project
    mock_gl.groups.get.return_value.projects.list.side_effect = [[mock_project], []]

    # Mock get_repo_members
    mock_repo_members = [MockMember(1, "user1"), MockMember(3, "user3")]
    mock_project.members.list.side_effect = [mock_repo_members, []]

    grd.remove_direct_members(mock_gl, 1, dry_run=True)

    mock_print.assert_any_call(
        "Dry-run: Would remove directly added member user1 from repository "
        "test-project"
    )
    mock_project.members.delete.assert_not_called()


@patch("builtins.print")
def test_remove_direct_members_actual_run(mock_print, mock_gitlab):
    """Test remove_direct_members in actual run mode."""
    mock_gl = mock_gitlab.return_value

    # Mock get_all_groups
    mock_gl.groups.get.side_effect = [MockGroup(1), MockGroup(2)]
    mock_gl.groups.get.return_value.subgroups.list.side_effect = [[MockGroup(2)], []]

    # Mock get_group_members
    mock_group_members = [MockMember(1, "user1"), MockMember(2, "user2")]
    mock_gl.groups.get.return_value.members.list.side_effect = [mock_group_members, []]

    # Mock get_group_projects
    mock_project = MockProject(1, "test-project", "group/test-project")
    mock_gl.projects.get.return_value = mock_project
    mock_gl.groups.get.return_value.projects.list.side_effect = [[mock_project], []]

    # Mock get_repo_members
    mock_repo_members = [MockMember(1, "user1"), MockMember(3, "user3")]
    mock_project.members.list.side_effect = [mock_repo_members, []]

    grd.remove_direct_members(mock_gl, 1, dry_run=False)

    mock_print.assert_any_call(
        "Removing member user1 from repository test-project"
    )
    mock_project.members.delete.assert_called_once_with(1)


@patch("builtins.print")
def test_remove_direct_members_exclude_users(mock_print, mock_gitlab):
    """Test remove_direct_members with excluded users."""
    mock_gl = mock_gitlab.return_value

    # Mock get_all_groups
    mock_gl.groups.get.side_effect = [MockGroup(1), MockGroup(2)]
    mock_gl.groups.get.return_value.subgroups.list.side_effect = [[MockGroup(2)], []]

    # Mock get_group_members
    mock_group_members = [MockMember(1, "user1"), MockMember(2, "user2")]
    mock_gl.groups.get.return_value.members.list.side_effect = [mock_group_members, []]

    # Mock get_group_projects
    mock_project = MockProject(1, "test-project", "group/test-project")
    mock_gl.projects.get.return_value = mock_project
    mock_gl.groups.get.return_value.projects.list.side_effect = [[mock_project], []]

    # Mock get_repo_members
    mock_repo_members = [MockMember(1, "user1"), MockMember(3, "user3")]
    mock_project.members.list.side_effect = [mock_repo_members, []]

    grd.remove_direct_members(mock_gl, 1, dry_run=False, exclude_users=["user1"])

    mock_print.assert_any_call(
        "Skipping member user1 as they are in the exclude list for repository test-project"
    )
    mock_project.members.delete.assert_not_called()


@patch("builtins.print")
def test_remove_direct_members_delete_error(mock_print, mock_gitlab):
    """Test remove_direct_members with a GitlabDeleteError."""
    mock_gl = mock_gitlab.return_value

    # Mock get_all_groups
    mock_gl.groups.get.side_effect = [MockGroup(1), MockGroup(2)]
    mock_gl.groups.get.return_value.subgroups.list.side_effect = [[MockGroup(2)], []]

    # Mock get_group_members
    mock_group_members = [MockMember(1, "user1"), MockMember(2, "user2")]
    mock_gl.groups.get.return_value.members.list.side_effect = [mock_group_members, []]

    # Mock get_group_projects
    mock_project = MockProject(1, "test-project", "group/test-project")
    mock_gl.projects.get.return_value = mock_project
    mock_gl.groups.get.return_value.projects.list.side_effect = [[mock_project], []]

    # Mock get_repo_members
    mock_repo_members = [MockMember(1, "user1"), MockMember(3, "user3")]
    mock_project.members.list.side_effect = [mock_repo_members, []]
    mock_project.members.delete.side_effect = GitlabDeleteError("Failed to delete")

    grd.remove_direct_members(mock_gl, 1, dry_run=False)

    mock_print.assert_any_call(
        "Failed to remove user1 from test-project: Failed to delete"
    )
    mock_project.members.delete.assert_called_once_with(1)


@patch("argparse.ArgumentParser")
@patch("gitlab.Gitlab")
@patch("gitlab_remove_doubleton_members.gitlab_remove_doubleton_members.remove_direct_members")
def test_main(mock_remove_members, mock_gitlab_class, mock_argparse):
    """Test the main function."""
    mock_args = mock_argparse.return_value.parse_args.return_value
    mock_args.gitlab_url = "https://gitlab.com"
    mock_args.token = "token"
    mock_args.group = "group_id"
    mock_args.dry_run = False
    mock_args.exclude_users = None

    mock_gl = mock_gitlab_class.return_value

    grd.main()

    mock_gitlab_class.assert_called_once_with(
        "https://gitlab.com", private_token="token", ssl_verify=False
    )
    mock_remove_members.assert_called_once_with(mock_gl, "group_id", False, None)
