#!/bin/bash

# Universal File Converter API Deployment Script
# Usage: ./deploy.sh [production|staging]

set -e

ENVIRONMENT=${1:-production}
APP_NAME="universal-converter-api"
DOCKER_IMAGE="universal-converter:latest"

echo "🚀 Deploying Universal File Converter API to $ENVIRONMENT environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p uploads converted logs

# Set permissions
chmod 755 uploads converted

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t $DOCKER_IMAGE .

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for health check
echo "⏳ Waiting for service to be healthy..."
for i in {1..30}; do
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo "✅ Service is healthy!"
        break
    fi
    echo "⏳ Waiting for service to start... ($i/30)"
    sleep 2
done

# Check if service is running
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "🎉 Deployment successful!"
    echo "📊 API is running at: http://localhost:8000"
    echo "📚 Documentation at: http://localhost:8000/docs"
    echo "💚 Health check at: http://localhost:8000/health"
else
    echo "❌ Deployment failed. Service is not responding."
    echo "📋 Checking logs..."
    docker-compose logs
    exit 1
fi

echo "🔧 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop service: docker-compose down"
echo "  Restart service: docker-compose restart"
echo "  Update: git pull && ./deploy.sh" 