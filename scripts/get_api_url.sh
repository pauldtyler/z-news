#!/bin/bash
# Script to get the API URL for the z-news application

# Ensure script stops on first error
set -e

echo "🔍 Retrieving API URL for z-news application..."

# Create temporary directory
TEMP_DIR=$(mktemp -d)
echo "📁 Created temporary directory: $TEMP_DIR"

# Copy zappa settings to temp directory
cp zappa_settings.json "$TEMP_DIR"
cd "$TEMP_DIR"

# Create Dockerfile
echo "🐳 Creating Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.8-slim

WORKDIR /app

# Install zappa
RUN pip install zappa==0.56.1

# Copy configuration
COPY zappa_settings.json .

# Default command
CMD ["bash"]
EOF

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t z-news-info .

# Run zappa status inside the container and capture the output
echo "🔍 Getting API information..."
API_INFO=$(docker run --rm \
  -v ~/.aws:/root/.aws:ro \
  z-news-info \
  bash -c "zappa status dev")

echo "$API_INFO"

# Extract the API URL from the output (the correct API Gateway URL)
API_URL=$(echo "$API_INFO" | grep "API Gateway URL" | grep -o 'https://[^"]*')

echo "✅ Completed!"
echo "🧹 Cleaning up temporary directory..."
cd -
rm -rf "$TEMP_DIR"

echo "📝 Test your API with:"
echo "curl -X POST ${API_URL}/z-news \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"company_name\":\"Prudential Financial, Inc.\", \"time_filter\":\"w\", \"summary_type\":\"client\"}'"
echo ""
echo "Or test the healthcheck endpoint:"
echo "curl ${API_URL}/healthcheck"