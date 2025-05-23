# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Install dependencies: `pip install pandas duckduckgo_search anthropic python-dotenv`
- Run collection script: `python collect_all_news.py --target [clients|competitors|both]`
- Generate summaries: `python batch_executive_summary.py --type [client|competitor]`
- Environment: Create virtual environment with `python -m venv venv` and activate it
- Run Flask API locally: `python app.py`
- Test API endpoint: `curl -X POST -H "Content-Type: application/json" -d '{"company_name":"JP Morgan"}' http://localhost:5000/z-news`

## API Endpoints

### POST /z-news
Real-time news search and summary generation for specific companies.

**Parameters:**
- `company_name` (required): Name of company to search for
- `time_filter` (optional): Time period (d/w/m/y, default: w)
- `max_results` (optional): Maximum articles to return
- `summary_type` (optional): client|competitor|consolidated (default: client)
- `competitor_name` (optional): Required for consolidated summaries

**Response:** Full article data with generated summary

### GET /daily-summary
Lightweight endpoint for website integration that returns consolidated daily summary.

**Query Parameters:**
- `companies` (optional): Comma-separated list of companies (defaults to all clients)
- `date` (optional): Date in YYYY-MM-DD format (defaults to today)

**Response:** JSON optimized for website display
```json
{
  "date": "2025-01-22",
  "generated_at": "2025-01-22T08:00:00Z",
  "summary": "markdown content...",
  "companies_included": ["JP Morgan", "Goldman Sachs"],
  "total_articles": 25
}
```

### GET /healthcheck
Service health verification endpoint.

## Code Style Guidelines

- **Imports**: Group standard library imports first, followed by third-party libraries, then local modules
- **Functions**: Use descriptive names with snake_case and type hints where appropriate
- **Error Handling**: Use try/except with specific exception types and fallback mechanisms
- **Documentation**: All functions should have docstrings explaining purpose, args, and returns
- **Variable Names**: Use descriptive names that reflect purpose (e.g., client_news vs data)
- **Constants**: Use UPPER_CASE for configuration constants
- **Rate Limiting**: Implement proper delays and exponential backoff for API requests
- **Data Structure**: Follow pandas best practices with consistent DataFrame operations