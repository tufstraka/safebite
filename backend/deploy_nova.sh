#!/bin/bash

# SafeBite AI - Deploy Nova Powered Backend
# This script updates the live backend with Textract + Nova 2 Lite integration

set -e

echo "🚀 Deploying SafeBite AI (Nova Powered)"
echo "========================================"

# Navigate to backend directory
cd /home/ubuntu/.openclaw/workspace/price-intelligence-ai/backend

# Backup current main.py
echo "📦 Backing up current backend..."
cp main.py main.py.backup.$(date +%Y%m%d_%H%M%S)

# Copy new Nova-powered files
echo "📝 Copying Nova components..."
cp /home/ubuntu/.openclaw/workspace/bounty-recon-ai/backend/nova_textract_ocr.py .
cp /home/ubuntu/.openclaw/workspace/bounty-recon-ai/backend/nova_lite_reasoner.py .
cp /home/ubuntu/.openclaw/workspace/bounty-recon-ai/backend/main_nova_complete.py main.py

# Install dependencies
echo "📦 Installing dependencies..."
source venv/bin/activate
pip install boto3 --upgrade

# Check AWS credentials
echo "🔑 Checking AWS credentials..."
if [ -z "$AWS_ACCESS_KEY_ID" ]; then
    echo "⚠️  AWS_ACCESS_KEY_ID not set in environment"
    echo "Please add to .env file:"
    echo "AWS_ACCESS_KEY_ID=your_key"
    echo "AWS_SECRET_ACCESS_KEY=your_secret"
    echo "AWS_DEFAULT_REGION=us-east-1"
fi

# Restart service
echo "🔄 Restarting SafeBite API service..."
sudo systemctl restart price-intelligence-api

# Wait for service to start
echo "⏳ Waiting for service to stabilize..."
sleep 5

# Check status
echo "📊 Service status:"
sudo systemctl status price-intelligence-api --no-pager | head -20

# Test health endpoint
echo ""
echo "🏥 Testing health endpoint..."
curl -s http://localhost:8000/health | jq .

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🎯 What changed:"
echo "  1. AWS Textract for OCR (replaces Nova Pro)"
echo "  2. Nova 2 Lite for allergen reasoning"
echo "  3. Color-coded menu formatting (green/yellow/red)"
echo "  4. Hidden ingredient detection"
echo ""
echo "📝 Live at: https://safebite.locsafe.org"
echo "🔗 API docs: http://localhost:8000/docs"
