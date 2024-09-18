import argparse
import gitlab
import logging
import warnings
from urllib3.exceptions import InsecureRequestWarning

# Suppress the InsecureRequestWarning from urllib3
warnings.simplefilter('ignore', InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)

def get_paginated_data(get_function, **kwargs):
    """
    Helper function to handle paginated API results.

    Args:
        get_function (function): Function to fetch data.
        **kwargs: Additional keyword arguments for the function.

    Returns:
        list: A list of all paginated data.
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

def get_group_members(gl, group_id):
    """
    Get all members of a group, including inherited members.

    Args:
        gl (gitlab.Gitlab): GitLab connection object.
        group_id (int or str): The group ID or path.

    Returns:
        list: A list of members in the group.
    """
    group = gl.groups.get(group_id)
    return get_paginated_data(group.members.list)

def get_repo_members(gl, repo_id):
    """
    Get all direct members of a repository (project).

    Args:
        gl (gitlab.Gitlab): GitLab connection object.
        repo_id (int or str): The repository ID.

    Returns:
        list: A list of direct members of the repository.
    """
    project = gl.projects.get(repo_id)
    return get_paginated_data(project.members.list)

def get_group_projects(gl, group_id):
    """
    Get all projects in a group, including those in subgroups.

    Args:
        gl (gitlab.Gitlab): GitLab connection object.
        group_id (int or str): The group ID or path.

    Returns:
        list: A list of projects in the group and its subgroups.
    """
    group = gl.groups.get(group_id)
    all_projects = get_paginated_data(group.projects.list)

    # Recursively get projects from subgroups
    subgroups = get_paginated_data(group.subgroups.list)
    for subgroup in subgroups:
        logging.info(f"Fetching projects from subgroup {subgroup.name} (ID: {subgroup.id})")
        all_projects.extend(get_group_projects(gl, subgroup.id))

    return all_projects

def remove_direct_members(gl, group_id, dry_run, repo_scope=None):
    """
    Remove direct members of repositories that are part of the group.

    Args:
        gl (gitlab.Gitlab): GitLab connection object.
        group_id (int or str): The group ID or path.
        dry_run (bool): If True, only print the actions without performing them.
        repo_scope (list of str, optional): List of repository names to limit scope.
    """
    # Get all members of the group
    logging.info(f"Fetching members of group {group_id}")
    group_members = get_group_members(gl, group_id)
    group_member_ids = {member.id for member in group_members}

    # Get all repositories in the group, including subgroups
    logging.info(f"Fetching repositories for group {group_id}")
    projects = get_group_projects(gl, group_id)

    # Filter repositories if scope is provided
    if repo_scope:
        projects = [project for project in projects if project.name in repo_scope]

    # Ensure that we have a valid list of projects
    if not projects:
        logging.info(f"No repositories found for group {group_id}")
        return

    # Loop through each repository
    for project in projects:
        logging.info(f"Processing repository {project.name} (ID: {project.id})")

        # Get direct members of the project
        repo_members = get_repo_members(gl, project.id)

        for member in repo_members:
            if member.id in group_member_ids:
                # Direct member found in the group
                if dry_run:
                    logging.info(f"Dry-run: Would remove member {member.username} from repository {project.name}")
                else:
                    try:
                        logging.info(f"Removing member {member.username} from repository {project.name}")
                        project.members.delete(member.id)
                    except gitlab.exceptions.GitlabDeleteError as e:
                        logging.error(f"Failed to remove {member.username} from {project.name}: {e}")

def main():
    """
    Main function to parse arguments and run the member cleanup process.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="GitLab group repository member cleanup script")
    parser.add_argument("gitlab_url", help="The base URL of the GitLab instance")
    parser.add_argument("access_token", help="GitLab personal access token")
    parser.add_argument("group_id", help="The group ID or path for which to clean up repositories")
    parser.add_argument("--dry-run", action="store_true", help="If set, just print members that would be removed")
    parser.add_argument("--repo-scope", nargs="*", help="Optional list of repository names to limit scope")

    args = parser.parse_args()

    # Initialize GitLab connection
    gl = gitlab.Gitlab(args.gitlab_url, private_token=args.access_token, ssl_verify=False)

    # Run the member cleanup process
    remove_direct_members(gl, args.group_id, args.dry_run, args.repo_scope)

if __name__ == "__main__":
    main()
