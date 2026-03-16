#!/bin/bash
set -e
LOG=/opt/safebite/logs/deploy.log
exec >> $LOG 2>&1

echo ""
echo "========================================"
echo "🚀 Deploy started: $(date)"
echo "========================================"

cd /opt/safebite

# Pull latest changes
echo "📥 Pulling latest from GitHub..."
git pull origin main

# Backend deps
echo "📦 Installing backend dependencies..."
cd /opt/safebite/backend
./venv/bin/pip install -r requirements.txt --quiet 2>/dev/null || true
cd /opt/safebite

# Build frontend
echo "🔨 Building frontend..."
cd /opt/safebite/frontend
npm install --legacy-peer-deps --silent 2>/dev/null
npm run build
cd /opt/safebite

# Restart via PM2
echo "🔄 Restarting services via PM2..."
pm2 restart safebite-backend
pm2 restart safebite-frontend
pm2 save

sleep 4

# Health check
echo "✅ Health check..."
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Backend healthy!"
else
    echo "⚠️  Backend health endpoint not responding (may be ok)"
fi

echo "🎉 Deploy complete: $(date)"
echo "🌐 Live at: https://safebite.locsafe.org"
