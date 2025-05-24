#!/bin/bash
# Script to view logs from the deployed Lambda function

# Ensure script stops on first error
set -e

echo "📜 Retrieving Zappa logs for z-news application..."

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
docker build -t z-news-logs .

# Run zappa tail inside the container
echo "📜 Getting logs (press Ctrl+C to exit)..."
docker run --rm -it \
  -v ~/.aws:/root/.aws:ro \
  z-news-logs \
  bash -c "zappa tail dev"

echo "✅ Completed!"
echo "🧹 Cleaning up temporary directory..."
cd -
rm -rf "$TEMP_DIR"