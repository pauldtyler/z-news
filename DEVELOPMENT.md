# Z-News Development Guide

## Project Structure

```
z-news/
├── services/           # Core application services
├── config/            # Configuration files (clients, competitors, topics)
├── data/              # Generated news data and summaries
├── archive/           # Old test files and data (not deployed)
├── scripts/           # Utility scripts (not deployed)
├── deployment/        # Deployment configs (AWS, GCP, etc.)
├── docs/              # Documentation (not deployed)
├── simple_api.py      # Main API for Vercel deployment
├── dev.py             # Local development server
├── requirements.txt   # Vercel/production dependencies
└── daily_summary.json # Latest generated summary
```

## Local Development

### 1. Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Ensure environment variables are set in .env
NEWSAPI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
```

### 2. Run Local Server
```bash
# Start development server
python dev.py

# Test endpoints
curl http://localhost:5000/daily-summary
curl http://localhost:5000/healthcheck
```

### 3. Collect Fresh Data
```bash
# Collect news and generate summaries
python scripts/run_collection.py

# Or run individual steps
python collect_all_news.py --target clients
python generate_daily_summary.py
```

## Vercel Deployment

### Automatic Deployment
- Push to `main` branch → Vercel auto-deploys
- Uses `simple_api.py` as entry point
- Environment variables configured in Vercel dashboard

### Environment Variables in Vercel
```
NEWSAPI_API_KEY = your_newsapi_key
ANTHROPIC_API_KEY = your_anthropic_key
```

### API Endpoints (Production)
- `GET /daily-summary` - Pre-generated daily summary
- `GET /healthcheck` - Service health check
- `GET /status` - Service status

## File Organization

### Core Files (Deployed)
- `simple_api.py` - Main API server
- `services/` - Business logic
- `config/` - Entity configurations  
- `daily_summary.json` - Latest summary data
- `requirements.txt` - Dependencies

### Development Only (Not Deployed)
- `dev.py` - Local server
- `scripts/` - Utility scripts
- `archive/` - Old files
- `deployment/` - Other platform configs
- `docs/` - Documentation

## Key Features

✅ **NewsAPI Integration** - Replaced DuckDuckGo with NewsAPI  
✅ **Claude AI Summaries** - Automated executive summaries  
✅ **Auto Deployment** - Push to main → Live on Vercel  
✅ **Local Testing** - Full development environment  
✅ **Clean Structure** - Organized and maintainable