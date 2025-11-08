# scheduler.py

import asyncio
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import logging
import sys

# Import the main functions from your other scripts
from main import main_pipeline
from poster import post_tweets 

# --- Configure Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    handlers=[
        logging.FileHandler("scheduler_run_log.log"), # Saves logs to a file
        logging.StreamHandler(sys.stdout)
    ]
)

# --- Define Job Wrappers ---
def run_main_pipeline_job():
    """Wrapper to run the async main_pipeline function."""
    logging.info("--- SCHEDULER: Starting the main pipeline job ---")
    try:
        asyncio.run(main_pipeline())
        logging.info("--- SCHEDULER: Main pipeline job finished successfully ---")
    except Exception as e:
        logging.error(f"--- SCHEDULER: An error occurred in the main pipeline: {e} ---")

def run_poster_job():
    """Wrapper to run the async post_one_tweet function."""
    logging.info("--- SCHEDULER: Starting the poster job ---")
    try:
        asyncio.run(post_tweets())
        logging.info("--- SCHEDULER: Poster job finished successfully ---")
    except Exception as e:
        logging.error(f"--- SCHEDULER: An error occurred in the poster job: {e} ---")

# --- Main Scheduler Logic ---
if __name__ == "__main__":
    scheduler = BlockingScheduler()

    scheduler.add_job(run_main_pipeline_job, 'interval', hours=5, id='main_pipeline_job')
    logging.info("✅ Main pipeline scheduled to run every 5 hours.")

    scheduler.add_job(run_poster_job, 'interval', hours=1, id='poster_job')
    logging.info("✅ Poster script scheduled to run every 30 minutes.")

    # Run the main pipeline once immediately on startup
    print("\n--- Running initial main pipeline on startup... ---")
    run_main_pipeline_job()
    print("--- Initial run complete. Scheduler is now active. ---")

    print("\nScheduler is running...")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logging.info("Scheduler stopped.")