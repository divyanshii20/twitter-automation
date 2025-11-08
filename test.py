import asyncio
import csv
from pathlib import Path
from playwright.async_api import async_playwright
import re
import pymysql
from datetime import datetime, timedelta

STORAGE_FILE = r"C:\Users\Divyanshi\Downloads\tweeet_poster\twitter_login.json"


def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="Divyanshi@1",
        database="twitter",
        cursorclass=pymysql.cursors.DictCursor
    )
    
# Step 1: Save cookies after manual login
async def save_login_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔐 Please log into Twitter manually in the browser window.")
        await page.goto("https://twitter.com/login")
        await page.wait_for_timeout(60000)  # 60 seconds to log in manually

        await context.storage_state(path=STORAGE_FILE)
        print(f"✅ Login session saved to {STORAGE_FILE}")
        await browser.close()
        



def clean_tweet(tweet: str) -> str:
    tweet = tweet.strip()

    # Case-insensitive removal of "📝 BREAKING:" or "BREAKING:"
    tweet = re.sub(r"^📝\s*breaking:\s*", "", tweet, flags=re.IGNORECASE)
    tweet = re.sub(r"^breaking:\s*", "", tweet, flags=re.IGNORECASE)

    # Replace line breaks, tabs, etc. with space
    tweet = tweet.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')

    # Collapse multiple spaces into a single space
    tweet = ' '.join(tweet.split())

    return tweet

async def get_tweet_id_from_url(tweet_element):
    """
    Finds a link within a tweet element and extracts the ID from its URL.
    This is the most reliable way to get a unique identifier.
    """
    try:
        # The permalink is usually on a link containing the timestamp.
        # We look for any link containing '/status/' in its href attribute.
        link_element = await tweet_element.query_selector('a[href*="/status/"]')
        if link_element:
            url = await link_element.get_attribute('href')
            # The URL looks like: /username/status/1812041282293923840
            # We split the string by '/status/' and take the last part.
            tweet_id = url.split('/status/')[-1]
            return tweet_id
    except Exception as e:
        print(f"⚠️ Could not extract tweet ID from URL: {e}")
    return None

# === REFINED SCRAPING FUNCTION ===
# === REFINED SCRAPING FUNCTION (with patient scrolling) ===
async def scrape_tweets():
    print("--- Starting Tweet Scraping Process ---")
    conn = get_db_connection()
    
    queries = [
        # ... your keyword list ...
        "Putin", "Biden", "Modi", "India Parliament", "inflation report", "AI breakthrough",
        "viral video", "earthquake", "China Taiwan", "Narendra Modi", "India vs Pakistan"
    ]
    
    today = datetime.utcnow().date()
    yesterday = today - timedelta(days=1)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False) # Use headless=True for automation
        context = await browser.new_context(storage_state=STORAGE_FILE)
        page = await context.new_page()
        
        for keyword in queries:
            print("\n" + "="*50)
            print(f"🔎 Scraping for keyword: '{keyword}'")
            
            search_url = f"https://x.com/search?q={keyword.replace(' ', '%20')}%20min_faves%3A100%20lang%3Aen%20until%3A{today}%20since%3A{yesterday}%20-filter%3Areplies&f=live"
            
            await page.goto(search_url)
            await page.wait_for_timeout(3000)

            # --- **REFINED SCROLLING LOGIC** ---
            # This loop will scroll down slowly and patiently.
            
            # Use a set to track tweet IDs seen in this session to avoid reprocessing
            # already visible tweets in the same scroll session.
            seen_in_session = set() 
            
            for _ in range(10): # Scroll up to 5 times per keyword
                # Process all currently visible tweets
                tweet_divs = await page.query_selector_all('div[data-testid="cellInnerDiv"]')
                
                for tweet_element in tweet_divs:
                    tweet_id = await get_tweet_id_from_url(tweet_element)
                    
                    if tweet_id and tweet_id not in seen_in_session:
                        seen_in_session.add(tweet_id) # Add to session tracker

                        with conn.cursor() as cursor:
                            cursor.execute("SELECT id FROM scrapped_tweets WHERE id = %s", (tweet_id,))
                            result = cursor.fetchone()
                        
                        if result:
                            continue # Skip if already in the database
                        
                        tweet_text_div = await tweet_element.query_selector('div[data-testid="tweetText"]')
                        if tweet_text_div:
                            tweet_text = await tweet_text_div.inner_text()
                            processed_tweet = clean_tweet(tweet_text)
                            
                            with conn.cursor() as cursor:
                                cursor.execute("INSERT INTO scrapped_tweets (id, tweet) VALUES (%s, %s)", (tweet_id, processed_tweet))
                            print(f"  ✅ Saved new tweet -> ID: {tweet_id}")
                
                conn.commit()

                # **Slow scroll to the bottom to give the page time to load new content**
                print("  -> Scrolling down to load more tweets...")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                # **Crucial: Wait longer after scrolling**
                await page.wait_for_timeout(4000) 
            
            print(f"Finished scrolling for '{keyword}'. Moving to the next keyword.")
            
    conn.close()
    await browser.close()
    print("\n" + "="*50)
    print("--- Scraping Process Finished ---")
    
if __name__ == "__main__":
    if not Path(STORAGE_FILE).exists():
        asyncio.run(save_login_state())
    asyncio.run(scrape_tweets())


# (The rest of your script, including the main execution block, remains the same)