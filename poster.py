import asyncio
import pymysql
from playwright.async_api import async_playwright
from pathlib import Path

STORAGE_FILE_1 = r"C:\Users\Divyanshi\Downloads\tweeet_poster\twitter_poster.json"

async def save_login_1_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔐 Please log into Twitter manually in the browser window.")
        await page.goto("https://twitter.com/login")
        await page.wait_for_timeout(60000)  # 60 seconds to log in manually

        await context.storage_state(path=STORAGE_FILE_1)
        print(f"✅ Login session saved to {STORAGE_FILE_1}")
        await browser.close()
        

# (Your database functions remain the same)
def get_db_connection():
    return pymysql.connect(
        host="localhost", user="root", password="Divyanshi@1",
        database="twitter", cursorclass=pymysql.cursors.DictCursor, autocommit=True
    )

def get_unposted_tweets(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT id, post FROM scrapped_tweets WHERE posted = FALSE AND post IS NOT NULL")
        return cursor.fetchone()

def mark_as_posted(conn, tweet_id):
    with conn.cursor() as cursor:
        cursor.execute("UPDATE scrapped_tweets SET posted = TRUE WHERE id = %s", (tweet_id,))
    print(f"✔️ Marked tweet ID {tweet_id} as posted in the database.")

# === Post Tweets on Twitter (Final, Robust Version) ===
async def post_tweets():
    conn = get_db_connection()
    tweets_to_post = get_unposted_tweets(conn)
    
    if not tweets_to_post:
        
        conn.close()
        return

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Set to True for production
        context = await browser.new_context(storage_state=STORAGE_FILE_1)
        page = await context.new_page()
        
        await page.goto("https://x.com/home")

        tweet = tweets_to_post
        tweet_id = tweet["id"]
        tweet_text = tweet["post"]
        

        try:
            # Step 1: Find and fill the text box
            tweet_box_selector = 'div[data-testid="tweetTextarea_0"]'
            await page.wait_for_selector(tweet_box_selector, timeout=30000)
            await page.locator(tweet_box_selector).fill(tweet_text)
            await asyncio.sleep(1) # Brief pause after typing

            # Step 2: Locate the post button
            post_button_selector = 'button[data-testid="tweetButtonInline"]'
            post_button = page.locator(post_button_selector)
            
            # Step 3: **THE FIX** - Use a direct JavaScript click
            # This is the most reliable method to bypass overlays.
            
            await post_button.evaluate("button => button.click()")
            

            # Step 4: Wait for the confirmation "toast" message to verify success
            await page.wait_for_selector('div[data-testid="toast"]', state="visible", timeout=15000)
            print(f"✅ Post confirmed successfully.")

            # Step 5: Mark as posted in the database
            mark_as_posted(conn, tweet_id)
            
            await asyncio.sleep(10)

        except Exception as e:
            print(f"❌ Failed to post tweet ID {tweet_id}: {e}")
            
        
        await browser.close()
    conn.close()
    
    

# === Run it ===
if __name__ == "__main__":
    if not Path(STORAGE_FILE_1).exists():
        asyncio.run(save_login_1_state())
    asyncio.run(post_tweets())