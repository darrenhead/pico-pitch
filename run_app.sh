#!/bin/bash

# This script automates the process of scraping Reddit and running the PicoPitch orchestrator.
# It now accepts a --skip-scraper flag to bypass the scraping step.

# --- Configuration ---
# Add as many subreddits as you want to scrape here, separated by spaces
SUBREDDITS_TO_SCRAPE=("SideProject" "startups")
POST_LIMIT=50 # Number of posts to scrape from EACH subreddit
COMMENT_LIMIT=30 # Number of top comments to fetch from EACH post

# --- Script ---

echo "--- Activating Virtual Environment ---"
source venv/bin/activate

if [[ "$1" != "--skip-scraper" ]]; then
    echo ""
    echo "--- Step 1: Scraping Multiple Subreddits for new leads (Posts: $POST_LIMIT, Comments: $COMMENT_LIMIT per post) ---"
    python3 reddit_scraper_agent.py "${SUBREDDITS_TO_SCRAPE[@]}" --limit "$POST_LIMIT" --comments "$COMMENT_LIMIT"
else
    echo "--- SKIPPING SCRAPER ---"
fi

echo ""
echo "--- Step 2: Starting the Main Orchestrator ---"
echo "The orchestrator will now process all leads, find themes across all scraped content, and validate opportunities."
echo "This may take several minutes depending on the number of leads and API response times."
python3 orchestrator.py

echo ""
echo "--- Run Complete ---"
echo "Check the 'picopitch_outputs' directory for any generated Markdown documents for validated opportunities."

# Deactivate the virtual environment (optional)
# deactivate 