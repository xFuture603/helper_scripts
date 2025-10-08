#!/usr/bin/env python3
"""
A script to audit GitLab groups for blocked and banned users.
It identifies users with restricted access and shows their group and project memberships.
"""

import argparse
import logging
import warnings
import gitlab
from urllib3.exceptions import InsecureRequestWarning

# Suppress the InsecureRequestWarning from urllib3
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
    """Fetch all groups under the specified group ID, including subgroups."""
    all_groups = []
    group = gl.groups.get(group_id)
    all_groups.append(group)

    subgroups = get_paginated_data(group.subgroups.list)
    for subgroup in subgroups:
        all_groups.append(gl.groups.get(subgroup.id))
        all_groups.extend(get_all_groups(gl, subgroup.id))

    return all_groups


def collect_all_members(groups):
    """Collect all unique members from a list of groups."""
    all_members = {}
    for group in groups:
        logging.info("Fetching members from group: %s", group.full_path)
        members = get_paginated_data(group.members.list)
        for member in members:
            if member.id not in all_members:
                all_members[member.id] = {
                    "username": member.username,
                    "name": member.name,
                    "groups": [],
                }
            all_members[member.id]["groups"].append(
                {"id": group.id, "name": group.name, "full_path": group.full_path}
            )
    return all_members


def filter_users_by_state(gl, members, state):
    """Filter members by their state (blocked, banned, etc.)."""
    filtered_users = {}
    logging.info("Checking user states for %d unique members...", len(members))

    for user_id, member_info in members.items():
        try:
            user_detail = gl.users.get(user_id)
            if user_detail.state == state:
                filtered_users[user_id] = {
                    "name": user_detail.name,
                    "username": user_detail.username,
                    "email": getattr(user_detail, "email", "N/A"),
                    "groups": member_info["groups"],
                    "projects": [],
                }
        except gitlab.exceptions.GitlabGetError as err:
            logging.warning("Could not fetch user %d: %s", user_id, err)
    return filtered_users


def get_group_projects(gl, group_id):
    """Get all projects in a group, including those in subgroups."""
    group = gl.groups.get(group_id)
    return get_paginated_data(group.projects.list, include_subgroups=True)


def find_users_in_projects(gl, projects, target_users):
    """Find which target users are members of given projects."""
    target_user_ids = set(target_users.keys())
    for project in projects:
        try:
            full_project = gl.projects.get(project.id)
            logging.info("Checking project: %s", full_project.path_with_namespace)
            members = get_paginated_data(full_project.members.list)
            for member in members:
                if member.id in target_user_ids:
                    target_users[member.id]["projects"].append(
                        {
                            "id": full_project.id,
                            "name": full_project.name,
                            "path": full_project.path_with_namespace,
                        }
                    )
        except gitlab.exceptions.GitlabGetError as err:
            logging.warning("Could not fetch project %d: %s", project.id, err)


def print_report(target_group, blocked_users, banned_users):
    """Print the audit report."""
    print("\n" + "=" * 80)
    print(f"AUDIT REPORT FOR GROUP: {target_group.full_path}")
    print("=" * 80)

    def print_user_section(title, users, icon):
        print(f"\n=== {title.upper()} ===")
        if not users:
            print(f"No {title.lower()} users found in this group hierarchy.")
            return
        for user_id, user_info in users.items():
            print(f"\n{icon} {user_info['name']}")
            print(f"   Username: {user_info['username']}")
            print(f"   Email: {user_info['email']}")
            print(f"   User ID: {user_id}")
            if user_info["groups"]:
                print(f"   Groups ({len(user_info['groups'])}):")
                for group in user_info["groups"]:
                    print(f"     - {group['full_path']} (ID: {group['id']})")
            if user_info["projects"]:
                unique_projects = {
                    (p["id"], p["name"], p["path"]) for p in user_info["projects"]
                }
                print(f"   Projects ({len(unique_projects)}):")
                for pid, _, ppath in unique_projects:
                    print(f"     - {ppath} (ID: {pid})")

    print_user_section("Blocked Users", blocked_users, "🧑")
    print_user_section("Banned Users", banned_users, "🚫")

    print("\n" + "=" * 80)
    print(f"SUMMARY: {len(blocked_users)} blocked, {len(banned_users)} banned")
    print("=" * 80)


def main():
    """Main function to parse arguments and audit GitLab group for blocked/banned users."""
    parser = argparse.ArgumentParser(
        description="Audit GitLab group for blocked and banned users.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s -u https://gitlab.example.com -t my-gitlab-token -g my-group\n"
            "  %(prog)s -u https://gitlab.example.com -t my-gitlab-token -g 123"
        ),
    )
    parser.add_argument(
        "-u", "--gitlab-url", required=True, help="The base URL of the GitLab instance."
    )
    parser.add_argument(
        "-t", "--token", required=True, help="GitLab personal access token."
    )
    parser.add_argument(
        "-g",
        "--group",
        required=True,
        help="The group ID or path to audit (e.g., 'my-group' or '123').",
    )
    args = parser.parse_args()

    gl = gitlab.Gitlab(args.gitlab_url, private_token=args.token, ssl_verify=False)

    logging.info("Analyzing group: %s", args.group)
    try:
        target_group = gl.groups.get(args.group)
    except gitlab.exceptions.GitlabGetError as err:
        logging.error("Error: Could not find group '%s': %s", args.group, err)
        return

    logging.info("Found group: %s (ID: %s)", target_group.name, target_group.id)
    logging.info("Full path: %s", target_group.full_path)

    logging.info("Fetching subgroups...")
    all_groups = get_all_groups(gl, target_group.id)
    logging.info("Total groups (including parent): %d", len(all_groups))

    logging.info("Fetching members from all groups...")
    all_members = collect_all_members(all_groups)
    logging.info("Total unique members found: %d", len(all_members))

    blocked_users = filter_users_by_state(gl, all_members, "blocked")
    banned_users = filter_users_by_state(gl, all_members, "banned")

    logging.info("Blocked users found: %d", len(blocked_users))
    logging.info("Banned users found: %d", len(banned_users))

    if blocked_users or banned_users:
        logging.info("Fetching projects...")
        projects = get_group_projects(gl, target_group.id)
        logging.info("Total projects found: %d", len(projects))
        logging.info("Analyzing project memberships...")
        target_users = {**blocked_users, **banned_users}
        find_users_in_projects(gl, projects, target_users)

    print_report(target_group, blocked_users, banned_users)


if __name__ == "__main__":
    main()
