# PicoPitch

> Transform Reddit pain points into validated SaaS opportunities with AI-ready development plans

PicoPitch is an autonomous multi-agent system that discovers real user problems from Reddit communities, validates them as business opportunities, and generates AI-optimized documentation (BRD, PRD, Agile plans) ready for implementation in Cursor IDE.

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- API Keys: [Gemini](https://makersuite.google.com/app/apikey), [Reddit](https://www.reddit.com/prefs/apps), [Supabase](https://supabase.com)

### Installation

```bash
# Clone repository
git clone https://github.com/darrenhead/pico-pitch.git
cd pico-pitch

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys
```

### Database Setup

1. Create a [Supabase](https://supabase.com) project (free tier works)
2. In Supabase SQL Editor, run:
   ```sql
   -- Copy and paste contents from database/schema.sql
   ```
   Or directly run:
   ```bash
   psql $SUPABASE_CONNECTION_STRING < database/schema.sql
   ```

### Run PicoPitch

```bash
# Full pipeline (scrape Reddit + analyze)
./run_app.sh

# Skip scraping, analyze existing data
./run_app.sh --skip-scraper

# Custom subreddits
python3 reddit_scraper_agent.py startups SideProject --limit 50
```

## 📁 Output

PicoPitch generates:

```
picopitch_outputs/
├── 1_Technical_Hiring_Crisis/
│   ├── BRD_v1.md           # Business Requirements
│   ├── PRD_v1.md           # Technical Specs
│   └── AGILE_PLAN_v1.md    # 1-point tasks
└── 2_Customer_Support_AI/
    └── ... (same structure)
```

## 🎯 What It Does

PicoPitch transforms community discussions into actionable SaaS opportunities:

```mermaid
graph LR
    A[Reddit Posts] --> B[AI Analysis]
    B --> C[Problem Validation]
    C --> D[Business Documents]
    D --> E[AI-Ready Plans]
    E --> F[Cursor IDE Build]
```

### Key Features

- **Evidence-Based Discovery**: Extracts real user quotes, financial impacts, urgency indicators
- **Market Validation**: Aggregates pain points across multiple posts with frequency analysis
- **AI-Optimized Docs**: Generates BRD/PRD/Agile plans formatted for AI coding agents
- **MCP Integration Ready**: Pre-configured for Supabase, Stripe, GitHub servers

### Example Output

> **Opportunity: Technical Hiring Platform**
> 
> Based on 47 Reddit posts with evidence:
> - "Burned $75k on a developer who couldn't deliver" (234 upvotes)
> - Financial Impact: $50k-$100k losses (67% of posts)
> - Urgency: High (23% used "desperate", "urgent")
> 
> Generated: BRD with market validation, PRD with technical specs, 52 Agile tasks

## ⚙️ Configuration

### Environment Variables

Create `.env` from example:

```bash
cp .env.example .env
```

Required variables:
```env
GEMINI_API_KEY=your_gemini_api_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=PicoPitch:v1.0 (by /u/yourusername)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_service_role_key  # Use service role, not anon key
```

### Customization

**Target different subreddits** (`run_app.sh`):
```bash
SUBREDDITS_TO_SCRAPE=("SideProject" "startups" "entrepreneur")
POST_LIMIT=50
COMMENT_LIMIT=30
```

**AI model settings** (`orchestrator.py`):
```python
FLASH_MODEL_NAME = "gemini-2.5-flash-preview-05-20"  # Fast processing
PRO_MODEL_NAME = "gemini-2.5-pro-preview-06-05"      # Deep analysis
MIN_LEADS_FOR_THEME = 3                              # Minimum posts per opportunity
```

## 🏗️ Architecture

### Multi-Agent System

1. **Reddit Scraper Agent**: Collects posts/comments from subreddits
2. **Gemini Analysis Agent**: Extracts problems, validates opportunities
3. **Orchestrator Agent**: Coordinates 6-stage pipeline with parallel processing
4. **Database Manager**: Supabase integration for persistent storage
5. **File Exporter**: Generates organized documentation

### Processing Pipeline

```
1. Extract Problems → 2. Group Domains → 3. Consolidate Themes
→ 4. Create Opportunities → 5. Validate & Score → 6. Generate Docs
```

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Rate limits** | Built-in retry with exponential backoff |
| **No tables created** | Run `database/schema.sql` in Supabase SQL editor |
| **No opportunities** | Lower `MIN_LEADS_FOR_THEME` threshold |
| **Connection errors** | Verify service role key (not anon key) |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

### Development Setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests (when available)
python -m pytest

# Format code
black .
```

## 📄 License

MIT License - see [LICENSE](LICENSE) file

## 👨‍💻 About the Creator

Hi! I'm Darren, a designer turned AI prototyper and indie hacker based in Tokyo. I build full-stack SaaS tools that merge design intuition with AI capabilities.

### Why I Built PicoPitch

As AI coding tools like Cursor became my daily drivers, I found myself constantly writing BRDs, PRDs, and sprint plans to feed these AI agents. But I was doing this manually, based on hunches rather than real user data.

PicoPitch automates this entire discovery process - it finds real problems from Reddit, validates them with evidence, and generates AI-ready documentation. The entire system was built using the same "vibe coding" approach it enables, proving that modern AI tools can accelerate development from idea to implementation.

This tool has transformed how I evaluate and build side projects. Instead of guessing what to build, I let real user pain points guide my decisions.

### Connect

- 🐦 Twitter: [@Darren_Head](https://twitter.com/Darren_Head)
- 💻 GitHub: [@darrenhead](https://github.com/darrenhead)
- 💼 LinkedIn: [/in/darrenhead](https://linkedin.com/in/darrenhead)
- 📧 Email: info@darrenhead.com

Got feedback or want to chat about AI-powered development? I'd love to hear from you!

## 🙏 Acknowledgments

- [Google Gemini](https://gemini.google.com) - AI analysis engine
- [PRAW](https://github.com/praw-dev/praw) - Reddit API wrapper
- [Supabase](https://supabase.com) - Database backend
- [Cursor IDE](https://cursor.sh) - AI development environment

---

**Built with ❤️ in Tokyo using modern agentic patterns**
