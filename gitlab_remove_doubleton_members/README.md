# GitLab Direct Members Cleanup Script

This script removes direct members from GitLab repositories that are part of a specified group. It efficiently handles paginated API responses and processes repositories, including those in subgroups.

## Description

The script connects to a GitLab instance, retrieves all projects within a specified group (and its subgroups), and removes direct members who are also part of the group. This is useful for maintaining clean and consistent access control across repositories by ensuring that members are not directly added if they are already covered by group membership.

## Use Cases

- **Clean Up Direct Members**: Ensure that members who are already part of a group do not have redundant direct access to repositories.
- **Maintain Access Control**: Automatically manage repository permissions based on group memberships.
- **Audit Memberships**: Verify that repository access aligns with group memberships.

## Requirements

- Python 3
- `gitlab` library
- `urllib3` library
- `colorama` library (for colored output)

## Usage

The script can be executed from the command line. You need to provide the GitLab URL, an access token with API scope, and the group ID or path. You can also specify a list of repositories to limit the scope and use a dry-run option to preview changes without making modifications.

```sh
usage: gitlab_remove_doubleton_members.py [-h] [-u GITLAB_URL] -t ACCESS_TOKEN -g GROUP_ID [--dry-run] [--exclude-users USER1 USER2]

Remove direct members from repositories that are part of a specified GitLab group.

options:
  -h, --help            show this help message and exit
  -u GITLAB_URL, --gitlab-url GITLAB_URL
                        GitLab base URL (default: https://gitlab.com)
  -t ACCESS_TOKEN, --access-token ACCESS_TOKEN
                        GitLab access token (API scope)
  -g GROUP_ID, --group-id GROUP_ID
                        The group ID or path for which to clean up repositories
  --dry-run              If set, just print members that would be removed
  --exclude-users
                        Optional list of usernames to exclude from removal.

```

## Example

To run the script and remove direct members from repositories within a group, use:

```sh
python gitlab_remove_doubleton_members.py -u https://gitlab.example.com -t your_access_token -g your_group
```
## Example Output

```sh
Fetching members of group 1765555
Fetching repositories for group 1765555
Fetching projects from subgroup Projects (ID: 17899)
Fetching projects from subgroup Automation (ID: 17900)
Fetching projects from subgroup Linting (ID: 17901)
Processing repository Automation Templates (ID: 1304)
Processing repository Linting Boilerplate (ID: 1513)
Processing repository Project Templates (ID: 19951)
Dry-run: Would remove member $member from repository Linting (https://gitlab.example.com/projects/linting/-/project_members)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
