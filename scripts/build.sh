#!/bin/bash
# Build script for Bounty Recon AI

set -e

echo "🔨 Building Bounty Recon AI..."

# Build frontend
echo "📦 Building frontend..."
cd frontend
npm install
npm run build
cd ..

echo "✅ Build complete!"
echo "📂 Frontend static files in: frontend/out"
