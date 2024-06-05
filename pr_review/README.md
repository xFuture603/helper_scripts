# GitHub Pull Request Review Checker

This script fetches all open pull requests from specified GitHub user and organization accounts, and determines which pull requests need a review. It can handle both personal and organization repositories, including private ones.

## Requirements

- Python 3
- `requests` library
- `argparse` library
- `json` library

You can install the required libraries using:

```sh
pip3 install -r requirements.txt
```

## Usage
The script can be run from the command line. It requires a GitHub username, a personal access token with read privileges for repositories, and a list of GitHub user and organization accounts to scan. Optionally, you can specify an output file to save the formatted results.

```sh
python3 pr_review.py --username <GITHUB_USERNAME> --token <GITHUB_TOKEN> --owners <OWNER1> <OWNER2> <ORG> --output-file <OUTPUT_FILE>
```

## Arguments

- `--username` (required): Your GitHub username.
- `--token` (required): Your GitHub personal access token.
- `--owners` (required): A list of GitHub user accounts and organization accounts to scan for pull requests.
- `--output-file` (optional): A file to save the formatted output in a json file.

## Example Output

When the script is run, it prints the repositories and pull requests that need a review:

```sh
Checking repository: johndoe/repo1
Checking repository: johndoe/repo2
Checking repository: myorganization/repo1
Checking repository: myorganization/repo2
Repository: johndoe/repo1
  PR #1 needs review: https://github.com/johndoe/repo1/pull/1
  PR #2 needs review: https://github.com/johndoe/repo1/pull/2
Repository: myorganization/repo2
  PR #3 needs review: https://github.com/myorganization/repo2/pull/3
```

If an output file is specified, the results are also saved in the specified JSON file:

```json
{
    "repos_with_needed_review_list": [
        "Repository: johndoe/repo1",
        "  PR #1 needs review: https://github.com/johndoe/repo1/pull/1",
        "  PR #2 needs review: https://github.com/johndoe/repo1/pull/2",
        "Repository: myorganization/repo2",
        "  PR #3 needs review: https://github.com/myorganization/repo2/pull/3"
    ]
}
```
## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
