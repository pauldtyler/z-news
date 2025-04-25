# Z-News: Financial Services News Collection and Analysis

A comprehensive system for collecting, processing, and summarizing news about financial services clients, competitors, and industry topics.

## Overview

Z-News automates the collection of recent news articles for financial services clients, competitors, and industry topics, then generates executive summaries using Claude AI. The system is designed to help executives stay informed about their clients', competitors', and industry trends with flexible daily or weekly cadence options.

## Features

- Automated news collection from DuckDuckGo (daily or weekly options)
- Website monitoring for direct tracking of company blogs and newsrooms
- Rate limiting and error handling to prevent API blocks
- Batched processing of multiple entities
- Adaptive result counts based on company profile
- Flexible configuration through external JSON files
- Modular architecture with separation of concerns
- Combined report option with categorized sections
- Executive summary generation using Claude API
- Support for clients, competitors, and industry topics
- Daily news collection with automatic cleanup of intermediate files
- Duplicate detection to eliminate repeated stories

## Project Structure

```
z-news/
├── config/                 # Configuration files
│   ├── clients.json        # Client list with search queries
│   ├── competitors.json    # Competitor list with search queries
│   ├── config.py           # Configuration constants
│   ├── topics.json         # Industry topics list with search queries
│   ├── websites.json       # Website monitoring configuration
│   └── __init__.py
├── services/               # Service modules
│   ├── api_client.py       # Claude API client
│   ├── search_service.py   # Search service
│   ├── website_monitor.py  # Website monitoring service
│   └── __init__.py
├── data/                   # Output directory (created at runtime)
├── batch_executive_summary.py  # Summary generation script
├── collect_all_news.py     # News collection script
├── templates.py            # Templates for Claude prompts
├── utils.py                # Utility functions
└── README.md
```

## Components

### 1. News Collection

The `collect_all_news.py` script searches for and collects news articles for specified clients, competitors, and industry topics. It offers both weekly and daily collection options.

#### Usage

```bash
# Weekly News Collection (Default Mode)

# Collect weekly news for clients only (default)
python collect_all_news.py --target clients

# Collect weekly news for competitors only
python collect_all_news.py --target competitors

# Collect weekly news for industry topics
python collect_all_news.py --target topics

# Collect weekly news for both clients and competitors
python collect_all_news.py --target both

# Collect weekly news for all types (clients, competitors, topics)
python collect_all_news.py --target all

# Disable adaptive result counts
python collect_all_news.py --target clients --no-adaptive

# Daily News Collection with Single Summary

# Collect just the prior day's news for clients and competitors
# and generate a single consolidated summary (cleans up intermediate files)
python collect_all_news.py --daily
```

#### Weekly Collection
The script collects news from the past week and adjusts the number of results based on company profile:
- High-profile companies (more active): 5 articles per company
- Medium-profile companies (standard): 3 articles per company
- Low-profile companies (less active): 4 articles per company for increased coverage
- Industry topics: 5 articles per topic

#### Daily Collection (with `--daily` flag)
- Collects only the prior day's news for clients and competitors (no industry topics)
- Generates a single consolidated markdown summary using Claude API
- Automatic cleanup of intermediate files, keeping only the consolidated CSV and markdown summary

### 2. Executive Summary Generation

The `batch_executive_summary.py` script processes collected news data and generates executive summaries using Claude API.

#### Usage

```bash
# Generate a summary for client news (default)
python batch_executive_summary.py --type client

# Generate a summary for competitor news
python batch_executive_summary.py --type competitor

# Generate a summary for industry topics
python batch_executive_summary.py --type topic

# Generate summaries for all types
python batch_executive_summary.py --type all

# Create a combined report with all summaries
python batch_executive_summary.py --type all --combined

# Specify a custom CSV file path
python batch_executive_summary.py --type client --csv /path/to/your/file.csv

# Specify individual CSV files for each type
python batch_executive_summary.py --type all --client-csv /path/to/client.csv --competitor-csv /path/to/competitor.csv --topic-csv /path/to/topic.csv
```

## Data Flow

1. `collect_all_news.py` collects weekly news articles and saves them to CSV files:
   - Client news: `data/client_news_[timestamp].csv`
   - Competitor news: `data/competitor_news_[timestamp].csv`
   - Topic news: `data/topic_news_[timestamp].csv`
   - Combined weekly news (when using `--target both` or `--target all`): `data/weekly_news_[timestamp].csv`

2. The latest CSV file paths are tracked in:
   - `data/latest_client_csv.txt`
   - `data/latest_competitor_csv.txt`
   - `data/latest_topic_csv.txt`
   - `data/latest_weekly_csv.txt`

3. `batch_executive_summary.py` processes these CSV files to generate:
   - Individual batch summaries: `data/executive_summary_[type]_batch[n]_[timestamp].md`
   - Consolidated summary: `data/executive_summary_[type]_full_[timestamp].md`
   - Combined report (with `--combined`): `data/executive_summary_combined_[timestamp].md`

## Recommended Workflows

### Weekly Workflow

For a complete weekly news summary:

1. Collect news for all entity types:
   ```bash
   python collect_all_news.py --target all
   ```

2. Generate combined report with all summary types:
   ```bash
   python batch_executive_summary.py --type all --combined
   ```

3. View the generated markdown files in the `data` directory or convert them to other formats as needed.

### Daily Workflow

