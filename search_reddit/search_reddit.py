import praw
import argparse
import prawcore
import re

def search_in_subreddits(reddit, subreddits, query, limit=10):
    """
    Search for a specific string in a list of subreddits.

    :param reddit: Initialized Reddit instance.
    :param subreddits: List of subreddit names to search in.
    :param query: The string to search for.
    :param limit: Number of results to return per subreddit.
    :return: Dictionary with subreddit names as keys and list of results as values.
    """
    results = {}
    for subreddit in subreddits:
        results[subreddit] = []
        for submission in reddit.subreddit(subreddit).search(query, sort='new', limit=limit):
            # Filter out submissions that do not contain the exact simport praw
import prawcore
import argparse

def search_in_subreddits(reddit, subreddits, query, limit=10):
    """
    Search for a specific string in a list of subreddits, sorted by newest.

    :param reddit: Initialized Reddit instance.
    :param subreddits: List of subreddit names to search in.
    :param query: The string to search for.
    :param limit: Number of results to return per subreddit.
    :return: Dictionary with subreddit names as keys and list of results as values.
    """
    results = {}
    for subreddit in subreddits:
        try:
            subreddit_instance = reddit.subreddit(subreddit)
            results[subreddit] = []
            for submission in subreddit_instance.search(query, sort='new', limit=limit):
                results[subreddit].append({
                    'title': submission.title,
                    'url': submission.url,
                    'score': submission.score,
                    'created_utc': submission.created_utc,
                    'num_comments': submission.num_comments
                })
        except prawcore.exceptions.NotFound:
            print(f"Subreddit '{subreddit}' not found.")
        except prawcore.exceptions.Forbidden:
            print(f"Subreddit '{subreddit}' is private.")
        except Exception as e:
            print(f"An error occurred while searching subreddit '{subreddit}': {e}")
    return results

def main(client_id, client_secret, user_agent, subreddits, query, limit):
    # Initialize the Reddit client
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    # Convert the comma-separated subreddits string to a list
    subreddit_list = subreddits.split(',')

    # Perform the search
    results = search_in_subreddits(reddit, subreddit_list, query, limit)

    # Print the results
    for subreddit, posts in results.items():
        print(f"Subreddit: {subreddit}")
        for post in posts:
            print(f"  Title: {post['title']}")
            print(f"  URL: {post['url']}")
            print(f"  Score: {post['score']}")
            print(f"  Created UTC: {post['created_utc']}")
            print(f"  Number of Comments: {post['num_comments']}")
            print('  ' + '-' * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search Reddit for a specific string in specified subreddits.")
    parser.add_argument('--client_id', required=True, help='Your Reddit API client ID')
    parser.add_argument('--client_secret', required=True, help='Your Reddit API client secret')
    parser.add_argument('--user_agent', required=True, help='Your Reddit API user agent')
    parser.add_argument('--subreddits', required=True, help='Comma-separated list of subreddits to search in')
    parser.add_argument('--query', required=True, help='The string to search for')
    parser.add_argument('--limit', type=int, default=10, help='Number of results to return per subreddit (default: 10)')

    args = parser.parse_args()

    main(args.client_id, args.client_secret, args.user_agent, args.subreddits, args.query, args.limit)

                    'score': submission.score,
                    'created_utc': submission.created_utc,
                    'num_comments': submission.num_comments
                })
            # Check comments for exact match
            submission.comments.replace_more(limit=None)
            for comment in submission.comments.list():
                if query in comment.body:
                    results[subreddit].append({
                        'title': submission.title,
                        'url': submission.url,
                        'score': submission.score,
                        'created_utc': comment.created_utc,
                        'num_comments': comment.num_comments,
                        'comment': comment.body
                    })
    return results

def main(client_id, client_secret, user_agent, subreddits, query, limit):
    # Initialize the Reddit client
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )

    # Convert the comma-separated subreddits string to a list
    subreddit_list = subreddits.split(',')

    # Perform the search
    results = search_in_subreddits(reddit, subreddit_list, query, limit)

    # Print the results
    for subreddit, posts in results.items():
        print(f"Subreddit: {subreddit}")
        for post in posts:
            print(f"  Title: {post['title']}")
            print(f"  URL: {post['url']}")
            print(f"  Score: {post['score']}")
            print(f"  Created UTC: {post['created_utc']}")
            print(f"  Number of Comments: {post['num_comments']}")
            if 'comment' in post:
                print(f"  Comment: {post['comment']}")
            print('  ' + '-' * 40)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search Reddit for a specific string in specified subreddits.")
    parser.add_argument('--client_id', required=True, help='Your Reddit API client ID')
    parser.add_argument('--client_secret', required=True, help='Your Reddit API client secret')
    parser.add_argument('--user_agent', required=True, help='Your Reddit API user agent')
    parser.add_argument('--subreddits', required=True, help='Comma-separated list of subreddits to search in')
    parser.add_argument('--query', required=True, help='The string to search for')
    parser.add_argument('--limit', type=int, default=10, help='Number of results to return per subreddit (default: 10)')

    args = parser.parse_args()

    main(args.client_id, args.client_secret, args.user_agent, args.subreddits, args.query, args.limit)
