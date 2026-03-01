# Bounty Recon AI

> AI-Powered Bug Bounty Reconnaissance Platform using Amazon Nova Act

Built for Amazon Nova Hackathon 2026 | Category: UI Automation

## What Makes This Different

This isn't just another vulnerability scanner. We provide **professional-grade reconnaissance reports** that bug bounty hunters can submit directly to programs - with unique features that existing tools don't offer.

### Unique Value Propositions

#### 1. Zero False Positives from 404s
Most scanners report every endpoint they test. **We verify each endpoint with HTTP requests** before reporting - eliminating false positives that waste researchers' time.

#### 2. Real-World Security Implications
Not just "missing Content-Security-Policy header." We explain:
- What attackers can actually do (XSS injection, data theft, session hijacking)
- Real attack scenarios for each vulnerability
- Business impact of exploitation

#### 3. Actionable Remediation Steps
Every finding includes:
- Specific configuration examples
- Step-by-step implementation guide
- Best practices from security experts
- Code snippets when applicable

#### 4. Active Security Testing
We don't just read headers - we actively test:
- **CORS**: Send requests from malicious origins to prove misconfiguration
- **Rate Limiting**: Send 20 rapid requests to verify absence
- **Cookies**: Analyze individual security attributes
- **SSL/TLS**: Validate protocols and cipher strength

#### 5. Professional Bug Bounty Reports
One-click PDF export with everything security programs require:
- Executive summary with risk assessment
- CVSS scores for severity
- Detailed findings with evidence
- Methodology documentation
- Responsible disclosure language

## Comprehensive Security Analysis

### 8 Advanced Vulnerability Checks

1. **SSL/TLS Configuration**
   - Protocol version analysis (TLS 1.0/1.1/1.2/1.3)
   - Cipher suite strength
   - Certificate validation
   - HTTPS enforcement

2. **Cookie Security**
   - Secure flag (HTTPS-only)
   - HttpOnly flag (XSS protection)
   - SameSite attribute (CSRF prevention)
   - Per-cookie analysis

3. **CORS Misconfiguration**
   - Wildcard origin detection
   - Reflected origin testing
   - Credentials exposure
   - Active exploitation attempts

4. **Technology Fingerprinting**
   - Server identification
   - Framework detection
   - CMS discovery
   - Version information

5. **Information Disclosure**
   - Error message exposure
   - Stack trace detection
   - Sensitive comments
   - Directory listings

6. **Rate Limiting**
   - Brute force susceptibility
   - DoS vulnerability
   - API abuse potential
   - Active burst testing

7. **Security Headers**
   - Content-Security-Policy
   - Strict-Transport-Security
   - X-Frame-Options
   - Permissions-Policy
   - Referrer-Policy
   - X-Content-Type-Options

8. **Endpoint Discovery**
   - API endpoints (versioned)
   - Admin panels
   - Sensitive files (.git, .env)
   - Configuration files
   - robots.txt analysis

## Comparison to Existing Tools

| Feature | Bounty Recon AI | Burp Suite | OWASP ZAP | Nuclei | Qualys |
|---------|----------------|------------|-----------|--------|--------|
| Endpoint Verification | Yes | Manual | Manual | No | Limited |
| Active CORS Testing | Yes | Manual | Manual | No | No |
| Rate Limiting Test | Yes | Manual | Manual | No | No |
| Cookie Analysis | Per-cookie | Basic | Basic | No | Basic |
| SSL/TLS Analysis | Complete | Plugin | Plugin | No | Yes |
| Tech Detection | Multi-source | Manual | Manual | Templates | Limited |
| Information Disclosure | Pattern-based | Manual | Manual | Templates | Basic |
| CVSS Scoring | Yes | Commercial | No | No | Yes |
| Implications Explained | Detailed | No | No | No | Generic |
| Remediation Steps | Actionable | Generic | Generic | No | Generic |
| PDF Reports | Professional | Commercial | Manual | No | Yes |
| No 404 False Positives | Yes | Manual | No | No | Manual |

**Result:** Save hours of manual testing while improving report quality and acceptance rates.

## Technology Stack

