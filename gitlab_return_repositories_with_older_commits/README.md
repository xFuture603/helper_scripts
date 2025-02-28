# GitLab Repository Check Commit Age Script

This script lists GitLab repositories whose latest commit is older than a specified
timestamp or have no commits at all. It efficiently handles paginated API responses
and processes repositories, including those in subgroups.

## Description

The script connects to a GitLab instance and retrieves all projects within a specified
group (and its subgroups), or across all accessible projects if no group is provided.
It then checks the date of the latest commit in each repository and prints a list of
repositories that have either no commits or have not been updated since a given
timestamp. This is useful for identifying inactive repositories that might be
candidates for archiving or further review.

## Use Cases

- **Audit Repository Activity**: Identify repositories that have not been updated in a
  long time.
- **Maintenance**: Locate repositories that may be candidates for archiving or clean-up
  due to inactivity.
- **Compliance**: Ensure repositories are actively maintained in accordance with
  organizational policies.

## Requirements

- Python 3
- `python-gitlab` library
- `python-dateutil` library
- `urllib3` library

## Usage

The script can be executed from the command line. You need to provide the GitLab URL,
a personal access token with the appropriate API scope, and a threshold timestamp in
ISO8601 format. Optionally, you can specify a group ID or path to limit the search to
a specific group.

```sh
usage: gitlab_return_repositories_with_older_commits.py [-h] [--group GROUP]
                                                      gitlab_url access_token timestamp

List GitLab repositories with latest commit older than a given timestamp or with no commit.

positional arguments:
  gitlab_url      The base URL of the GitLab instance (e.g., https://gitlab.com)
  access_token    GitLab personal access token
  timestamp       Threshold timestamp (ISO8601 format, e.g., 2021-01-01T00:00:00Z)

optional arguments:
  -h, --help      show this help message and exit
  --group GROUP   Optional: Group ID or path to list repositories from a specific group only
```

## Example

To run the script and list repositories with the latest commit older than a given date, use:

```bash
python gitlab_return_repositories_with_older_commits.py \
    https://gitlab.example.com your_access_token 2022-01-01T00:00:00Z --group your_group
```

## Example Output

```bash
Fetching projects for group your_group
Project some_group/repo1 (ID: 101) last commit: 2021-12-31 23:59:59+00:00
Project some_group/repo2 (ID: 102) last commit: 2021-06-15 12:34:56+00:00
No commits found for project some_group/repo3 (ID: 103)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
