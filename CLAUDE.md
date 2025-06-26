# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PicoPitch is an agentic workflow system that discovers SaaS opportunities from Reddit discussions and generates AI-ready product documentation. It uses a multi-agent architecture with specialized Python agents coordinated through an orchestrator.

## Common Development Commands

### Virtual Environment and Dependencies
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install new package (remember to update requirements.txt)
pip install <package>
pip freeze > requirements.txt
```

### Running the System
```bash
# Full pipeline (scrape + analyze)
./run_app.sh

# Skip scraping, analyze existing data
./run_app.sh --skip-scraper

# Custom subreddits with limits
python3 reddit_scraper_agent.py startups SideProject --limit 50 --comments 30

# Run orchestrator independently
python3 orchestrator.py

# Test individual modules
python3 database_manager.py  # Tests Supabase connection
```

### Testing and Debugging
```bash
# No formal test suite exists - test modules individually
python3 -m <module_name>

# Check environment variables
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.getenv('SUPABASE_URL'))"

# Debug Gemini API issues
# Set enhanced logging in gemini_interaction_agent.py
```

## High-Level Architecture

### Multi-Agent System Design

The system implements a pipeline of specialized agents:

1. **Reddit Scraper Agent** (`reddit_scraper_agent.py`)
   - Collects posts/comments from specified subreddits
   - Creates session IDs for processing isolation
   - Stores raw leads in Supabase

2. **Gemini Interaction Agent** (`gemini_interaction_agent.py`)
   - Core AI module handling all Gemini API operations
   - Problem extraction with evidence capture
   - Theme consolidation across domains
   - Opportunity validation and scoring
   - Document generation (BRD, PRD, Agile plans)
   - Implements retry logic with exponential backoff

3. **Orchestrator Agent** (`orchestrator.py`)
   - Coordinates the 6-stage processing pipeline
   - Manages parallel execution with ThreadPoolExecutor
   - Handles session-based filtering
   - Tracks processing state through status fields

4. **Database Manager** (`database_manager.py`)
   - Supabase client initialization
   - Shared state management between agents

5. **File Exporter** (`file_exporter.py`)
   - Saves generated documents to organized folder structure
   - Handles filename sanitization

### Processing Pipeline Stages

1. **Lead Processing**: Extract problems from Reddit posts (parallel)
2. **Domain Grouping**: Group by problem domains
3. **Theme Consolidation**: Merge similar domains (batch processing)
4. **Opportunity Creation**: Generate business opportunities (parallel)
5. **Validation**: Score opportunities on monetization/feasibility (parallel)
6. **Document Generation**: Create BRD/PRD/Agile plans (parallel)

### Key Architectural Patterns

- **Session Isolation**: Each scraping run gets a unique session ID
- **Status-Based Processing**: Database status fields track pipeline state
- **Dual Model Strategy**: Gemini Flash for volume, Pro for quality
- **Evidence Preservation**: Enhanced extraction captures user quotes
- **Parallel Processing**: ThreadPoolExecutor for concurrent operations
- **Retry Mechanisms**: Exponential backoff for API rate limits

### Database Schema

- `raw_leads`: Reddit posts/comments with AI analysis
- `opportunities`: Validated business opportunities
- `solution_concepts`: Product concepts per opportunity
- `documents`: Generated BRDs, PRDs, Agile plans

### Configuration Points

In `orchestrator.py`:
```python
FLASH_MODEL_NAME = "gemini-2.5-flash-preview-05-20"
PRO_MODEL_NAME = "gemini-2.5-pro-preview-06-05"
MIN_LEADS_FOR_THEME = 3
USE_ENHANCED_EXTRACTION = True
DEFAULT_THEME_BATCH_SIZE = 50
```

In `run_app.sh`:
```bash
DEFAULT_SUBREDDITS=("ProductManagement" "ProductManager" "ProductHunters")
DEFAULT_POST_LIMIT=25
DEFAULT_COMMENT_LIMIT=20
```

### Environment Variables

Required in `.env`:
```
GEMINI_API_KEY=
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
SUPABASE_URL=
SUPABASE_KEY=  # Use service role key, not anon key
```

### Common Issues and Solutions

1. **Rate Limiting**: Built-in retry logic handles this automatically
2. **Session Not Found**: Check `.current_session_id` file exists
3. **Database Errors**: Verify service role key has proper permissions
4. **No Opportunities Generated**: Lower MIN_LEADS_FOR_THEME threshold
5. **JSON Parsing Errors**: Robust cleaning in place, check Gemini response format

### Output Structure

```
picopitch_outputs/
├── {id}_{opportunity_title}/
│   ├── BRD_v1.md           # Business Requirements
│   ├── PRD_v1.md           # Product Requirements
│   └── AGILE_PLAN_v1.md    # Development plan
```

Each document includes:
- Evidence-based market validation
- User quotes with Reddit links
- Financial impact analysis
- Technical specifications
- 1-point Agile task breakdown