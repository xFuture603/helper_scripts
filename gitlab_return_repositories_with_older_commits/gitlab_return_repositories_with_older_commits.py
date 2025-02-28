#!/usr/bin/env python3
"""
A script to list GitLab repositories whose latest commit is older than a
specified timestamp, or have no commits at all.

Usage:
    ./script.py <gitlab_url> <access_token> <timestamp>
    [--group <group_id_or_path>]

Example:
    ./script.py https://gitlab.example.com YOUR_ACCESS_TOKEN 2022-01-01T00:00:00Z
    --group 1770
"""

import argparse
import logging
import warnings
import gitlab
from gitlab.exceptions import GitlabError
from urllib3.exceptions import InsecureRequestWarning
from dateutil.parser import parse as parse_date  # Requires python-dateutil

# Suppress InsecureRequestWarning from urllib3
warnings.simplefilter("ignore", InsecureRequestWarning)

logging.basicConfig(level=logging.INFO, format="%(message)s")


def get_paginated_data(get_function, **kwargs):
    """
    Retrieve all pages of data using the provided get_function.

    Args:
        get_function: Function to call for each page.
        **kwargs: Additional keyword arguments for the function.

    Returns:
        A list containing all items from paginated responses.
    """
    all_data = []
    page = 1
    while True:
        data = get_function(page=page, per_page=100, **kwargs)
        if not data:
            break
        all_data.extend(data)
        page += 1
    return all_data


def get_all_projects(gl):
    """
    Retrieve all projects accessible to the authenticated user.

    Args:
        gl: An authenticated GitLab instance.

    Returns:
        A list of project objects.
    """
    return get_paginated_data(gl.projects.list)


def get_group_projects(gl, group_id):
    """
    Retrieve all projects in a specific group and its subgroups.

    Args:
        gl: An authenticated GitLab instance.
        group_id: The group ID or path.

    Returns:
        A list of project objects within the group and its subgroups.
    """
    group = gl.groups.get(group_id)
    projects = get_paginated_data(group.projects.list)
    subgroups = get_paginated_data(group.subgroups.list)
    for subgroup in subgroups:
        projects.extend(get_group_projects(gl, subgroup.id))
    return projects


def repository_last_commit_date(project):
    """
    Get the datetime of the latest commit for a project.

    Args:
        project: A GitLab project object.

    Returns:
        A datetime object of the latest commit if available;
        otherwise, None.
    """
    try:
        # Explicitly set get_all=False to fetch only one commit.
        commits = project.commits.list(per_page=1, get_all=False)
        if commits:
            return parse_date(commits[0].committed_date)
    except GitlabError as e:
        logging.error("Error retrieving commits for project %s: %s",
                      project.path_with_namespace, e)
    return None


def main():
    """
    Main entry point for the script. Parses command-line arguments,
    connects to the GitLab instance, fetches projects, and prints repositories
    whose latest commit is older than the provided threshold or that have no
    commits.
    """
    parser = argparse.ArgumentParser(
        description=("List GitLab repositories with latest commit older than a given "
                     "timestamp or no commit at all.")
    )
    parser.add_argument("gitlab_url",
                        help="The base URL of the GitLab instance (e.g., https://gitlab.com)")
    parser.add_argument("access_token", help="GitLab personal access token")
    parser.add_argument(
        "timestamp",
        help=("Threshold timestamp (ISO8601 format, e.g., 2021-01-01T00:00:00Z). "
              "Repositories with the latest commit before this time will be listed.")
    )
    parser.add_argument("--group",
                        help=("Optional: Group ID or path to list repositories from a "
                              "specific group only"))

    args = parser.parse_args()

    try:
        threshold_date = parse_date(args.timestamp)
    except Exception as e:
        logging.error("Failed to parse timestamp: %s", e)
        return

    # Connect to the GitLab instance.
    gl = gitlab.Gitlab(args.gitlab_url, private_token=args.access_token,
                       ssl_verify=False)

    if args.group:
        logging.info("Fetching projects for group %s", args.group)
        projects = get_group_projects(gl, args.group)
    else:
        logging.info("Fetching all accessible projects")
        projects = get_all_projects(gl)

    old_projects = []
    no_commit_projects = []
    for proj_summary in projects:
        try:
            project = gl.projects.get(proj_summary.id)
        except GitlabError as e:
            logging.error("Failed to fetch project %s: %s", proj_summary.id, e)
            continue

        last_commit_date = repository_last_commit_date(project)
        if last_commit_date:
            if last_commit_date < threshold_date:
                old_projects.append(project)
                logging.info("Project %s (ID: %s) last commit: %s",
                             project.path_with_namespace, project.id,
                             last_commit_date)
        else:
            logging.info("No commits found for project %s (ID: %s)",
                         project.path_with_namespace, project.id)
            no_commit_projects.append(project)

    print(f"\nRepositories with latest commit older than {threshold_date}:")
    if not old_projects:
        print("None found.")
    else:
        for project in old_projects:
            print(f"- {project.web_url} (ID: {project.id})")

    print("\nRepositories with no commit found:")
    if not no_commit_projects:
        print("None found.")
    else:
        for project in no_commit_projects:
            print(f"- {project.web_url} (ID: {project.id})")


if __name__ == "__main__":
    main()
