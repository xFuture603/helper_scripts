# GitLab Group Audit – Blocked and Banned Users

This script audits GitLab groups to identify blocked and banned users, including their group and project memberships. It connects to a GitLab instance using its REST API and reports users with restricted access.

## Description

The script scans a specified GitLab group (and all its subgroups), collects all unique members, and checks their account states.  
It identifies users who are **blocked** or **banned**, then lists the groups and projects they belong to.

This tool helps administrators verify access control, detect inactive or restricted accounts, and maintain compliance across GitLab organizations.

## Use Cases

- Identify blocked or banned users in a group hierarchy.
- Generate a report with blocked/banned accounts.

## Requirements

- Python 3.12 or higher
- `python-gitlab` and `urllib3` package

Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

The script can be run from the command line.
You need to provide the GitLab URL, a personal access token (API scope), and the group ID or path to audit.

```
usage: gitlab_find_banned_and_blocked_accounts.py [-h] -u GITLAB_URL -t TOKEN -g GROUP

Audit GitLab group for blocked and banned users.

options:
  -h, --help            show this help message and exit
  -u GITLAB_URL, --gitlab-url GITLAB_URL
                        The base URL of the GitLab instance.
  -t TOKEN, --token TOKEN
                        GitLab personal access token.
  -g GROUP, --group GROUP
                        The group ID or path to audit (e.g., 'my-group' or '123').
```

## Example

```bash
python gitlab_find_banned_and_blocked_accounts.py -u https://gitlab.example.com -t my-gitlab-token -g my-group
```

## Example Output

```md
================================================================================
AUDIT REPORT FOR GROUP: my-org/devops
================================================================================

=== BLOCKED USERS ===
John Doe
Username: jdoe
Email: jdoe@example.com
User ID: 42
Groups (2): - my-org/devops (ID: 101) - my-org/devops/backend (ID: 102)
Projects (1): - my-org/devops/api-service (ID: 305)

=== BANNED USERS ===
No banned users found in this group hierarchy.

================================================================================
SUMMARY: 1 blocked, 0 banned
================================================================================
```

## Notes

The script recursively analyzes all subgroups of the specified group.

Requires a GitLab personal access token with API permissions.

Large hierarchies may result in longer runtimes due to API pagination.

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
