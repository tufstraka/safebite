#!/bin/bash
# Deployment script for AWS

set -e

echo "🚀 Deploying Bounty Recon AI..."

# Build the application
./scripts/build.sh

# Deploy to S3 (replace with your bucket name)
# aws s3 sync frontend/out s3://your-bucket-name --delete

# Invalidate CloudFront cache
# aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"

echo "✅ Deployment complete!"
