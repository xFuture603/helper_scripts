#!/usr/bin/python3

import requests
import argparse

# GitHub API base URL
BASE_URL = "https://api.github.com"


def get_user_repos(headers):
    """Get all repositories owned by the user (including private ones)"""
    url = f"{BASE_URL}/user/repos"
    params = {"visibility": "all", "affiliation": "owner"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_org_repos(org, headers):
    """Get all repositories for a given organization (including private ones)"""
    url = f"{BASE_URL}/orgs/{org}/repos"
    params = {"visibility": "all"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def get_open_pull_requests(repo_full_name, headers):
    """Get all open pull requests for a given repository"""
    url = f"{BASE_URL}/repos/{repo_full_name}/pulls"
    params = {"state": "open"}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()


def needs_review(pull_request):
    """Determine if a pull request needs review"""
    return bool(pull_request["requested_reviewers"] or pull_request["requested_teams"])


def main(username, token, owners):
    # Define headers for API requests
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    # Create an empty dictionary to store repository information
    repos = {}

    for owner in owners:
        # Fetch repositories for user account
        if owner == username:
            user_repos = get_user_repos(headers)
            for repo in user_repos:
                repo_full_name = repo["full_name"]
                print(f"Checking repository: {repo_full_name}")
                pull_requests = get_open_pull_requests(repo_full_name, headers)

                # Update repository information with pull request details
                repos[repo_full_name] = {
                    "has_needing_review": any(needs_review(pr) for pr in pull_requests)
                }

        else:
            # Fetch repositories for organization account
            org_repos = get_org_repos(owner, headers)
            for repo in org_repos:
                repo_full_name = repo["full_name"]
                print(f"Checking repository: {repo_full_name}")
                pull_requests = get_open_pull_requests(repo_full_name, headers)

                # Update repository information with pull request details
                repos[repo_full_name] = {
                    "has_needing_review": any(needs_review(pr) for pr in pull_requests)
                }

    # Sort the dictionary based on the "has_needing_review" flag (descending)
    sorted_repos = sorted(
        repos.items(), key=lambda x: x[1]["has_needing_review"], reverse=True
    )

    # Print repositories based on the sorted order
    for repo_name, info in sorted_repos:
        if info['has_needing_review']:  # Check if review is needed
            print(f'Repository: {repo_name}')
            pull_requests = get_open_pull_requests(repo_name, headers)
            for pr in pull_requests:
                if needs_review(pr):
                    print(f'  PR #{pr["number"]} needs review: {pr["html_url"]}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fetch open pull requests that need review."
    )
    parser.add_argument("--username", required=True, help="GitHub username")
    parser.add_argument("--token", required=True, help="GitHub personal access token")
    parser.add_argument(
        "--owners",
        nargs="+",
        required=True,
        help="List of user accounts and organization accounts to scan",
    )

    args = parser.parse_args()

    main(args.username, args.token, args.owners)
