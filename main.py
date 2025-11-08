import asyncio
from pathlib import Path
import pymysql
import re

from scrapper import save_login_state, scrape_tweets
from model import score_tweet
from tweet_writer import rewritter 

def get_db_connection():
    """Establishes and returns a new database connection."""
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Divyanshi@1",
        database="twitter",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def clean_post(raw_text: str) -> str:
    """A helper function to clean the final rewritten post."""
    # This pattern looks for any text enclosed in **[...]** and removes it
    cleaned = re.sub(r'\*\*\[.*?\]:\*\*', '', raw_text).strip()
    # This removes common conversational prefixes
    prefixes_to_remove = ["Here is the rewritten tweet:", "The Watcher's Tweet:"]
    for prefix in prefixes_to_remove:
        if cleaned.lower().startswith(prefix.lower()):
            cleaned = cleaned[len(prefix):].strip()
    return cleaned

async def main_pipeline():
    
    conn = get_db_connection()

    # --- Step 1: Scrape new tweets ---
    await scrape_tweets()
    
    # --- Step 2: Score new tweets and filter ---
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, tweet FROM scrapped_tweets WHERE tweet_score IS NULL")
        tweets_to_score = cursor.fetchall()
        
        for tweet in tweets_to_score:
            score = score_tweet(tweet['tweet'])
            cursor.execute("UPDATE scrapped_tweets SET tweet_score = %s WHERE id = %s", (score, tweet['id']))
        
        # Delete low-scoring tweets
        cursor.execute("DELETE FROM scrapped_tweets WHERE tweet_score < 8")
    
    # --- Step 3: Rewrite high-scoring tweets ---
    
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, tweet FROM scrapped_tweets WHERE tweet_score >= 7 AND post IS NULL")
        tweets_to_rewrite = cursor.fetchall()
        
        for tweet in tweets_to_rewrite:
            rewritten_post_raw = rewritter(tweet['tweet'])
            if rewritten_post_raw:
                final_post = clean_post(rewritten_post_raw)
                cursor.execute("UPDATE scrapped_tweets SET post = %s WHERE id = %s", (final_post, tweet['id']))
                
            else:
                print(f"  -> Failed to rewrite tweet ID {tweet['id']}. Skipping.")
    
    conn.close()

if __name__ == "__main__":
    
    STORAGE_FILE = r"C:\Users\Divyanshi\Downloads\tweeet_poster\twitter_login.json"
    if not Path(STORAGE_FILE).exists():
        asyncio.run(save_login_state())
        
    asyncio.run(main_pipeline())