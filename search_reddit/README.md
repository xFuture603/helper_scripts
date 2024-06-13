# Reddit Search Tool

This script searches specified subreddits on Reddit for a specific string and retrieves relevant posts that match the criteria. It excludes image URLs from the results to focus on textual content.

## Use Cases

You can use this script to quickly find discussions or posts containing specific keywords across multiple subreddits. It's particularly useful for monitoring topics of interest or conducting research on Reddit.

## Requirements

- Python 3
- Reddit App
- `praw` library
- `argparse` library
- `colorama` library (optional for colored output)

You can install the required libraries using:

```sh
pip3 install -r requirements.txt
```

## Usage

The script can be run from the command line. It requires Reddit API credentials (client ID, client secret, and user agent), a list of subreddits to search in, and a query string to search for.

```sh
python3 search_reddit.py --client_id <CLIENT_ID> --client_secret <CLIENT_SECRET> --user_agent <USER_AGENT> --subreddits <SUBREDDITS> --query <QUERY> --limit <LIMIT>
```

## Arguments

- `--client_id` (required): Your Reddit API client ID.
- `--client_secret` (required): Your Reddit API client secret.
- `--user_agent` (required): Your Reddit API user agent (a descriptive string).
- `--subreddits` (required): Comma-separated list of subreddits to search in (e.g., devops, sysadmin, SRE).
- `--query` (required): The string to search for within the specified subreddits.
- `--limit` (optional): Number of results to return per subreddit (default: 10).

## Example Output

When the script is run, it prints the results with formatted output:

```sh
Subreddit: subdreddit1
URL: https://reddit.com/r/subdreddit1/post/123456
Date: 2024-06-15 13:45:00

Subreddit: subreddit2
URL: https://reddit.com/r/subdreddit2/post/7822222
Date: 2024-06-15 14:30:00
```

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details.
