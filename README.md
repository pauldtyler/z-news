# Z-News: Financial Services News Collection and Analysis

A comprehensive system for collecting, processing, and summarizing news about financial services clients, competitors, and industry topics.

## Overview

Z-News automates the collection of recent news articles for financial services clients, competitors, and industry topics, then generates executive summaries using Claude AI. The system is designed to help executives stay informed about their clients', competitors', and industry trends with flexible daily or weekly cadence options.

## Features

- Automated news collection from DuckDuckGo (daily or weekly options)
- Robust website monitoring for direct tracking of company blogs and newsrooms
- Incremental website monitoring with checkpointing to prevent timeouts
- Comprehensive tools for viewing and analyzing website changes
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
├── monitor_incremental.py  # Robust incremental website monitoring
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
- Automatically removes duplicate news articles by comparing with previous collections
- Applies date filtering to ensure only recent articles (from the past 3 days) are included
- Intelligently handles companies with only older news by keeping their most recent article
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

3. Monitor competitor websites for direct updates:
   ```bash
   python monitor_incremental.py 
   ```

4. View any detected website changes:
   ```bash
   python monitor_incremental.py --show-changes
   ```

5. View the generated markdown files in the `data` directory or convert them to other formats as needed.

### Daily Workflow

For a quick daily news update:

1. Collect the prior day's news for clients and competitors and generate a summary:
   ```bash
   python collect_all_news.py --daily
   ```

2. Monitor competitor websites (process a few at a time to avoid timeouts):
   ```bash
   python monitor_incremental.py --max-sites 5
   ```

3. Review any website changes detected:
   ```bash
   python monitor_incremental.py --show-changes
   ```

4. The collection script will:
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
# Run website monitoring to check for updates (standard method)
python services/website_monitor.py

# Run with a custom config file
python services/website_monitor.py --config path/to/custom/websites.json

# For improved reliability and timeout prevention:
python monitor_incremental.py

# Process just a few websites at a time (good for timeouts)
python monitor_incremental.py --max-sites 3

# Continue from where you left off 
python monitor_incremental.py --max-sites 3

# List completed websites
python monitor_incremental.py --list

# View recent website changes (new/updated content)
python monitor_incremental.py --show-changes

# Show more or fewer changes
python monitor_incremental.py --show-changes --limit 10

# Filter changes for a specific company
python monitor_incremental.py --show-changes --company "luma"

# List available CSV files with website changes
python monitor_incremental.py --list-files

# View changes from a specific CSV file
python monitor_incremental.py --show-changes --csv-file website_updates_20250427_181345.csv

# Start fresh (ignore previous progress)
python monitor_incremental.py --fresh

# Clear checkpoint and start over
python monitor_incremental.py --clear
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

### Incremental Monitoring

The `monitor_incremental.py` script provides a more robust way to monitor websites with these advantages:

- Processes one website at a time with progress checkpointing
- Automatically resumes where it left off if interrupted
- Can process websites in smaller batches to prevent timeouts
- Provides monitoring status and progress information
- More resilient to timeouts and connection issues

Key features:
- Progress tracking: Monitors and saves which websites have been processed
- Resumable: Can continue from where it was interrupted
- Configurable: Control how many sites to process in a single run
- Progress visibility: Shows completed websites and monitoring status

### Viewing Website Changes

The incremental monitor provides comprehensive tools to view and analyze detected changes:

```bash
# View all recent changes
python monitor_incremental.py --show-changes

# Show only the first 5 changes
python monitor_incremental.py --show-changes --limit 5

# View changes for a specific company
python monitor_incremental.py --show-changes --company "ipipe"  # Partial match works

# List all available change files
python monitor_incremental.py --list-files

# View changes from a specific file
python monitor_incremental.py --show-changes --csv-file website_updates_20250427_181322.csv
```

The change viewer displays:
- A summary of total changes detected
- Changes grouped by company and type (new/updated)
- Detailed information for each change including:
  - Title of the content
  - URL to view the full content
  - Publication date (when available)
  - Content excerpt (when available)

This makes it easy to quickly scan for important updates and access the full content directly.

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
   
   # Use the incremental monitor instead of the standard one
   python monitor_incremental.py --max-sites 5 >> data/website_updates/monitor_log.txt 2>&1
   ```
5. Make the script executable: `chmod +x ~/Documents/scripts/run_monitor.sh`
6. Select this script in the Calendar alert dialog

#### Using cron:
```bash
# Edit crontab
crontab -e

# Add line to run daily at 8 AM with incremental monitor
0 8 * * * cd /path/to/z-news && /path/to/z-news/venv/bin/python /path/to/z-news/monitor_incremental.py --max-sites 5 >> /path/to/z-news/data/website_updates/monitor_log.txt 2>&1

