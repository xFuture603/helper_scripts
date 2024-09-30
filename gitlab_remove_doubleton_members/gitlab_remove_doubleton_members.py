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
# an error in certain infrastructures.
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


def get_all_groups(gl, group_id):
    """Fetch all groups under the specified group ID."""
    all_groups = []
    group = gl.groups.get(group_id)
    all_groups.append(group)

    # Recursively get subgroups
    subgroups = get_paginated_data(group.subgroups.list)
    for subgroup in subgroups:
        all_groups.append(subgroup)
        all_groups.extend(get_all_groups(gl, subgroup.id))

    return all_groups


def get_group_members(gl, group_id):
    """Get all members of a group, including inherited members."""
    group = gl.groups.get(group_id)
    members = get_paginated_data(group.members.list)
    logging.info(f"Fetched group members for group {group_id} (URL: {group.web_url})")
    return members


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


def remove_direct_members(gl, group_id, dry_run, repo_scope=None, exclude_users=None):
    """Remove direct members of repositories that are part of the group and have inherited permissions."""
    all_groups = get_all_groups(gl, group_id)
    all_group_member_ids = set()

    # Collect all members from all groups for quick access
    for group in all_groups:
        members = get_group_members(gl, group.id)
        all_group_member_ids.update(member.id for member in members)

    logging.info("Collected all group member IDs from specified group and subgroups.")

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

    processed_projects = set()  # Track processed project IDs

    # Loop through each repository
    for project in projects:
        project_id = project.id

        # Check if project has already been processed
        if project_id in processed_projects:
            logging.info(f"Skipping already processed project {project.name} (ID: {project_id})")
            continue

        # Add to processed projects
        processed_projects.add(project_id)

        # Fetch project details to ensure complete data
        project = gl.projects.get(project_id)  # Ensure we have all project data
        project_url = project.web_url  # Get the project URL
        logging.info(f"Processing repository {project.name} (ID: {project.id}, URL: {project_url})")

        # Get direct members of the project
        repo_members = get_repo_members(gl, project.id)

        # Construct the URL for the members tab of the project
        members_url = f"{gl.url}/{project.path_with_namespace}/-/project_members"

        for member in repo_members:
            if member.id in all_group_member_ids:
                # Check if the member is in the exclude list
                if exclude_users and member.username in exclude_users:
                    logging.info(
                        Fore.LIGHTBLUE_EX
                        + "Skipping member %s as they are in the exclude list for repository %s"
                        + Style.RESET_ALL,
                        member.username,
                        project.name,
                    )
                    continue

                if dry_run:
                    logging.info(
                        Fore.YELLOW
                        + "Dry-run: Would remove directly added member %s from repository %s (%s) "
                        + "as they already have inherited access."
                        + Style.RESET_ALL,
                        member.username,
                        project.name,
                        members_url,
                    )
                else:
                    try:
                        logging.info(
                            Fore.GREEN
                            + "Removing member %s from repository %s"
                            + Style.RESET_ALL,
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
        --exclude-users (optional): List of usernames to exclude from removal.

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
    parser.add_argument(
        "--exclude-users",
        nargs="*",
        help="Optional list of usernames to exclude from removal",
    )

    args = parser.parse_args()

    # Initialize GitLab connection
    gl = gitlab.Gitlab(
        args.gitlab_url, private_token=args.access_token, ssl_verify=False
    )

    # Run the member cleanup process
    remove_direct_members(gl, args.group_id, args.dry_run, args.repo_scope, args.exclude_users)


if __name__ == "__main__":
    main()
