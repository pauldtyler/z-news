#!/bin/bash
# Setup script for the new cron-based architecture

echo "🚀 Setting up Z-News Cron Architecture..."

# 1. Test data collection and JSON generation
echo "📊 Testing data collection and JSON generation..."
python generate_daily_summary.py

if [ ! -f "daily_summary.json" ]; then
    echo "❌ JSON file was not generated. Please check the script."
    exit 1
fi

echo "✅ JSON file generated successfully"

# 2. Test the simple API
echo "🔍 Testing simple API..."
python -c "
import sys
sys.path.append('.')
from simple_api import app
with app.test_client() as client:
    response = client.get('/daily-summary')
    if response.status_code == 200:
        print('✅ Simple API working')
    else:
        print('❌ Simple API failed')
        sys.exit(1)
"

# 3. Show file structure
echo "📁 Current file structure:"
echo "  ✓ daily_summary.json (generated)"
echo "  ✓ simple_api.py (fast API)"
echo "  ✓ .github/workflows/daily-news-collection.yml (cron job)"
echo "  ✓ vercel.json (deployment config)"

# 4. Instructions
echo "
🎯 Next Steps:

1. **Set up GitHub repository secrets:**
   - Go to your GitHub repo → Settings → Secrets → Actions
   - Add: ANTHROPIC_API_KEY (required)
   - Add: AWS_ACCESS_KEY_ID (optional, for S3 storage)
   - Add: AWS_SECRET_ACCESS_KEY (optional, for S3 storage)

2. **Test the cron job manually:**
   - Go to your GitHub repo → Actions tab
   - Find 'Daily News Collection' workflow
   - Click 'Run workflow' to test manually

3. **Deploy to Vercel:**
   - Run: vercel --prod
   - Or connect your GitHub repo to Vercel for auto-deployment

4. **Update your Next.js website:**
   - Change fetch URL to your Vercel deployment
   - Example: https://your-vercel-app.vercel.app/daily-summary

5. **Monitor the system:**
   - Check /status endpoint for last update time
   - Check /healthcheck for service health
   - Cron runs daily at 8 AM UTC (midnight PST)

📋 API Endpoints:
  - /daily-summary (main endpoint)
  - /daily-summary?companies=Fidelity Investments (filtered)
  - /status (system status)
  - /healthcheck (health check)

🔄 Architecture:
  [GitHub Cron] → [Collect News] → [Generate JSON] → [Commit to Repo]
                                                    ↓
  [Your Website] → [Vercel API] → [Serve Static JSON] → [Fast Response]
"

echo "✅ Setup complete! Your new architecture is ready."