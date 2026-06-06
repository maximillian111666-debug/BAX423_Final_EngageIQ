"""
Reddit API scraper stub (PRAW).
Credentials in .env: REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT.
Not used in the offline dataset; available for live refresh expansion.
"""
import os


def is_configured() -> bool:
    return bool(os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET"))


def scrape_subreddits(subreddits: list[str], limit: int = 100) -> list[dict]:
    """Fetch hot posts from specified subreddits. Requires REDDIT_CLIENT_ID/SECRET in env."""
    if not is_configured():
        return []
    try:
        import praw
        reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_CLIENT_SECRET"],
            user_agent=os.environ.get("REDDIT_USER_AGENT", "EngageIQ/1.0"),
        )
        results = []
        for sub in subreddits:
            for post in reddit.subreddit(sub).hot(limit=limit):
                results.append({
                    "external_id": f"reddit_{post.id}",
                    "source": "reddit",
                    "title": post.title,
                    "body": post.selftext[:500] if post.selftext else "",
                    "url": f"https://reddit.com{post.permalink}",
                    "stars": post.score,
                    "forks": 0,
                    "comments": post.num_comments,
                    "tags": [],
                    "is_gfi": False,
                })
        return results
    except Exception:
        return []
