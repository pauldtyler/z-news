#!/bin/bash
# Verification script to check if everything is set up correctly

echo "🔍 Verifying Z-News Setup..."

# Check if all required files exist
echo "📁 Checking required files..."
files=(
    ".github/workflows/daily-news-collection.yml"
    "simple_api.py"
    "daily_summary.json"
    "vercel.json"
    "ARCHITECTURE_SUMMARY.md"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (missing)"
    fi
done

# Check if git is up to date
echo -e "\n📤 Checking git status..."
if git status --porcelain | grep -q .; then
    echo "  ⚠️  You have uncommitted changes"
    git status --short
else
    echo "  ✅ Git repository is clean"
fi

# Test the simple API
echo -e "\n🧪 Testing simple API..."
python -c "
import sys
sys.path.append('.')
try:
    from simple_api import app
    with app.test_client() as client:
        response = client.get('/daily-summary')
        if response.status_code == 200:
            data = response.get_json()
            print('  ✅ API working - Status:', data.get('status'))
            print('  ✅ Companies:', len(data.get('companies_included', [])))
            print('  ✅ Articles:', data.get('total_articles'))
        else:
            print('  ❌ API failed with status:', response.status_code)
except Exception as e:
    print('  ❌ API test failed:', str(e))
"

# Check JSON file
echo -e "\n📋 Checking JSON file..."
if [ -f "daily_summary.json" ]; then
    file_size=$(wc -c < "daily_summary.json")
    echo "  ✅ daily_summary.json exists ($file_size bytes)"
    
    # Check if JSON is valid
    if python -c "import json; json.load(open('daily_summary.json'))" 2>/dev/null; then
        echo "  ✅ JSON is valid"
    else
        echo "  ❌ JSON is invalid"
    fi
else
    echo "  ❌ daily_summary.json not found"
fi

echo -e "\n🎯 Next Steps:"
echo "1. ✅ Code pushed to GitHub"
echo "2. ⏳ Add ANTHROPIC_API_KEY to GitHub secrets (see setup_github_secrets.md)"
echo "3. ⏳ Test GitHub Actions workflow manually"
echo "4. ⏳ Deploy to Vercel"
echo "5. ⏳ Update your Next.js website"

echo -e "\n📖 See ARCHITECTURE_SUMMARY.md for complete instructions"
echo "✨ Setup verification complete!"