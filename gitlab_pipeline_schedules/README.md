# GitLab Pipeline Schedules Checker

This script lists all pipeline schedules with a specific owner for all projects accessible by a given GitLab user. It uses GitLab's REST API and keyset pagination to efficiently retrieve data.

## Description

The script scans all projects accessible by the user, retrieves active pipeline schedules, and checks for schedules owned by a specified user. It uses keyset pagination for efficient data retrieval.

## Use Cases

- **Audit Pipeline Schedules**: Identify pipeline schedules owned by a specific user across all projects.
- **Manage Permissions**: Ensure that pipeline schedules are managed by the correct users.
- **Monitor Activity**: Keep track of active pipeline schedules for organizational purposes.

## Requirements

- Python 3
- `requests` library

## Usage

The script can be run from the command line. You need to provide the GitLab URL, an access token with API scope, and the username of the pipeline schedule owner to search for.

```sh
usage: gitlab_pipeline_schedules.py [-h] [-u GITLAB_URL] -t ACCESS_TOKEN -o OWNER

List all pipeline schedules with a specific owner.

options:
  -h, --help            show this help message and exit
  -u GITLAB_URL, --gitlab-url GITLAB_URL
                        GitLab base URL (default: https://gitlab.com)
  -t ACCESS_TOKEN, --access-token ACCESS_TOKEN
                        GitLab access token (API scope)
  -o OWNER, --owner OWNER
                        Pipeline schedule owner to search for
```

## Example
```
python gitlab_pipeline_schedules.py -u https://gitlab.example.com -t your_access_token -o mopo
```

## Example Output
```
{
    "id": 13,
    "description": "Test schedule pipeline",
    "ref": "refs/heads/main",
    "cron": "* * * * *",
    "cron_timezone": "Asia/Tokyo",
    "next_run_at": "2017-05-19T13:41:00.000Z",
    "active": true,
    "created_at": "2017-05-19T13:31:08.849Z",
    "updated_at": "2017-05-19T13:40:17.727Z",
    "owner": {
        "name": "Administrator",
        "username": "mopo",
        "id": 1,
        "state": "active",
        "avatar_url": "http://www.gravatar.com/avatar/e64c7d89f26bd1972efa854d13d7dd61?s=80&d=identicon",
        "web_url": "https://gitlab.example.com/root"
    }
}
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
