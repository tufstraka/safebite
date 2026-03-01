# Amazon Nova Act SDK Setup

## Prerequisites

1. AWS Account with Amazon Bedrock access
2. IAM user with permissions for:
   - bedrock:InvokeModel
   - bedrock:ListFoundationModels
3. AWS credentials configured

## Installation

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

1. Copy environment template:
```bash
cp .env.example .env
```

2. Add your AWS credentials to `.env`:
```
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
```

3. Verify Amazon Nova Act model access:
```bash
aws bedrock list-foundation-models \
  --by-provider amazon \
  --region us-east-1 \
  --query 'modelSummaries[?contains(modelId, `nova-act`)].modelId'
```

Expected output:
```json
[
    "amazon.nova-act-v1:0"
]
```

## IAM Policy

Create an IAM policy with these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": "arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-act-v1:0"
    }
  ]
}
```

## Testing SDK Integration

```bash
# Start backend locally
python main.py

# Test health endpoint
curl http://localhost:8000/

# Expected response:
{
  "name": "Bounty Recon AI API",
  "version": "1.0.0",
  "status": "operational",
  "powered_by": "Amazon Nova Act"
}
```

## SDK Architecture

### NovaActClient
- Wraps boto3 bedrock-runtime client
- Handles model invocation with Nova Act
- Implements prompt building for UI automation tasks

### NovaActAgent
- High-level interface for reconnaissance operations
- Methods:
  - `start_session()` - Initialize browser automation
  - `navigate_to(url)` - Navigate to target URL
  - `discover_endpoints(base_url)` - Crawl and discover endpoints
  - `check_security_headers(url)` - Analyze security headers
  - `capture_screenshot(url)` - Take page screenshot
  - `end_session()` - Cleanup resources

### Integration Points

1. **Backend API** (`main.py`)
   - Imports from `nova_act_sdk`
   - Uses NovaActAgent in ReconEngine
   - Orchestrates scan workflow

2. **Environment Config** (`.env`)
   - AWS credentials
   - Bedrock model ID
   - Region configuration

## Troubleshooting

### Error: "NoSuchModel"
- Verify Nova Act model availability in your AWS region
- Check IAM permissions for bedrock:InvokeModel

### Error: "AccessDenied"
- Verify AWS credentials are correct
- Check IAM policy includes bedrock:InvokeModel permission
- Ensure model ARN matches your region

### Error: "ThrottlingException"
- Implement exponential backoff
- Request quota increase in AWS Service Quotas console

## Production Deployment

1. Use IAM roles instead of access keys (EC2/ECS)
2. Enable CloudWatch logging
3. Set up AWS Secrets Manager for credentials
4. Configure VPC endpoints for Bedrock
5. Monitor API costs in AWS Cost Explorer

## References

- Amazon Bedrock Documentation: https://docs.aws.amazon.com/bedrock/
- Nova Act Model Card: https://aws.amazon.com/bedrock/nova/
- Boto3 Bedrock Runtime: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/bedrock-runtime.html
