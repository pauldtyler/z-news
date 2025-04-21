# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

- Install dependencies: `pip install pandas duckduckgo_search anthropic python-dotenv`
- Run collection script: `python collect_all_news.py --target [clients|competitors|both]`
- Generate summaries: `python batch_executive_summary.py --type [client|competitor]`
- Environment: Create virtual environment with `python -m venv venv` and activate it

## Code Style Guidelines

- **Imports**: Group standard library imports first, followed by third-party libraries, then local modules
- **Functions**: Use descriptive names with snake_case and type hints where appropriate
- **Error Handling**: Use try/except with specific exception types and fallback mechanisms
- **Documentation**: All functions should have docstrings explaining purpose, args, and returns
- **Variable Names**: Use descriptive names that reflect purpose (e.g., client_news vs data)
- **Constants**: Use UPPER_CASE for configuration constants
- **Rate Limiting**: Implement proper delays and exponential backoff for API requests
- **Data Structure**: Follow pandas best practices with consistent DataFrame operations