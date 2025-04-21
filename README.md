# Z-News: Weekly Financial Services News Collection and Analysis

A comprehensive system for collecting, processing, and summarizing weekly news about financial services clients and competitors.

## Overview

Z-News automates the weekly collection of recent news articles for financial services clients and competitors, and generates executive summaries using Claude AI. The system is designed to help executives stay informed about their clients' and competitors' business developments with a regular weekly cadence.

## Features

- Automated weekly news collection from DuckDuckGo
- Rate limiting and error handling to prevent API blocks
- Batched processing of multiple entities
- Adaptive result counts based on company profile
- Combined weekly report option for both clients and competitors
- Executive summary generation using Claude AI
- Support for both client and competitor news

## Components

### 1. Weekly News Collection

The `collect_all_news.py` script searches for and collects the most recent week's news articles for specified clients and competitors.

#### Usage

```bash
# Collect weekly news for clients only (default)
python collect_all_news.py --target clients

# Collect weekly news for competitors only
python collect_all_news.py --target competitors

# Collect weekly news for both clients and competitors (creates a combined file)
python collect_all_news.py --target both

# Disable adaptive result counts
python collect_all_news.py --target clients --no-adaptive
```

The script collects news from the past week and adjusts the number of results based on company profile:
- High-profile companies (more active): 5 articles per company
- Medium-profile companies (standard): 3 articles per company
- Low-profile companies (less active): 4 articles per company for increased coverage

### 2. Executive Summary Generation

The `batch_executive_summary.py` script processes collected news data and generates executive summaries using Claude AI.

#### Usage

```bash
# Generate a summary for client news (default)
python batch_executive_summary.py --type client

# Generate a summary for competitor news
python batch_executive_summary.py --type competitor

# Specify a custom CSV file path
python batch_executive_summary.py --type client --csv /path/to/your/file.csv
```

## Data Flow

1. `collect_all_news.py` collects weekly news articles and saves them to CSV files:
   - Client news: `data/client_news_[timestamp].csv`
   - Competitor news: `data/competitor_news_[timestamp].csv`
   - Combined weekly news (when using `--target both`): `data/weekly_news_[timestamp].csv`

2. The latest CSV file paths are tracked in:
   - `data/latest_client_csv.txt`
   - `data/latest_competitor_csv.txt`
   - `data/latest_weekly_csv.txt`

3. `batch_executive_summary.py` processes these CSV files to generate:
   - Individual batch summaries: `data/executive_summary_[type]_batch[n]_[timestamp].md`
   - Consolidated summary: `data/executive_summary_[type]_full_[timestamp].md`

## Recommended Weekly Workflow

For a complete weekly news summary:

1. Collect combined news for both clients and competitors:
   ```bash
   python collect_all_news.py --target both
   ```

2. Generate summaries for both types:
   ```bash
   python batch_executive_summary.py --type client
   python batch_executive_summary.py --type competitor
   ```

3. View the generated markdown files in the `data` directory or convert them to other formats as needed.

## Customization

### Adding new clients or competitors

Edit the `clients` or `competitors` lists in `collect_all_news.py`:

```python
competitors = [
    ("Company Name", "\"Company Name\" AND (Industry OR Related Term)"),
    # Add more companies here...
]
```

### Adjusting search parameters

Modify the configuration constants in `collect_all_news.py`:

```python
BATCH_SIZE = 3  # Number of entities per batch
MAX_RESULTS_PER_CLIENT = 5  # Articles per entity
DEFAULT_TIME_PERIOD = 'm'  # Default time filter (month)
```

## Requirements

- Python 3.8+
- pandas
- duckduckgo_search
- anthropic
- python-dotenv

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
client,title,url,date,source,excerpt
Company Name,Article Title,https://example.com,2025-04-19,Source Name,Article excerpt...
```

### Executive Summary Format

```markdown
# Client Executive News Summary
2025-04-19

## Company Name
Company has reported Q1 earnings of $1.2B, exceeding analyst expectations by 3%. CEO Jane Smith announced a new digital transformation initiative focusing on AI-powered customer service solutions set to launch in Q3. The firm also completed its acquisition of TechCorp for $500M, expanding its software capabilities.
```