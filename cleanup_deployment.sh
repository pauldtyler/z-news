#!/bin/bash
# Script to clean up and undeploy the z-news application

# Ensure script stops on first error
set -e

echo "🧹 Starting cleanup of z-news deployment"

# Create a temporary directory for the cleanup
TEMP_DIR=$(mktemp -d)
echo "📁 Created temporary directory: $TEMP_DIR"

# Copy required files to temp directory
echo "📋 Copying configuration files..."
cp -r zappa_settings.json requirements-zappa.txt "$TEMP_DIR"
cd "$TEMP_DIR"

# Create Dockerfile
echo "🐳 Creating Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.8

WORKDIR /app

# Install dependencies
COPY requirements-zappa.txt .
RUN pip install zappa==0.56.1

# Copy configuration
COPY zappa_settings.json .

# Set environment variables
ENV PYTHONPATH=/app

# Default command
CMD ["bash"]
EOF

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t z-news-cleanup .

# Run zappa undeploy inside the container
echo "🗑️ Running Zappa undeploy inside container..."
docker run --rm \
  -v ~/.aws:/root/.aws:ro \
  z-news-cleanup \
  bash -c "python -m venv venv && source venv/bin/activate && pip install zappa && zappa undeploy dev -y"

echo "✅ Cleanup completed!"
echo "🧹 Cleaning up temporary directory..."
cd -
rm -rf "$TEMP_DIR"

echo "🌐 Your application has been undeployed!"