# Deployment Guide - Bounty Recon AI

## Prerequisites

- AWS Account with CLI configured
- S3 bucket for static hosting
- CloudFront distribution (optional, for CDN)
- Domain name (optional)

## Quick Deploy to AWS S3

### 1. Build the Application

```bash
cd /home/ubuntu/.openclaw/workspace/bounty-recon-ai
./scripts/build.sh
```

### 2. Create S3 Bucket (First Time Only)

```bash
# Replace 'your-bucket-name' with your actual bucket name
aws s3 mb s3://bounty-recon-ai --region us-east-1

# Enable static website hosting
aws s3 website s3://bounty-recon-ai/ \
    --index-document index.html \
    --error-document 404.html

# Set bucket policy for public read access
aws s3api put-bucket-policy \
    --bucket bounty-recon-ai \
    --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::bounty-recon-ai/*"
  }]
}'
```

### 3. Deploy Static Files

```bash
# Sync frontend files to S3
aws s3 sync frontend/out/ s3://bounty-recon-ai/ \
    --delete \
    --cache-control "public, max-age=31536000, immutable" \
    --exclude "*.html" \
    --exclude "*.txt"

# Upload HTML files with shorter cache
aws s3 sync frontend/out/ s3://bounty-recon-ai/ \
    --cache-control "public, max-age=0, must-revalidate" \
    --exclude "*" \
    --include "*.html" \
    --include "*.txt"
```

Your site will be available at:
```
http://bounty-recon-ai.s3-website-us-east-1.amazonaws.com
```

### 4. (Optional) Set Up CloudFront CDN

```bash
# Create CloudFront distribution
aws cloudfront create-distribution \
    --origin-domain-name bounty-recon-ai.s3-website-us-east-1.amazonaws.com \
    --default-root-object index.html
```

## Deploy Backend API

### Option 1: AWS Lambda + API Gateway

```bash
cd backend

# Install dependencies in a layer
pip install -r requirements.txt -t python/lib/python3.11/site-packages/
zip -r lambda_layer.zip python

# Create Lambda layer
aws lambda publish-layer-version \
    --layer-name bounty-recon-deps \
    --zip-file fileb://lambda_layer.zip \
    --compatible-runtimes python3.11

# Deploy function
zip function.zip main.py
aws lambda create-function \
    --function-name bounty-recon-api \
    --runtime python3.11 \
    --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-role \
    --handler main.handler \
    --zip-file fileb://function.zip \
    --layers arn:aws:lambda:us-east-1:YOUR_ACCOUNT:layer:bounty-recon-deps:1
```

### Option 2: AWS ECS/Fargate

```bash
# Build Docker container
cd backend
docker build -t bounty-recon-api .

# Push to ECR and deploy (full ECS setup required)
```

### Option 3: Simple EC2/VPS

```bash
# SSH into server
cd /home/ubuntu/bounty-recon-ai/backend

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run with systemd or PM2
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Environment Configuration

### Frontend (.env.production)

```env
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX
NEXT_PUBLIC_ANALYTICS_ENABLED=true
```

### Backend (.env)

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
NOVA_ACT_ENDPOINT=https://nova-act.amazonaws.com
```

## Continuous Deployment

### GitHub Actions (Recommended)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Build Frontend
        run: |
          cd frontend
          npm ci
          npm run build
      
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Deploy to S3
        run: |
          aws s3 sync frontend/out/ s3://bounty-recon-ai/ --delete
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ secrets.CLOUDFRONT_ID }} \
            --paths "/*"
```

## Post-Deployment Checklist

- [ ] Verify frontend loads at your URL
- [ ] Test API endpoint connectivity
- [ ] Check analytics tracking (Google Analytics dashboard)
- [ ] Verify SSL certificate (if using CloudFront/custom domain)
- [ ] Test scan functionality end-to-end
- [ ] Review error logs
- [ ] Set up monitoring/alerts

## Rollback

If something goes wrong:

```bash
# List previous versions
aws s3api list-object-versions --bucket bounty-recon-ai

# Restore previous version (if versioning enabled)
aws s3api copy-object \
    --copy-source bounty-recon-ai/index.html?versionId=OLD_VERSION_ID \
    --bucket bounty-recon-ai \
    --key index.html
```

## Monitoring

### CloudWatch Logs

```bash
# Backend API logs
aws logs tail /aws/lambda/bounty-recon-api --follow

# Frontend CloudFront logs (if enabled)
aws logs tail /aws/cloudfront/bounty-recon-ai --follow
```

### Cost Monitoring

Estimated monthly costs:
- S3 hosting: ~$1-5
- CloudFront: ~$5-20 (depends on traffic)
- Lambda: ~$0-10 (generous free tier)

Total: **$10-35/month** for moderate traffic

## Support

For issues or questions:
- GitHub Issues: https://github.com/tufstraka/bounty-recon-ai/issues
- Email: keithkadima@gmail.com

---

**Built for Amazon Nova Hackathon 2026** | #AmazonNova