### Frontend
- Next.js 14 (React)
- TypeScript
- Tailwind CSS
- Modern, responsive design

### Backend
- FastAPI (Python)
- Amazon Nova Act (AI-powered UI automation)
- Amazon Bedrock
- Async/await for performance
- ReportLab (PDF generation)

### Security
- httpx for HTTP verification
- SSL/TLS analysis
- Pattern matching for disclosure detection
- Security knowledge base

## Quick Start

### Prerequisites
- AWS Account with Bedrock access
- Python 3.12+
- Node.js 18+

### Installation

```bash
# Clone repository
git clone https://github.com/tufstraka/bounty-recon-ai.git
cd bounty-recon-ai

# Backend setup
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure AWS credentials
cp .env.example .env
# Add your AWS credentials to .env

# Frontend setup
cd ../frontend
npm install
npm run build

# Start services (production)
# Backend: systemd service
# Frontend: nginx serving static files
```

### Configuration

Add your AWS credentials to `backend/.env`:

```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
BEDROCK_MODEL_ID=amazon.nova-act-v1:0
```

See `docs/NOVA_ACT_SETUP.md` for detailed AWS setup instructions.

## Usage

1. Navigate to the application
2. Enter target URL
3. Click "Start Recon"
4. Wait for comprehensive analysis
5. Review findings with implications and recommendations
6. Export professional PDF report

## Features in Detail

### Executive Summary
Automatic risk assessment based on findings severity. Critical vulnerabilities highlighted immediately.

### Statistics Dashboard
Visual overview of findings by severity:
- Critical (CVSS 9.0+)
- High (CVSS 7.0-8.9)
- Medium (CVSS 4.0-6.9)
- Low (CVSS 0.1-3.9)
- Info (no CVSS)

### Detailed Findings
Each finding includes:
- Title and severity
- CVSS score
- Description
- Security implications (what can happen)
- Recommendations (how to fix)
- Evidence (proof of vulnerability)
- Category and timestamp

### PDF Export
Professional report with:
- Title page with metadata
- Executive summary
- Risk overview table
- Sorted findings (Critical -> Info)
- Conclusion and next steps
- Methodology documentation

## Architecture

```
┌─────────────────┐
│  Next.js        │
│  Frontend       │
│  (Static)       │
└────────┬────────┘
         │ HTTPS
         │
┌────────▼────────┐
│  Nginx          │
│  Reverse Proxy  │
└────────┬────────┘
         │
         │ /api/*
         │
┌────────▼────────┐
│  FastAPI        │
│  Backend API    │
│  (2 workers)    │
└────────┬────────┘
         │
         │
┌────────▼────────┐
│  Nova Act SDK   │
│  Reconnaissance │
│  Engine         │
└────────┬────────┘
         │
         │
┌────────▼────────┐
│  Amazon Bedrock │
│  Nova Act Model │
└─────────────────┘
```

## Documentation

- `FEATURES.md` - Comprehensive feature list and comparisons
- `docs/NOVA_ACT_SETUP.md` - AWS configuration guide
- `docs/DEPLOYMENT_STATUS.md` - Production deployment info
- `docs/PRODUCTION_DEPLOYMENT.md` - Deployment procedures
- `STATUS.md` - Quick health check script
- `FIXES_APPLIED.md` - Development history

## Demo Video

[Link to 3-minute demo video - TBD]

## Blog Post

[Link to builder.aws.com blog post - TBD]

## License

MIT License - See LICENSE file for details

## Hackathon Submission

**Amazon Nova Hackathon 2026**
- Category: UI Automation
- Prize Pool: $40,000 cash + $55,000 AWS credits
- Submission Date: 2026-03-01

## Author

Keith Kadima ([@tufstraka](https://github.com/tufstraka))
- LinkedIn: [kadimakeith](https://linkedin.com/in/kadimakeith)
- X: [@dobynog](https://x.com/dobynog)
- Website: [lumora.locsafe.org](https://lumora.locsafe.org)

## Acknowledgments

- Amazon Web Services for the Nova Act foundation model
- Amazon Bedrock team
- Bug bounty community for security insights

---

**Built with Amazon Nova Act | Amazon Nova Hackathon 2026**
