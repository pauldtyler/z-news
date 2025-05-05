#!/bin/bash
# Script to test the z-news API

# API URL
API_URL="https://c70o4akv4j.execute-api.us-east-1.amazonaws.com/dev"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Testing Z-News API${NC}"
echo "=================================="

# Test the healthcheck endpoint
echo -e "${YELLOW}Testing healthcheck endpoint...${NC}"
curl -s "${API_URL}/healthcheck"
echo -e "\n"

# Test the z-news endpoint with Prudential Financial
echo -e "${YELLOW}Testing z-news endpoint with Prudential Financial...${NC}"
echo "This may take 30-60 seconds as it searches for news and generates a summary..."
curl -s -X POST "${API_URL}/z-news" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Prudential Financial, Inc.",
    "time_filter": "w",
    "summary_type": "client"
  }'
echo -e "\n\n"

# Notify about completion
echo -e "${GREEN}Tests completed.${NC}"
echo "=================================="
echo "For more examples and documentation, see api_docs.md"