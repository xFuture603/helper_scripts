#!/usr/bin/env python3

import requests
import argparse
import json


class GitLabAPI:
    def __init__(self, gitlab_url, access_token):
        self.gitlab_url = gitlab_url + "/api/v4"
        self.access_token = access_token
        self.headers = {"Authorization": f"Bearer {self.access_token}"}

    def list_projects(self, per_page=50, order_by="id", sort="asc"):
        """
        List all projects accessible by the user using keyset pagination.
        """
        projects = []
        url = f"{self.gitlab_url}/projects?pagination=keyset&per_page={per_page}&order_by={order_by}&sort={sort}"

        while url:
            response = requests.get(url, headers=self.headers)
            response_data = self._handle_response(response)
            projects.extend(response_data)
            url = self._get_next_page_url(response)
        return projects

    def get_pipeline_schedules(self, project_id, per_page=1000):
        """
        Get active pipeline schedules for a specific project.
        """
        url = f"{self.gitlab_url}/projects/{project_id}/pipeline_schedules?per_page={per_page}&scope=active"
        response = requests.get(url, headers=self.headers)
        return self._handle_response(response)

    def _handle_response(self, response):
        """
        Handle the HTTP response from the API.
        """
        if response.status_code in (200, 201):
            return response.json()
        elif response.status_code == 403:
            print(f"Access denied: {response.url}")
        elif response.status_code == 404:
            print(f"Not found: {response.url}")
        else:
            response.raise_for_status()

    def _get_next_page_url(self, response):
        """
        Extract the next page URL from the Link header.
        """
        link_header = response.headers.get("Link")
        if link_header:
            links = link_header.split(",")
            for link in links:
                if 'rel="next"' in link:
                    next_url = link[link.find("<") + 1 : link.find(">")]
                    return next_url
        return None


def main(gitlab_url, access_token, owner):
    gitlab = GitLabAPI(gitlab_url, access_token)

    # List all projects
    projects = gitlab.list_projects()

    for project in projects:
        project_id = project["id"]
        # Get active pipeline schedules for each project
        schedules = gitlab.get_pipeline_schedules(project_id)

        if schedules:
            for schedule in schedules:
                # Check for schedule owner
                if schedule["owner"]["username"] == owner:
                    print(json.dumps(schedule))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List all pipeline schedules with specific owner."
    )
    parser.add_argument(
        "-u",
        "--gitlab-url",
        type=str,
        default="https://gitlab.com",
        help="GitLab base url.",
    )
    parser.add_argument(
        "-t",
        "--access-token",
        type=str,
        required=True,
        help="GitLab access token (api scope).",
    )
    parser.add_argument(
        "-o",
        "--owner",
        type=str,
        required=True,
        help="Pipeline schedule owner to search for.",
    )
    args = parser.parse_args()

    main(args.gitlab_url, args.access_token, args.owner)
