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

# Step 2: Scrape tweets
async def scrape_tweets():
    tweets = []
    scroll_increment = 660
    seen_tweet = set()
    conn = get_db_connection()
    cursor = conn.cursor()
    notfound_count = 0
    
    queries = [
    # 🌐 Global Affairs & Politics
    "Putin", "Biden", "Modi", "Macron", "Zelenskyy", "UN resolution", "BRICS", "G7 summit", "Israel Gaza", "Iran sanctions",
    "NATO expansion", "North Korea missile", "African coup", "geopolitical tensions", "foreign policy", "diplomatic row",

    # 🇮🇳 Indian Politics & News
    "India Parliament", "Rahul Gandhi", "Modi speech", "ED raid", "CBI case", "Lok Sabha", "Supreme Court India",
    "Manipur", "Kashmir update", "Opposition INDIA alliance", "UCC", "Election Commission", "Nitin Gadkari", "Amit Shah",

    # 📉 Economy & Business
    "inflation report", "interest rate hike", "stock market crash", "India GDP", "recession fears", "crypto ban",
    "RBI announcement", "Adani", "Ambani", "Nifty 50", "Sensex update", "SEBI", "startup funding", "layoffs",

    # 🔬 Tech & Innovation
    "AI breakthrough", "ChatGPT", "Google Gemini", "OpenAI news", "Tesla update", "Elon Musk",
    "Apple launch", "iPhone 16", "Neuralink", "SpaceX launch", "data breach", "cyber attack", "ISRO",

    # 🔥 Trending & Controversies
    "viral video", "leaked chat", "controversial statement", "protest update", "boycott trend", "fact check",
    "deepfake", "breaking news", "massive outrage", "scandal", "smear campaign",

    # 🌍 Global Events & Disasters
    "earthquake", "flood update", "wildfire", "plane crash", "terrorist attack", "nuclear threat",
    "climate crisis", "heatwave alert", "UN report", "humanitarian crisis", "tsunami warning",

    # 🧠 Geopolitics & Strategy
    "China Taiwan", "Indo-Pacific", "India Russia ties", "Quad alliance", "Pakistan border", "defense deal",
    "arms race", "nuclear submarine", "cyber war", "intelligence agency", "military drill",

    # 👥 Leaders Making News
    "Narendra Modi", "Xi Jinping", "Joe Biden", "Donald Trump", "Putin news", "Volodymyr Zelenskyy", "Rishi Sunak",
    "Netanyahu", "Imran Khan", "George Soros", "S Jaishankar", "Yogi Adityanath",

    # 🏏 Sports & High-Stakes Games (NEW)
    "India vs Pakistan", "Virat Kohli", "Rohit Sharma", "Jasprit Bumrah", "Shubman Gill",
    "IPL auction", "World Cup final", "Ashes", "Manchester United", "Real Madrid",
    "Messi", "Ronaldo", "BCCI", "Olympic scandal", "Wimbledon final"
]
    
    today = datetime.utcnow().date()
    
    
    yesterday = today - timedelta(days=1)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        context = await browser.new_context(
            storage_state=STORAGE_FILE,
            user_agent=user_agent,
            viewport={"width": 1280, "height": 800},
        )
        page = await context.new_page()
        
        table_name = "scrapped_tweets"
        
        
        for i in queries:
            keyword = i.replace(" ","%20")
            
            url = f"https://x.com/search?q={keyword}%20min_replies%3A300%20min_faves%3A500%20min_retweets%3A500%20lang%3Aen%20until%3A{today}%20since%3A{yesterday}%20-filter%3Areplies&f=live&src=typed_query"

            notfound_count = 0
            await page.goto(url)
            await page.wait_for_timeout(3000)
            
            while True:
                await page.wait_for_selector('div[data-testid="cellInnerDiv"]')
                tweet_divs = await page.query_selector_all('div[data-testid="cellInnerDiv"]')

                for tweet in tweet_divs:
                    tweet_id = await get_tweet_id_from_url(tweet)
                    
                    if tweet_id:
                        
                        
                        cursor.execute("SELECT id FROM scrapped_tweets WHERE id = %s", (tweet_id,))
                        result = cursor.fetchone()
                        
                        if result:
                            # print(f"  -> Skipping duplicate tweet ID: {tweet_id}")
                            continue
                        
                        tweet_text_div = await tweet.query_selector('div[data-testid="tweetText"]')
                        
                        if tweet_text_div:
                            show_more = await tweet.query_selector('button[data-testid="tweet-text-show-more-link"]')
                            if  show_more:
                                try:
                                    await show_more.click()
                                    await asyncio.sleep(0.3)  # Allow time for tweet to expand
                                except Exception as e:
                                    print(f"⚠️ Error clicking 'Show more': {e}")
                            
                            tweet_text = await tweet_text_div.inner_text()
                            
                            tweet_text = tweet_text.strip()

                            if tweet_text not in seen_tweet:
                                notfound_count = 0
                                seen_tweet.add(tweet_text)
                                
                                processed_tweet = clean_tweet(tweet_text)
                                cursor.execute(f"insert into `{table_name}` (id,tweet) values(%s,%s)",(tweet_id, processed_tweet))
                                
                                # Optional: Keep seen_tweet from growing too big
                                if len(seen_tweet) > 60:
                                    seen_tweet.pop()
                        
                        else:
                            print("not found")
                            notfound_count += 1
                        if notfound_count > 30:
                                break
                                
                        conn.commit()     
                    
                if notfound_count > 30:
                            break
                last_height = await page.evaluate("document.body.scrollHeight")
                await page.evaluate(f"window.scrollBy(0, {scroll_increment});")
                await page.wait_for_timeout(4000)
                new_height = await page.evaluate("document.body.scrollHeight")

# If the height hasn't changed, we've reached the bottom.
                if new_height == last_height:
                    print(f"Reached the end of the results for '{i}'. Moving to the next keyword.")
                    break
                
        conn.close()
        await browser.close()

    


# Run the scraper
if __name__ == "__main__":
    if not Path(STORAGE_FILE).exists():
        asyncio.run(save_login_state())
    asyncio.run(scrape_tweets())
