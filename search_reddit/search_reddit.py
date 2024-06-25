#!/usr/bin/env python3

"""
A script to search subreddits for a specific string.
"""

from datetime import datetime, timezone
import argparse
import praw
from colorama import Fore, Style


def is_image_url(url):
    """
    Check if the given URL ends with a common image file extension.

    :param url: URL string to check.
    :return: True if URL ends with an image extension, False otherwise.
    """
    image_extensions = [".jpg", ".jpeg", ".png", ".gif"]
    return any(url.lower().endswith(ext) for ext in image_extensions)


def search_in_subreddits(reddit, subreddits, query, limit=10):
    """
    Search for a specific string in a list of subreddits (excluding image URLs).

    :param reddit: Initialized Reddit instance.
    :param subreddits: List of subreddit names to search in.
    :param query: The string to search for.
    :param limit: Number of results to return per subreddit.
    :return: List of dictionaries with 'subreddit', 'url', and 'created_utc'
             as keys containing the subreddit name, URLs of submissions, and creation timestamp.
    """
    results = []
    for subreddit_name in subreddits:
        subreddit = reddit.subreddit(subreddit_name)
        for submission in subreddit.search(query, sort="new", limit=limit):
            # Check if the query string is in the title or selftext (case insensitive)
            title_contains_query = query.lower() in submission.title.lower()
            selftext_contains_query = query.lower() in submission.selftext.lower()
            if title_contains_query or selftext_contains_query:
                # Check if the URL is not an image URL
                if not is_image_url(submission.url):
                    results.append(
                        {
                            "subreddit": subreddit_name,
                            "url": submission.url,
                            "created_utc": submission.created_utc,
                        }
                    )
    return results


def main(client_id, client_secret, user_agent, subreddits, query, limit):
    """
    Main function to search Reddit for a specific string in specified subreddits and print results.

    :param client_id: Reddit API client ID.
    :param client_secret: Reddit API client secret.
    :param user_agent: Reddit API user agent.
    :param subreddits: Comma-separated list of subreddit names to search in.
    :param query: The string to search for.
    :param limit: Number of results to return per subreddit.
    """
    # Initialize the Reddit client
    reddit = praw.Reddit(
        client_id=client_id, client_secret=client_secret, user_agent=user_agent
    )

    # Convert the comma-separated subreddits string to a list
    subreddit_list = subreddits.split(",")

    # Perform the search
    results = search_in_subreddits(reddit, subreddit_list, query, limit)

    # Print the results with formatted output
    for result in results:
        created_utc = result["created_utc"]
        created_datetime_utc = datetime.fromtimestamp(created_utc, tz=timezone.utc)
        created_date = created_datetime_utc.strftime("%Y-%m-%d %H:%M:%S")

        print(f"Subreddit: {Fore.GREEN}{result['subreddit']}{Style.RESET_ALL}")
        print(f"URL: {result['url']}")
        print(f"Date: {created_date}")
        print()  # Print an empty line for separation


if __name__ == "__main__":
    # Initialize ArgumentParser
    parser = argparse.ArgumentParser(
        description=(
            "Search Reddit for a specific string in specified subreddits "
            "(excluding image URLs)."
        )
    )
    parser.add_argument("--client_id", required=True, help="Your Reddit API client ID")
    parser.add_argument(
        "--client_secret", required=True, help="Your Reddit API client secret"
    )
    parser.add_argument(
        "--user_agent", required=True, help="Your Reddit API user agent"
    )
    parser.add_argument(
        "--subreddits",
        required=True,
        help="Comma-separated list of subreddits to search in",
    )
    parser.add_argument("--query", required=True, help="The string to search for")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Number of results to return per subreddit (default: 10)",
    )

    # Parse arguments from command line
    args = parser.parse_args()

    # Call main function with parsed arguments
    main(
        args.client_id,
        args.client_secret,
        args.user_agent,
        args.subreddits,
        args.query,
        args.limit,
    )
