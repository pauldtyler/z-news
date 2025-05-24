# Z-News: Financial Services News Collection and Analysis

A comprehensive system for collecting, processing, and summarizing news about financial services clients, competitors, and industry topics with AI-powered insights.

## Overview

Z-News automates the collection of recent news articles for financial services clients, competitors, and industry topics, then generates executive summaries using Claude AI. The system is designed to help executives stay informed about their clients', competitors', and industry trends with flexible daily or weekly cadence options.

## ✨ Features

- **NewsAPI Integration** - Reliable news collection with boolean search support
- **Claude AI Summaries** - Executive-level insights and analysis
- **Vercel Deployment** - Automatic deployment from GitHub with serverless API
- **Local Development** - Full local testing environment
- **Clean Architecture** - Organized, maintainable codebase
- **Flexible Configuration** - JSON-based entity and query management
- **Rate Limiting & Error Handling** - Robust processing with exponential backoff
- **Website Monitoring** - Direct tracking of company newsrooms and blogs
- **Daily/Weekly Modes** - Adaptable collection schedules

## 🚀 Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables in .env
NEWSAPI_API_KEY=your_newsapi_key
ANTHROPIC_API_KEY=your_anthropic_key

# Start local development server
python dev.py

# Test API endpoints
curl http://localhost:5000/daily-summary
curl http://localhost:5000/healthcheck
```

### Collect Fresh News Data

```bash
# Run full collection pipeline
python scripts/run_collection.py

# Or run individual steps
python collect_all_news.py --target clients
python generate_daily_summary.py
```

### Deploy to Vercel

1. **Connect Repository**: Link this GitHub repo to Vercel
2. **Set Environment Variables** in Vercel dashboard:
   - `NEWSAPI_API_KEY`
   - `ANTHROPIC_API_KEY`
3. **Auto-Deploy**: Push to `main` branch → Vercel deploys automatically

## 📁 Project Structure

```
z-news/
├── 🎯 Core Application
│   ├── simple_api.py          # Main API for Vercel deployment
│   ├── services/              # Business logic modules
│   ├── config/                # Entity configurations (clients, competitors)
│   ├── daily_summary.json     # Latest generated summary
│   └── requirements.txt       # Production dependencies
│
├── 🔧 Development
│   ├── dev.py                 # Local development server
│   ├── scripts/               # Utility scripts and pipeline tools
│   ├── collect_all_news.py    # News collection engine
│   ├── generate_daily_summary.py # AI summary generation
│   └── batch_executive_summary.py # Batch processing
│
├── 📚 Documentation & Config
│   ├── README.md              # This file
│   ├── DEVELOPMENT.md         # Development guide
│   ├── CLAUDE.md              # AI assistant instructions
│   ├── vercel.json           # Vercel deployment config
│   └── docs/                 # Additional documentation
│
└── 📦 Archive & Deployment
    ├── archive/              # Old test files and data
    ├── deployment/           # AWS/GCP deployment configs
    └── data/                # Generated news data and summaries
```

## 🌐 API Endpoints

### Production (Vercel)
- `GET /daily-summary` - Pre-generated daily summary
- `GET /healthcheck` - Service health check

### Local Development
- `GET /daily-summary` - Daily summary with real-time generation
- `GET /healthcheck` - Health check
- `GET /status` - Detailed service status

## 📊 News Collection

### Usage

```bash
# Weekly News Collection (Default)
python collect_all_news.py --target clients     # Clients only
python collect_all_news.py --target competitors # Competitors only
python collect_all_news.py --target both        # Both clients & competitors
python collect_all_news.py --target all         # All entities + topics

# Daily News Collection
python collect_all_news.py --daily              # Daily collection with cleanup

# Disable adaptive result counts
python collect_all_news.py --target clients --no-adaptive
```

### Collection Features

- **Adaptive Result Counts**: Adjusts article count based on company profile
- **Boolean Search Support**: Complex search queries with AND/OR/quotes
- **Time Filtering**: Daily, weekly, monthly, yearly periods
- **Rate Limiting**: Prevents API blocks with exponential backoff
- **Duplicate Detection**: Eliminates repeated stories

## 🤖 AI Summary Generation

### Usage

```bash
# Generate summaries
python batch_executive_summary.py --type client      # Client summary
python batch_executive_summary.py --type competitor  # Competitor summary
python batch_executive_summary.py --type all         # All summaries
python batch_executive_summary.py --type all --combined # Combined report