# For larger sets of websites, run multiple times throughout the day
0 8,12,16,20 * * * cd /path/to/z-news && /path/to/z-news/venv/bin/python /path/to/z-news/monitor_incremental.py --max-sites 3 >> /path/to/z-news/data/website_updates/monitor_log.txt 2>&1
```

## API Deployment for Next.js Integration

Z-News includes a deployed AWS Lambda API for integration with Next.js websites and applications.

### API Endpoint

The production API is available at:
```
https://e67d6gnyza.execute-api.us-east-1.amazonaws.com/prod/daily-summary
```

### API Response Format

The API returns a JSON response optimized for website integration:

```json
{
  "date": "2025-05-22",
  "generated_at": "2025-05-22T23:55:45.574948",
  "summary": "# Financial Services News Summary - May 22, 2025\n\n## Service Status\n\nThe news search service is currently experiencing connectivity issues with external data providers...",
  "companies_included": [
    "Ameriprise Financial, Inc.",
    "American National Life Insurance", 
    "Advisors Excel, LLC"
  ],
  "total_articles": 0,
  "time_period": "past week",
  "status": "service_unavailable"
}
```

### Next.js Integration

The API is fully tested and ready for integration. Here's how to integrate it with your Next.js application:

#### 1. Create Vercel Cron Job API Route

Create `pages/api/cron/daily-summary.js` (or `app/api/cron/daily-summary/route.js` for App Router):

```javascript
// pages/api/cron/daily-summary.js
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Method not allowed' });
  }

  try {
    const response = await fetch(
      'https://e67d6gnyza.execute-api.us-east-1.amazonaws.com/prod/daily-summary'
    );
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const data = await response.json();
    
    // Store in your database/storage (implement based on your setup)
    // await saveDailySummary(data);
    
    res.status(200).json({ success: true, data });
  } catch (error) {
    console.error('Error fetching daily summary:', error);
    res.status(500).json({ error: error.message });
  }
}
```

#### 2. Configure Vercel Cron

Add to your `vercel.json`:

```json
{
  "crons": [{
    "path": "/api/cron/daily-summary",
    "schedule": "0 8 * * *"
  }]
}
```

This runs daily at 8 AM UTC.

#### 3. Display Summary on Your Site

Create a page component to display the daily summary:

```javascript
// components/DailySummary.jsx
import { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';

export default function DailySummary() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchDailySummary();
  }, []);

  const fetchDailySummary = async () => {
    try {
      // Option 1: Fetch directly from AWS API (for real-time data)
      const response = await fetch(
        'https://e67d6gnyza.execute-api.us-east-1.amazonaws.com/prod/daily-summary'
      );
      
      // Option 2: Fetch from your stored data (recommended for cached data)
      // const response = await fetch('/api/get-daily-summary');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setSummary(data);
      
      // Handle service unavailable status gracefully
      if (data.status === 'service_unavailable') {
        console.log('News service temporarily unavailable, showing fallback content');
      }
      
    } catch (error) {
      console.error('Error fetching summary:', error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div>Loading daily summary...</div>;
  if (error) return <div>Error loading summary: {error}</div>;
  if (!summary) return <div>No summary available</div>;

  return (
    <div className="daily-summary">
      <div className="summary-header">
        <h2>Financial Services News - {summary.date}</h2>
        <div className="summary-meta">
          <p>Generated: {new Date(summary.generated_at).toLocaleDateString()}</p>
          <p>Companies: {summary.companies_included?.length || 0}</p>
          <p>Articles: {summary.total_articles}</p>
          <p>Period: {summary.time_period}</p>
          {summary.status === 'service_unavailable' && (
            <p className="status-warning">⚠️ Service temporarily unavailable - showing cached content</p>
          )}
        </div>
      </div>
      
      <div className="summary-content">
        <ReactMarkdown>{summary.summary}</ReactMarkdown>
      </div>
      
      {summary.status === 'service_unavailable' && (
        <button onClick={fetchDailySummary} className="retry-button">
          Retry
        </button>
      )}
    </div>
  );
}
```

#### 4. Custom Company Selection

You can specify which companies to include in the summary:

```javascript
const fetchCustomSummary = async (companies) => {
  const companiesParam = companies.join(',');
  const response = await fetch(
    `https://e67d6gnyza.execute-api.us-east-1.amazonaws.com/prod/daily-summary?companies=${encodeURIComponent(companiesParam)}`
  );
  const data = await response.json();
  return data;
};

// Usage examples:
fetchCustomSummary(['Fidelity Investments']);
fetchCustomSummary(['J.P. Morgan Chase & Co.', 'Ameriprise Financial, Inc.']);
```

#### 5. Manual API Testing

You can test the API directly:

```bash
# Basic request - returns summary for first 5 default companies
curl "https://e67d6gnyza.execute-api.us-east-1.amazonaws.com/prod/daily-summary"

# Request specific companies
curl "https://e67d6gnyza.execute-api.us-east-1.amazonaws.com/prod/daily-summary?companies=Fidelity%20Investments"

# Multiple companies
curl "https://e67d6gnyza.execute-api.us-east-1.amazonaws.com/prod/daily-summary?companies=Fidelity%20Investments,J.P.%20Morgan%20Chase%20%26%20Co."
```

**API Status**: ✅ **Fully operational and tested**

The API gracefully handles network connectivity issues and returns informative fallback content when news services are temporarily unavailable.

### API Features

- **CORS enabled**: Ready for browser requests
- **Lightweight**: No heavy dependencies, fast response times
- **Graceful fallbacks**: Returns informative messages when search services are unavailable
- **Flexible company selection**: Supports custom company lists via query parameters
- **Markdown-ready**: Summary content is formatted for direct markdown rendering

### Local Development

For local testing, you can also run the Flask development server:

```bash
python app.py
```

Then access: `http://localhost:5000/daily-summary`

## Requirements

- Python 3.8+
- pandas
- duckduckgo_search
- anthropic
- python-dotenv
- Node.js (for website monitoring)
- Puppeteer (npm install puppeteer, auto-installed if missing)