#!/bin/bash
# SafeBite Auto-Deploy Script

set -e

echo "🚀 Starting SafeBite deployment..."

# Navigate to project directory
cd /home/ubuntu/.openclaw/workspace/price-intelligence-ai

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main

# Build frontend
echo "🔨 Building frontend..."
cd frontend
npm install --legacy-peer-deps > /dev/null 2>&1
npm run build

# Deploy frontend
echo "📦 Deploying frontend..."
sudo cp -r out/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html

# Restart backend
echo "🔄 Restarting backend API..."
sudo systemctl restart price-intelligence-api

# Wait for service to start
sleep 5

# Verify health
echo "✅ Verifying deployment..."
if curl -s http://localhost:8000/health | grep -q "operational"; then
    echo "✅ Backend healthy!"
else
    echo "❌ Backend health check failed!"
    exit 1
fi

# Check frontend
if curl -s http://localhost | grep -q "SafeBite"; then
    echo "✅ Frontend deployed!"
else
    echo "❌ Frontend check failed!"
    exit 1
fi

echo ""
echo "🎉 Deployment complete!"
echo "🌐 Live at: https://safebite.locsafe.org"
echo ""
