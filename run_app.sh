#!/bin/bash

# PicoPitch - Session-Isolated Workflow
# This script demonstrates the proper way to run the full pipeline

echo "🚀 PicoPitch - Session-Isolated SaaS Idea Pipeline"
echo "=================================================="

# --- Virtual Environment Setup ---
if [ -d "venv" ]; then
    echo "🔧 Activating virtual environment..."
    source venv/bin/activate
    echo "✅ Virtual environment activated"
else
    echo "⚠️  Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""

# --- Configuration ---
# Default subreddits to scrape (space-separated)
DEFAULT_SUBREDDITS=("mentalhealth" "MentalHealthSupport" "mentalillness")
DEFAULT_POST_LIMIT=50       # Number of posts to scrape from EACH subreddit
DEFAULT_COMMENT_LIMIT=100     # Number of top comments to fetch from EACH post

# Check if subreddits were provided as arguments
if [ $# -eq 0 ]; then
    echo "ℹ️  No subreddits specified, using defaults:"
    echo "🎯 Default subreddits: ${DEFAULT_SUBREDDITS[*]}"
    echo "📊 Posts per subreddit: $DEFAULT_POST_LIMIT"
    echo "💬 Comments per post: $DEFAULT_COMMENT_LIMIT"
    echo ""
    read -p "🤔 Use these defaults? (Y/n): " -n 1 -r
    echo    # Move to a new line
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo ""
        echo "💡 Usage: $0 <subreddit1> <subreddit2> ... [--limit POSTS] [--comments COMMENTS]"
        echo "📋 Example: $0 SaaS startups Entrepreneur --limit 30 --comments 15"
        echo "📋 Example: $0 adhd productivity --limit 50"
        exit 0
    fi
    
    # Use defaults
    SCRAPER_ARGS=("${DEFAULT_SUBREDDITS[@]}" "--limit" "$DEFAULT_POST_LIMIT" "--comments" "$DEFAULT_COMMENT_LIMIT")
    echo ""
    echo "📡 Step 1: Scraping Reddit communities for pain points..."
    echo "🎯 Target subreddits: ${DEFAULT_SUBREDDITS[*]}"
else
    # Use provided arguments
    SCRAPER_ARGS=("$@")
    echo "📡 Step 1: Scraping Reddit communities for pain points..."
    echo "🎯 Target arguments: $@"
fi

# Run the Reddit scraper with arguments
python3 reddit_scraper_agent.py "${SCRAPER_ARGS[@]}"

# Check if scraping was successful by looking for session file
if [ ! -f ".current_session_id" ]; then
    echo "❌ Reddit scraping failed or no session file created"
    exit 1
fi

# Read the session ID for display
SESSION_ID=$(cat .current_session_id)
echo ""
echo "✅ Reddit scraping completed successfully!"
echo "📋 Session ID: $SESSION_ID"
echo ""

# Ask user if they want to continue
read -p "🤔 Do you want to proceed with analyzing these leads? (y/N): " -n 1 -r
echo    # Move to a new line
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "⏸️  Stopping here. You can run the orchestrator later with: python3 orchestrator.py"
    exit 0
fi

echo ""
echo "🧠 Step 2: Running AI analysis and document generation..."
echo "⚡ This will process ONLY the leads from session: $SESSION_ID"

# Run the orchestrator
python3 orchestrator.py

echo ""
echo "🎉 PicoPitch pipeline completed!"
echo "📁 Check the 'picopitch_outputs' folder for generated documents"

# Show usage examples for next time
echo ""
echo "💡 Next time you can also run with custom settings:"
echo "   $0 adhd productivity mentalhealth --limit 50 --comments 30"
echo "   $0 restaurant hospitality --limit 20"
echo "   $0  # (uses defaults again)" 