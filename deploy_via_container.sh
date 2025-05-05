#!/bin/bash
# Script to deploy z-news application using a Docker container with Python 3.8

# Ensure script stops on first error
set -e

echo "🚀 Starting deployment via Docker container"

# Create temporary directory for deployment
TEMP_DIR=$(mktemp -d)
echo "📁 Created temporary directory: $TEMP_DIR"

# Copy required files to temp directory
echo "📋 Copying application files..."
cp -r app.py requirements-zappa.txt zappa_settings.json services config utils.py "$TEMP_DIR"
cd "$TEMP_DIR"

# Create Dockerfile
echo "🐳 Creating Dockerfile..."
cat > Dockerfile << 'EOF'
FROM python:3.8

WORKDIR /app

# Install Rust (needed for tokenizers)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements-zappa.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements-zappa.txt

# Copy application files
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Default command
CMD ["bash"]
EOF

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t z-news-deploy .

# Run zappa update inside the container (deploy first time, update if it exists)
echo "📦 Running Zappa deploy/update inside container..."
docker run --rm \
  -v ~/.aws:/root/.aws:ro \
  -e ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY}" \
  z-news-deploy \
  bash -c "python -m venv venv && source venv/bin/activate && pip install -r requirements-zappa.txt && zappa undeploy dev -y && zappa deploy dev"

echo "✅ Deployment completed!"
echo "🧹 Cleaning up temporary directory..."
cd -
rm -rf "$TEMP_DIR"

echo "🌐 Your application is now deployed!"
echo "Use 'zappa tail dev' to view logs (you may need to install zappa locally first)"