For a quick daily news update:

1. Collect the prior day's news for clients and competitors and generate a summary:
   ```bash
   python collect_all_news.py --daily
   ```

2. The script will:
   - Collect news from the past day
   - Generate a consolidated summary with Claude
   - Clean up intermediate files automatically
   - Keep only the final combined CSV and markdown summary

## Customization

### Modifying entities and search queries

Edit the JSON files in the `config` directory:

#### Client/Competitor Format:
```json
[
  {
    "name": "Company Name",
    "query": "\"Company Name\" AND (Industry OR Related Term)"
  }
]
```

#### Topic Format:
```json
[
  {
    "category": "Category Name",
    "name": "Topic Name",
    "query": "\"topic keywords\" AND (relevant OR search OR terms)"
  }
]
```

### Adjusting configuration parameters

Modify the values in `config/config.py`:

```python
# Search configuration
BATCH_SIZE = 3  # Process entities in batches of this size
DELAY_BETWEEN_REQUESTS = 8  # Seconds to wait between requests
DEFAULT_RESULT_COUNT = 3  # Default number of results per entity

# Topic categories order
TOPIC_CATEGORIES = [
    "Annuity Market",
    "Life Insurance Market",
    "Technology",
    # ...
]
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install pandas duckduckgo_search anthropic python-dotenv
   ```

3. Create a `.env` file with your API keys:
   ```
   ANTHROPIC_API_KEY=your_claude_api_key
   ```

## Output Examples

### News Collection CSV Format

```
client,title,url,date,source,excerpt,relevance
Company Name,Article Title,https://example.com,2025-04-19,Source Name,Article excerpt...,0.85
```

### Executive Summary Format

```markdown
# Client Executive News Summary
2025-04-19

## Company Name
Company has reported Q1 earnings of $1.2B, exceeding analyst expectations by 3%. CEO Jane Smith announced a new digital transformation initiative focusing on AI-powered customer service solutions set to launch in Q3. The firm also completed its acquisition of TechCorp for $500M, expanding its software capabilities.
```

### Combined Weekly Report Format

```markdown
# Financial Services Industry Executive Summary
2025-04-19

## Overview
This report provides a comprehensive weekly summary of key developments across the financial services industry, organized by market segments, industry topics, and individual companies.

## Industry Topics

# Annuity Market

## Annuity Industry Trends
[Summary paragraph about annuity industry trends]

# Technology

## Digital Transformation
[Summary paragraph about digital transformation in insurance]

## Client Companies

## Company A
[Summary paragraph about Company A]

## Company B
[Summary paragraph about Company B]

## Competitor Companies

## Competitor X
[Summary paragraph about Competitor X]
```

### Daily Summary Format

```markdown
# Daily Financial Services News Summary
2025-04-19

## Client Companies

### Company A
Company A has announced a new strategic partnership with Technology Provider Z to enhance their digital payment infrastructure. The partnership will focus on implementing blockchain-based solutions for faster transaction processing and improved security protocols. This move comes as part of Company A's $50M digital transformation initiative announced earlier this quarter.

### Company B
[Daily news summary for Company B]

## Competitor Companies

### Competitor X
[Daily news summary for Competitor X]

### Competitor Y
[Daily news summary for Competitor Y]
```

## Website Monitoring

The website monitoring system directly tracks company websites for updates to news, blogs, and press releases.

### Usage

```bash
# Run website monitoring to check for updates
python services/website_monitor.py

# Run with a custom config file
python services/website_monitor.py --config path/to/custom/websites.json
```

### Configuration

The website monitoring system is configured through a JSON file located at `config/websites.json`:

```json
[
  {
    "name": "Company Name",
    "url": "https://company.com/newsroom/",
    "selector": "article.post, .news-item",
    "frequency": 86400,
    "type": "news"
  }
]
```

Each entry in the configuration includes:
- `name`: Display name for the website
- `url`: Full URL to the page containing news/blog content
- `selector`: CSS selector(s) to identify individual news items (comma-separated for multiple)
- `frequency`: Checking frequency in seconds (86400 = daily)
- `type`: Content type (news, blog, insights, etc.)

### Output

Website monitoring results are saved to:
- CSV files: `data/website_updates/website_updates_[timestamp].csv`
- Latest file reference: `data/website_updates/latest_website_updates.txt`

### Scheduling

To run website monitoring on a regular schedule:

#### Using macOS Calendar:
1. Open Calendar app and create a new event
2. Set it to repeat at your desired frequency
3. Add an alert of type "Run script"
4. Create a shell script in a location like ~/Documents/scripts/run_monitor.sh:
   ```bash
   #!/bin/bash
   cd /Users/yourname/path/to/z-news
   source venv/bin/activate
   python services/website_monitor.py >> data/website_updates/monitor_log.txt 2>&1
   ```
5. Make the script executable: `chmod +x ~/Documents/scripts/run_monitor.sh`
6. Select this script in the Calendar alert dialog

#### Using cron:
```bash
# Edit crontab
crontab -e

# Add line to run daily at 8 AM
0 8 * * * cd /path/to/z-news && /path/to/z-news/venv/bin/python /path/to/z-news/services/website_monitor.py
```

## Requirements

- Python 3.8+
- pandas
- duckduckgo_search
- anthropic
- python-dotenv
- Node.js (for website monitoring)
- Puppeteer (npm install puppeteer, auto-installed if missing)