# Custom CSV files
python batch_executive_summary.py --type client --csv /path/to/file.csv
```

### Summary Features

- **Executive-Level Insights**: Professional summaries for C-suite consumption
- **Categorized Organization**: Grouped by clients, competitors, topics
- **Markdown Output**: Ready for web display or conversion
- **Batch Processing**: Handles large datasets efficiently

## 🔧 Configuration

### Entity Configuration

Edit JSON files in the `config/` directory:

#### Clients/Competitors (`clients.json`, `competitors.json`)
```json
[
  {
    "name": "JP Morgan",
    "query": "\"JP Morgan\" OR \"JPMorgan Chase\" AND (banking OR financial)"
  },
  {
    "name": "Goldman Sachs", 
    "query": "\"Goldman Sachs\" AND (investment OR securities)"
  }
]
```

#### Topics (`topics.json`)
```json
[
  {
    "category": "Technology",
    "name": "AI in Finance",
    "query": "(\"artificial intelligence\" OR \"AI\") AND (finance OR banking OR insurance)"
  }
]
```

### Search Configuration

Modify `config/config.py`:

```python
# Search parameters
BATCH_SIZE = 3                    # Entities per batch
DELAY_BETWEEN_REQUESTS = 8        # Seconds between requests
DEFAULT_RESULT_COUNT = 3          # Articles per entity
MAX_RETRIES = 3                   # Retry attempts
INITIAL_BACKOFF = 2.0            # Backoff starting time
```

## 🌐 Website Monitoring

Direct monitoring of company websites and newsrooms:

```bash
# Incremental monitoring (recommended)
python monitor_incremental.py                    # Monitor all sites
python monitor_incremental.py --max-sites 5     # Process 5 sites
python monitor_incremental.py --show-changes    # View detected changes
python monitor_incremental.py --list           # Show monitoring status

# Standard monitoring
python services/website_monitor.py              # Monitor all configured sites
```

### Website Configuration (`config/websites.json`)

```json
[
  {
    "name": "Company Newsroom",
    "url": "https://company.com/newsroom/",
    "selector": "article.post, .news-item",
    "frequency": 86400,
    "type": "news"
  }
]
```

## 📈 Data Flow

1. **Collection**: `collect_all_news.py` → CSV files in `data/`
2. **Summary Generation**: `generate_daily_summary.py` → `daily_summary.json`
3. **API Serving**: `simple_api.py` serves pre-generated summaries
4. **Website Monitoring**: Direct tracking of company websites

### Output Files

```
data/
├── client_news_[timestamp].csv         # Raw client news data
├── competitor_news_[timestamp].csv     # Raw competitor news data  
├── daily_summary_[timestamp].md        # Markdown summary
├── daily_summary.json                 # JSON API response
└── website_updates/                   # Website monitoring results
```

## 🔄 Recommended Workflows

### Daily Workflow

```bash
# 1. Collect news and generate summary (automated)
python collect_all_news.py --daily

# 2. Monitor websites (optional)
python monitor_incremental.py --max-sites 5

# 3. Review generated content
cat data/daily_summary_*.md
```

### Weekly Workflow

```bash
# 1. Comprehensive collection
python collect_all_news.py --target all

# 2. Generate combined report
python batch_executive_summary.py --type all --combined

# 3. Monitor website changes
python monitor_incremental.py --show-changes
```

## 🚀 Deployment Options

### Vercel (Recommended)
- **Automatic**: Push to `main` → Auto-deploy
- **Serverless**: Scales automatically
- **Fast**: Global CDN distribution

### AWS Lambda
```bash
# Deploy to AWS
python deployment/aws_lambda.py
```

### Google Cloud Functions
```bash
# Deploy to GCP
python deployment/cloud_function.py
```

## 🔗 Next.js Integration

The API is designed for seamless Next.js integration:

```javascript
// Fetch daily summary
const response = await fetch('/daily-summary');
const summary = await response.json();

// Display with React Markdown
import ReactMarkdown from 'react-markdown';
<ReactMarkdown>{summary.summary}</ReactMarkdown>
```

### Vercel Cron Integration

Add to `vercel.json`:

```json
{
  "crons": [{
    "path": "/api/cron/daily-summary",
    "schedule": "0 8 * * *"
  }]
}
```

## 📋 Requirements

### Core Dependencies
- Python 3.8+
- requests >= 2.25.0
- anthropic >= 0.16.0
- pandas >= 2.0.0
- flask >= 2.0.0
- python-dotenv >= 1.0.0

### API Keys Required
- **NewsAPI**: Get from [newsapi.org](https://newsapi.org)
- **Anthropic Claude**: Get from [console.anthropic.com](https://console.anthropic.com)

### Optional (for website monitoring)
- Node.js and Puppeteer

## 🎯 Example Output

### API Response Format

```json
{
  "date": "2025-05-24",
  "generated_at": "2025-05-24T08:00:00Z",
  "summary": "# Daily Financial Services News Summary...",
  "companies_included": ["JP Morgan", "Goldman Sachs"],
  "total_articles": 25,
  "time_period": "past week",
  "status": "success"
}
```

### Markdown Summary Example

```markdown
# Financial Services News Summary - May 24, 2025

## Client Companies

### JP Morgan
JPMorgan Chase reported strong Q1 earnings with net income of $15.2B, 
exceeding analyst expectations. CEO Jamie Dimon highlighted the bank's 
continued investment in AI and digital transformation initiatives...

### Goldman Sachs
Goldman Sachs announced a new partnership with fintech startup TechCorp
to enhance their digital trading platform. The collaboration focuses on...
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes following the existing code style
4. Test locally with `python dev.py`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**🚀 Ready to deploy!** Connect this repository to Vercel for automatic deployment, or run locally for development and testing.