import tweepy
from datetime import datetime, timedelta

# Twitter API credentials
consumer_key = ""
consumer_secret = ""
access_token = ""
access_token_secret = ""

# Number of days to check for recent tweets
days_to_check = 7

# Authenticate to Twitter
auth = tweepy.OAuth1UserHandler(consumer_key, consumer_secret, access_token, access_token_secret)
api = tweepy.API(auth)

def check_recent_tweets(username):
    try:
        # Get user's timeline
        tweets = api.user_timeline(screen_name=username, count=1)

        if len(tweets) == 0:
            return False
        else:
            # Get the timestamp of the last tweet
            last_tweet_date = tweets[0].created_at

            # Check if the last tweet was posted within the last 'days_to_check' days
            if datetime.now() - last_tweet_date < timedelta(days=days_to_check):
                return True
            else:
                return False
    except Exception as e:
        print(f"Error fetching tweets for {username}: {e}")
        return False

def main():
    try:
        # Get the list of users you follow
        following = api.get_friend_ids()

        for user_id in following:
            user = api.get_user(user_id)
            username = user.screen_name

            # Check if the user has posted something in the last 'days_to_check' days
            if check_recent_tweets(username):
                print(f"{username} has posted something in the last {days_to_check} days.")
            else:
                print(f"{username} has not posted anything in the last {days_to_check} days.")
    except Exception as e:
        print(f"Error fetching following list: {e}")

if __name__ == "__main__":
    main()
