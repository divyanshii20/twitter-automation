🧠 Twitter Automation Bot using Python & Playwright

An intelligent automation system that scrapes, stores, and posts tweets automatically — perfect for creators, curators, and news accounts like Xposed Daily.

🌟 Overview

The Twitter Automation Bot is a fully automated Python-based solution designed to manage and post tweets seamlessly using Playwright.
It connects to a MySQL database, picks unposted tweets, and posts them on X (Twitter) using a saved browser session — without manual login or human supervision.

Ideal for:

Automated news posting accounts

Daily tweet threads

Content curation bots

🚀 Features

✅ Automatic Tweet Posting
Posts tweets directly on X using a saved, secure login session.

🧠 Smart Database Control
Fetches only unposted tweets and marks them as posted after successful upload.

🕒 Task Scheduling Support
Integrates easily with Windows Task Scheduler or cron jobs for automatic daily runs.

🔐 Secure Login State
Stores Twitter session data in twitter_poster.json for login-free automation.

⚙️ Lightweight & Modular Design
Includes separate .bat scripts for modular control — post, clear, or schedule easily.

🧩 Tech Stack
Component	Technology
Language	Python 3.10+
Automation Engine	Playwright (async)
Database	MySQL (via PyMySQL)
Scheduler	Windows Task Scheduler / Cron
Scripts	.bat automation for easy execution
