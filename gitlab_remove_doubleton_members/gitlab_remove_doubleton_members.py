#!/usr/bin/env python3

"""
A script to remove direct members from GitLab repositories that are part of a specified group.
It efficiently handles paginated API responses and processes repositories,
including those in subgroups.
"""

import argparse
import logging
import warnings
import gitlab
from urllib3.exceptions import InsecureRequestWarning
from colorama import Fore, Style

# Suppress the InsecureRequestWarning from urllib3 because you will get
# a error in certain infrastructures..
warnings.simplefilter("ignore", InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")


def get_paginated_data(get_function, **kwargs):
    """Helper function to handle paginated API results."""
    all_data = []
    page = 1
    while True:
        data = get_function(page=page, per_page=100, **kwargs)
        if not data:
            break
        all_data.extend(data)
        page += 1
    return all_data


def get_group_members(gl, group_id):
    """Get all members of a group, including inherited members."""
    group = gl.groups.get(group_id)
    return get_paginated_data(group.members.list)


def get_repo_members(gl, repo_id):
    """Get all direct members of a repository (project)."""
    project = gl.projects.get(repo_id)
    return get_paginated_data(project.members.list)


def get_group_projects(gl, group_id):
    """Get all projects in a group, including those in subgroups."""
    group = gl.groups.get(group_id)
    all_projects = get_paginated_data(group.projects.list)

    # Recursively get projects from subgroups
    subgroups = get_paginated_data(group.subgroups.list)
    for subgroup in subgroups:
        logging.info(
            "Fetching projects from subgroup %s (ID: %s)", subgroup.name, subgroup.id
        )
        all_projects.extend(get_group_projects(gl, subgroup.id))

    return all_projects


def remove_direct_members(gl, group_id, dry_run, repo_scope=None):
    """Remove direct members of repositories that are part of the group."""
    # Get all members of the group
    logging.info("Fetching members of group %s", group_id)
    group_members = get_group_members(gl, group_id)
    group_member_ids = {member.id for member in group_members}

    # Get all repositories in the group, including subgroups
    logging.info("Fetching repositories for group %s", group_id)
    projects = get_group_projects(gl, group_id)

    # Filter repositories if scope is provided
    if repo_scope:
        projects = [project for project in projects if project.name in repo_scope]

    # Ensure that we have a valid list of projects
    if not projects:
        logging.info("No repositories found for group %s", group_id)
        return

    # Loop through each repository
    for project in projects:
        logging.info("Processing repository %s (ID: %s)", project.name, project.id)

        # Get direct members of the project
        repo_members = get_repo_members(gl, project.id)

        # Construct the URL for the members tab of the project
        project_url = f"{gl.url}/{project.path_with_namespace}/-/project_members"

        for member in repo_members:
            if member.id in group_member_ids:
                # Direct member found in the group
                if dry_run:
                    # Use lazy formatting, add color, and include the project URL
                    logging.info(
                        Fore.YELLOW
                        + "Dry-run: Would remove member %s from repository %s (%s)"
                        + Style.RESET_ALL,
                        member.username,
                        project.name,
                        project_url,
                    )
                else:
                    try:
                        logging.info(
                            "Removing member %s from repository %s",
                            member.username,
                            project.name,
                        )
                        project.members.delete(member.id)
                    except gitlab.exceptions.GitlabDeleteError as e:
                        logging.error(
                            "Failed to remove %s from %s: %s",
                            member.username,
                            project.name,
                            e,
                        )


def main():
    """Main function to parse arguments and clean up repository members in a GitLab group.

    This function handles the following steps:
    1. Parses command-line arguments.
    2. Connects to the GitLab instance using the provided URL and access token.
    3. Fetches and processes the group and its repositories.
    4. Optionally performs a dry-run or removes direct members from repositories
       based on the arguments.

    Command-line arguments:
        gitlab_url (str): The base URL of the GitLab instance.
        access_token (str): GitLab personal access token.
        group_id (int or str): The ID or path of the group to clean up.
        --dry-run (optional): If set, print members that would be removed without making changes.
        --repo-scope (optional): List of repositories to limit the scope to certain repositories.

    Returns:
        None
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="GitLab group repository member cleanup script"
    )
    parser.add_argument("gitlab_url", help="The base URL of the GitLab instance")
    parser.add_argument("access_token", help="GitLab personal access token")
    parser.add_argument(
        "group_id", help="The group ID or path for which to clean up repositories"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="If set, just print members that would be removed",
    )
    parser.add_argument(
        "--repo-scope",
        nargs="*",
        help="Optional list of repository names to limit scope",
    )

    args = parser.parse_args()

    # Initialize GitLab connection
    gl = gitlab.Gitlab(
        args.gitlab_url, private_token=args.access_token, ssl_verify=False
    )

    # Run the member cleanup process
    remove_direct_members(gl, args.group_id, args.dry_run, args.repo_scope)


if __name__ == "__main__":
    main()
