#!/bin/bash
# Script to update the Zappa deployment with fixed dependencies

set -e  # Exit on error

echo "🔄 Updating Z-News API deployment..."

# First, store your API key in SSM Parameter Store (run once)
echo "📦 Storing API key in AWS Systems Manager Parameter Store..."
read -p "Enter your Anthropic API key (or press Enter to skip if already stored): " API_KEY

if [ ! -z "$API_KEY" ]; then
  aws ssm put-parameter \
    --name "/z-news/ANTHROPIC_API_KEY" \
    --value "$API_KEY" \
    --type SecureString \
    --overwrite
  echo "✅ API key stored in Parameter Store"
else
  echo "⏭️ Skipping API key storage"
fi

# Activate the virtual environment
echo "🔄 Activating virtual environment..."
source zappa-venv/bin/activate || {
  echo "❌ Failed to activate virtual environment. Make sure it exists."
  exit 1
}

# Install necessary packages
echo "📦 Installing required packages..."
pip install requests pandas anthropic python-dotenv flask==2.0.3 werkzeug==2.0.3 zappa==0.56.1

# Update the deployment
echo "🚀 Updating Zappa deployment..."
zappa update dev

# Get and display the API URL
echo "📋 Deployment complete. Your API URL is:"
API_INFO=$(zappa status dev)
API_URL=$(echo "$API_INFO" | grep "API Gateway URL" | grep -o 'https://[^"]*')

echo "✅ Your API URL is: $API_URL"
echo ""
echo "📝 Test your API with:"
echo "curl -X POST ${API_URL}/z-news \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"company_name\":\"Prudential Financial, Inc.\", \"time_filter\":\"w\", \"summary_type\":\"client\"}'"
echo ""
echo "Or test the healthcheck endpoint:"
echo "curl ${API_URL}/healthcheck"