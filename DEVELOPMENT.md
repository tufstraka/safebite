# SafeBite AI - Development & Deployment Guide 🛠️

## 📋 Table of Contents

- [Overview](#overview)
- [Project Structure](#-project-structure)
- [Architecture](#-architecture)
- [Local Development](#-local-development)
- [EC2 Deployment](#-ec2-deployment)
- [Configuration Reference](#-configuration-reference)
- [API Reference](#-api-reference)
- [Troubleshooting](#-troubleshooting)
- [Updating the Application](#-updating-the-application)
- [Security Best Practices](#-security-best-practices)
- [Performance Optimization](#-performance-optimization)
- [Future Development Phases](#-future-development-phases)
- [Support](#-support)

---

## Overview

SafeBite AI is an AI-powered menu safety scanner that uses **AWS Textract** for OCR and **Amazon Nova 2 Lite** for allergen reasoning. This guide covers everything you need to develop, deploy, and maintain the application.

### Key Technologies

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | FastAPI (Python 3.11+) | REST API server |
| **Frontend** | Next.js 14 (React) | User interface |
| **OCR** | AWS Textract | Menu text extraction |
| **AI Reasoning** | Amazon Nova 2 Lite | Ingredient inference |
| **Voice** | Nova 2 Sonic / Polly | Audio summaries |
| **Embeddings** | Amazon Titan | Semantic matching |
| **Deployment** | Nginx + SystemD | Production hosting |

---

## 📁 Project Structure

```
bounty-recon-ai/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── admin_routes.py            # Admin analytics endpoints
│   ├── database.py                # SQLAlchemy models & database config
│   ├── nova_textract_ocr.py       # AWS Textract OCR integration
│   ├── nova_lite_reasoner.py      # Nova 2 Lite AI reasoning engine
│   ├── nova_sonic_voice.py        # Nova 2 Sonic voice synthesis
│   ├── nova_embeddings.py         # Titan embeddings for semantic search
│   ├── safebite_agent.py          # Agentic AI for multi-step reasoning
│   ├── requirements.txt           # Python dependencies
│   ├── requirements_nova.txt      # Nova-specific dependencies
│   ├── .env.example               # Environment template
│   ├── bounty-recon-api.service   # SystemD service file
│   ├── deploy_nova.sh             # Nova deployment script
│   └── feedback_data/             # User feedback storage
│       └── *.json                 # Feedback JSON files
├── frontend/
│   ├── app/
│   │   ├── page.tsx               # Main application page
│   │   ├── layout.tsx             # App layout & metadata
│   │   ├── globals.css            # Global styles
│   │   ├── metadata.ts            # SEO metadata
│   │   ├── admin/
│   │   │   └── page.tsx           # Admin dashboard
│   │   ├── feedbacks/
│   │   │   └── page.tsx           # Feedback viewer
│   │   └── components/
│   │       ├── AuthGuard.tsx      # Authentication wrapper
│   │       ├── CameraView.tsx     # Camera capture component
│   │       ├── FeedbackForm.tsx   # User feedback form
│   │       ├── Toast.tsx          # Notification toasts
│   │       └── ConsoleEasterEgg.tsx # Easter egg component
│   ├── public/
│   │   ├── manifest.json          # PWA manifest
│   │   ├── sw.js                  # Service worker
│   │   ├── favicon.svg            # App favicon
│   │   └── robots.txt             # SEO robots file
│   ├── package.json               # Node dependencies
│   ├── tailwind.config.ts         # Tailwind CSS config
│   ├── next.config.js             # Next.js configuration
│   └── .env.example               # Environment template
├── scripts/
│   ├── build.sh                   # Build script
│   └── deploy.sh                  # Deployment script
├── .github/                       # GitHub Actions workflows
├── nginx.conf                     # Nginx configuration
├── deploy.sh                      # Main deployment script
├── webhook_server.py              # Webhook handler
├── README.md                      # Project overview
├── DEVELOPMENT.md                 # This file
└── LICENSE                        # MIT License
```

---

## 🏗️ Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              SafeBite AI Architecture                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────────────────────┐   │
│  │   Browser   │────▶│   Nginx     │────▶│      Next.js Frontend       │   │
│  │   Client    │     │   (Port 80) │     │      (Static Export)        │   │
│  └─────────────┘     └──────┬──────┘     └─────────────────────────────┘   │
│                             │                                                │
│                             │ /api/*                                         │
│                             ▼                                                │
│                      ┌─────────────┐                                         │
│                      │   FastAPI   │                                         │
│                      │  (Port 8000)│                                         │
│                      └──────┬──────┘                                         │
│                             │                                                │
│         ┌───────────────────┼───────────────────┐                           │
│         ▼                   ▼                   ▼                            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                    │
│  │   Textract  │     │ Nova 2 Lite │     │ Nova Sonic  │                    │
│  │    (OCR)    │     │ (Reasoning) │     │  (Voice)    │                    │
│  └─────────────┘     └─────────────┘     └─────────────┘                    │
│         │                   │                   │                            │
│         └───────────────────┴───────────────────┘                           │
│                             │                                                │
│                      ┌──────▼──────┐                                         │
│                      │ AWS Bedrock │                                         │
│                      │  (us-east-1)│                                         │
│                      └─────────────┘                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Upload  │───▶│   OCR    │───▶│  Parse   │───▶│  Infer   │───▶│  Assess  │
│  Menu    │    │ Textract │    │  Dishes  │    │ Ingreds  │    │  Safety  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
                                                                      │
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│  Return  │◀───│  Voice   │◀───│  Format  │◀───│  Score   │◀────────┘
│  Results │    │ Summary  │    │  Output  │    │  Dishes  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘
```

---

## 💻 Local Development

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 18+ | Frontend build |
| AWS CLI | 2.x | AWS authentication |
| Git | 2.x | Version control |

### Backend Setup

```bash
# 1. Navigate to backend directory
cd backend

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Create environment file
cp .env.example .env

# 6. Edit .env with your AWS credentials
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret

# 7. Run the development server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Verify Backend:**
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- OpenAPI Schema: http://localhost:8000/openapi.json

### Frontend Setup

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies
npm install

# 3. Create environment file
cp .env.example .env.local

# 4. Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# 5. Run development server
npm run dev
```

**Verify Frontend:**
- Application: http://localhost:3000
- Admin Dashboard: http://localhost:3000/admin

### Testing the Application

1. Open http://localhost:3000 in your browser
2. Select your allergens (e.g., Peanuts, Milk)
3. Upload a menu image (JPG, PNG) or PDF
4. Click "Scan Menu"
5. View the color-coded results:
   - 🟢 **Green:** Safe dishes
   - 🟡 **Yellow:** Caution (verify with staff)
   - 🔴 **Red:** Unsafe (contains allergens)

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm run test

# E2E tests
npm run test:e2e
```

---

## 🚀 EC2 Deployment

### Prerequisites

- AWS EC2 instance (Ubuntu 22.04 LTS recommended)
- Security group with ports 22, 80, 443 open
- Domain name (optional, for HTTPS)
- SSH key pair

### Step 1: Connect to EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### Step 2: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install nodejs -y

# Install Nginx
sudo apt install nginx -y

# Install additional tools
sudo apt install git curl wget -y
```

### Step 3: Clone Repository

```bash
cd /home/ubuntu
git clone https://github.com/tufstraka/bounty-recon-ai.git
cd bounty-recon-ai
```

### Step 4: Setup Backend

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
nano .env  # Add your AWS credentials

# Test the backend
uvicorn main:app --host 0.0.0.0 --port 8000
# Press Ctrl+C to stop after verifying
```

### Step 5: Setup SystemD Service

```bash
# Copy service file
sudo cp bounty-recon-api.service /etc/systemd/system/

# Edit service file if needed
sudo nano /etc/systemd/system/bounty-recon-api.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable bounty-recon-api
sudo systemctl start bounty-recon-api

# Check status
sudo systemctl status bounty-recon-api
```

### Step 6: Build Frontend

```bash
cd ../frontend

# Install dependencies
npm install

# Create production environment
cp .env.example .env.production
nano .env.production
# Set: NEXT_PUBLIC_API_URL=/api

# Build for production
npm run build

# Deploy to Nginx
sudo rm -rf /var/www/html/*
sudo cp -r out/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html
```

### Step 7: Configure Nginx

```bash
# Copy nginx config
sudo cp ../nginx.conf /etc/nginx/sites-available/default

# Test configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Step 8: Verify Deployment

```bash
# Test frontend
curl http://localhost/

# Test API
curl http://localhost/health

# View logs
sudo journalctl -u bounty-recon-api -f
```

---

## ⚙️ Configuration Reference

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name _;

    # Frontend - Static files
    root /var/www/html;
    index index.html;

    # Handle client-side routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API Proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        
        # File upload settings
        client_max_body_size 50M;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }

    # WebSocket support (for future features)
    location /ws {
        proxy_pass http://127.0.0.1:8000/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Environment Variables

#### Backend (.env)

```env
# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key

# Application Settings
DEBUG=false
LOG_LEVEL=INFO
MAX_FILE_SIZE=52428800  # 50MB

# Database (optional)
DATABASE_URL=sqlite:///./safebite.db

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60
```

#### Frontend (.env.production)

```env
NEXT_PUBLIC_API_URL=/api
NEXT_PUBLIC_APP_NAME=SafeBite AI
NEXT_PUBLIC_GA_ID=G-XXXXXXXXXX  # Optional: Google Analytics
```

### SystemD Service Configuration

```ini
[Unit]
Description=SafeBite AI API
After=network.target

[Service]
Type=simple
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/bounty-recon-ai/backend
Environment="PATH=/home/ubuntu/bounty-recon-ai/backend/venv/bin"
ExecStart=/home/ubuntu/bounty-recon-ai/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## 📖 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/allergens` | List supported allergens |
| POST | `/analyze/image` | Analyze menu image/PDF |
| POST | `/analyze/agentic` | Agentic AI analysis |
| GET | `/admin/stats` | Admin statistics |

### Request/Response Examples

#### Health Check
```bash
curl http://localhost:8000/health
```
```json
{
  "name": "SafeBite AI API",
  "version": "1.0.0",
  "status": "operational",
  "powered_by": "Amazon Nova"
}
```

#### Analyze Menu
```bash
curl -X POST http://localhost:8000/analyze/image \
  -F "file=@menu.jpg" \
  -F "allergens=peanuts,milk" \
  -F "custom_allergens=msg"
```

---

## 🔧 Troubleshooting

### Backend Issues

| Issue | Solution |
|-------|----------|
| Service won't start | Check logs: `sudo journalctl -u bounty-recon-api -n 100` |
| Port already in use | Find process: `sudo lsof -i :8000` and kill it |
| AWS credentials error | Verify: `aws sts get-caller-identity` |
| Module not found | Reinstall: `pip install -r requirements.txt` |

```bash
# Useful commands
sudo systemctl status bounty-recon-api
sudo systemctl restart bounty-recon-api
sudo journalctl -u bounty-recon-api -f
```

### Frontend Issues

| Issue | Solution |
|-------|----------|
| Build fails | Clear cache: `rm -rf .next node_modules && npm install` |
| API not connecting | Check NEXT_PUBLIC_API_URL in .env |
| Static files not loading | Verify Nginx root path |

```bash
# Useful commands
sudo systemctl status nginx
sudo nginx -t
sudo tail -f /var/log/nginx/error.log
```

### AWS Issues

```bash
# Test AWS credentials
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1

# Test Textract
aws textract detect-document-text --document '{"S3Object":{"Bucket":"bucket","Name":"file.jpg"}}'
```

---

## 🔄 Updating the Application

### Backend Update

```bash
cd /home/ubuntu/bounty-recon-ai
git pull origin main
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bounty-recon-api
```

### Frontend Update

```bash
cd /home/ubuntu/bounty-recon-ai
git pull origin main
cd frontend
npm install
npm run build
sudo rm -rf /var/www/html/*
sudo cp -r out/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html
```

### Full Update Script

```bash
#!/bin/bash
# update.sh - Full application update

set -e

echo "Pulling latest changes..."
cd /home/ubuntu/bounty-recon-ai
git pull origin main

echo "Updating backend..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart bounty-recon-api

echo "Updating frontend..."
cd ../frontend
npm install
npm run build
sudo rm -rf /var/www/html/*
sudo cp -r out/* /var/www/html/
sudo chown -R www-data:www-data /var/www/html

echo "Update complete!"
```

---

## 🔒 Security Best Practices

### AWS Credentials

- ✅ Use IAM roles for EC2 instances (preferred)
- ✅ Use environment variables, never commit credentials
- ✅ Rotate access keys regularly
- ✅ Use least-privilege IAM policies

### Application Security

- ✅ Enable HTTPS with Let's Encrypt
- ✅ Set up rate limiting
- ✅ Validate all file uploads
- ✅ Sanitize user inputs
- ✅ Keep dependencies updated

### HTTPS Setup with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

---

## ⚡ Performance Optimization

### Backend Optimization

```python
# Use connection pooling for database
from sqlalchemy.pool import QueuePool
engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=5)

# Cache frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=100)
def get_allergen_keywords(allergen: str):
    return ALLERGEN_KEYWORDS.get(allergen, [])
```

### Frontend Optimization

```javascript
// next.config.js
module.exports = {
  images: {
    domains: ['your-cdn.com'],
  },
  compress: true,
  poweredByHeader: false,
}
```

### Nginx Optimization

```nginx
# Enable gzip compression
gzip on;
gzip_types text/plain text/css application/json application/javascript;
gzip_min_length 1000;

# Enable caching for static files
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 🔮 Future Development Phases

### Phase 3: Restaurant Collaboration (Q2-Q4 2026)

The next major phase focuses on partnering directly with restaurants for verified allergen data.

#### Technical Requirements

```python
# New API endpoints for restaurant partners
POST /api/v2/restaurant/register      # Restaurant registration
POST /api/v2/restaurant/menu          # Upload/update menu
GET  /api/v2/restaurant/analytics     # View analytics
POST /api/v2/restaurant/verify        # Request verification

# Database schema additions
class Restaurant(Base):
    __tablename__ = "restaurants"
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    verified = Column(Boolean, default=False)
    tier = Column(String, default="basic")  # basic, verified, premium
    
class VerifiedDish(Base):
    __tablename__ = "verified_dishes"
    id = Column(String, primary_key=True)
    restaurant_id = Column(String, ForeignKey("restaurants.id"))
    name = Column(String, nullable=False)
    ingredients = Column(JSON)
    allergens = Column(JSON)
    cross_contamination = Column(JSON)
    last_updated = Column(DateTime)
```

#### Integration Points

| Integration | Purpose | Priority |
|-------------|---------|----------|
| **POS Systems** | Square, Toast, Clover | High |
| **Menu Platforms** | Yelp, Google, DoorDash | Medium |
| **Inventory Systems** | Track ingredient changes | Medium |
| **Allergy Databases** | FARE, AllergyEats | High |

#### Restaurant Dashboard Features

1. **Menu Management**
   - Drag-and-drop dish editor
   - Ingredient autocomplete
   - Allergen tagging
   - Cross-contamination warnings

2. **Analytics Dashboard**
   - Most searched dishes
   - Allergen query trends
   - Customer demographics
   - Safety score tracking

3. **Verification System**
   - Document upload (recipes, supplier info)
   - Staff training verification
   - Kitchen inspection records
   - Annual re-verification

### Phase 4: Advanced Features (2027)

| Feature | Description | Technology |
|---------|-------------|------------|
| **Nova Act Scraping** | Automated menu collection | Nova Act (when available) |
| **User Accounts** | Save preferences, history | Cognito + DynamoDB |
| **Trend Analysis** | Allergen patterns | SageMaker |
| **Community Database** | User-contributed data | Crowdsourcing platform |

### Development Timeline

```
Q2 2026: Restaurant pilot (50 partners)
├── Partner onboarding system
├── Basic dashboard
└── Verification workflow

Q3 2026: Beta expansion (500 restaurants)
├── POS integrations
├── Mobile app launch
└── Analytics dashboard

Q4 2026: Public launch
├── 2,000+ restaurants
├── Full feature set
└── Marketing campaign

2027: Scale & innovate
├── National expansion
├── Nova Act integration
└── Community features
```

---

## 📞 Support

### Resources

| Resource | Link |
|----------|------|
| **Repository** | https://github.com/tufstraka/bounty-recon-ai |
| **Issues** | https://github.com/tufstraka/bounty-recon-ai/issues |
| **Documentation** | This file |
| **API Docs** | http://localhost:8000/docs |

### Getting Help

1. Check the [Troubleshooting](#-troubleshooting) section
2. Search existing [GitHub Issues](https://github.com/tufstraka/bounty-recon-ai/issues)
3. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - Relevant logs

---

## 📝 Changelog

### v3.0.0 (March 2026)
- Added Nova 2 Sonic voice summaries
- Added Titan Embeddings semantic matching
- Added SafeBite Agentic AI
- Improved documentation

### v2.0.0 (February 2026)
- Migrated to AWS Textract for OCR
- Added Nova 2 Lite reasoning
- Added custom allergen support
- Improved UI/UX

### v1.0.0 (January 2026)
- Initial release
- Basic menu scanning
- 14 common allergens

---

**Last Updated:** March 13, 2026
