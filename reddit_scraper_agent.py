import os
import praw
import argparse
import concurrent.futures
import time
from functools import partial
from database_manager import get_supabase_client
from dotenv import load_dotenv

load_dotenv()

def get_reddit_client():
    """Initializes and returns the PRAW Reddit client."""
    client_id = os.environ.get("REDDIT_CLIENT_ID")
    client_secret = os.environ.get("REDDIT_CLIENT_SECRET")
    user_agent = os.environ.get("REDDIT_USER_AGENT")
    if not all([client_id, client_secret, user_agent]):
        raise ValueError("Reddit API credentials must be set in environment variables.")
    
    return praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )

def scrape_subreddit(subreddit_name: str, reddit_client: praw.Reddit, limit: int = 10, comments_limit: int = 20):
    """
    Scrapes a single subreddit for new posts and their top comments.
    
    Args:
        subreddit_name: The name of the subreddit to scrape.
        reddit_client: The PRAW Reddit instance.
        limit: The number of new posts to fetch.
        comments_limit: The number of top comments to fetch per post.
        
    Returns:
        A list of dictionaries, where each dictionary is a lead.
    """
    subreddit = reddit_client.subreddit(subreddit_name)
    leads = []
    print(f"Scraping subreddit: r/{subreddit_name}")
    
    try:
        for submission in subreddit.new(limit=limit):
            # Add the post itself as a lead with enhanced metadata
            leads.append({
                "reddit_id": submission.id,
                "permalink": submission.permalink,
                "subreddit": subreddit_name,
                "title": submission.title,
                "body_text": submission.selftext,
                "is_comment": False,
                "author": str(submission.author) if submission.author else "[deleted]",
                "score": submission.score,
                "num_comments": submission.num_comments,
                "created_utc": int(submission.created_utc),
                "url": submission.url
            })
            
            # Add top-level comments as leads with enhanced metadata
            submission.comments.replace_more(limit=0) # Remove "load more comments"
            for comment in submission.comments.list()[:comments_limit]:
                leads.append({
                    "reddit_id": comment.id,
                    "permalink": comment.permalink,
                    "subreddit": subreddit_name,
                    "title": f"Comment on: {submission.title}",
                    "body_text": comment.body,
                    "is_comment": True,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "score": comment.score,
                    "num_comments": 0,  # Comments don't have sub-comments count
                    "created_utc": int(comment.created_utc),
                    "url": f"https://reddit.com{comment.permalink}"
                })
        print(f"Found {len(leads)} potential leads from r/{subreddit_name}.")
    except Exception as e:
        print(f"Could not scrape r/{subreddit_name}. Reason: {e}")

    return leads

def store_leads(supabase, leads: list):
    """Stores a list of leads into the Supabase 'raw_leads' table."""
    if not leads:
        print("No new leads to store.")
        return

    # Add session ID to all leads in this batch
    session_id = f"scrape_{int(time.time())}"
    for lead in leads:
        lead['session_id'] = session_id
        # Remove scraped_at since the table has a default value of now()

    print(f"Storing {len(leads)} leads in Supabase with session_id: {session_id}...")
    try:
        data, count = supabase.table('raw_leads').upsert(leads, on_conflict='reddit_id').execute()
        print(f"Successfully stored/updated {len(data[1])} leads.")
        print(f"Session ID for this batch: {session_id}")
        return session_id  # Return session_id for the orchestrator to use
    except Exception as e:
        print(f"Error storing leads in Supabase: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Scrape multiple Reddit subreddits in parallel for SaaS ideas.")
    parser.add_argument(
        "subreddits", 
        nargs='+', 
        help="One or more subreddit names to scrape (e.g., 'SaaS' 'startups')."
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        default=50, 
        help="Number of new posts to fetch from each subreddit."
    )
    parser.add_argument(
        "--comments", 
        type=int, 
        default=20, 
        help="Number of top comments to fetch from each post."
    )
    args = parser.parse_args()

    try:
        reddit = get_reddit_client()
        supabase = get_supabase_client()
        all_leads = []

        # Create a partial function with the reddit client and limit arguments pre-filled
        scrape_with_args = partial(scrape_subreddit, reddit_client=reddit, limit=args.limit, comments_limit=args.comments)

        # Use a ThreadPoolExecutor to scrape subreddits in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # map the scraping function to the list of subreddits
            results = executor.map(scrape_with_args, args.subreddits)
            
            # Collect all leads from the parallel scrapes
            for lead_list in results:
                all_leads.extend(lead_list)

        session_id = store_leads(supabase, all_leads)
        
        # Write session_id to a file for the orchestrator to use
        if session_id:
            with open('.current_session_id', 'w') as f:
                f.write(session_id)
            print(f"✅ Scraping complete! Session ID saved to .current_session_id")
            print(f"💡 Run the orchestrator next to process these {len(all_leads)} leads")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during parallel scraping: {e}")


if __name__ == "__main__":
    main() 