# SafeBite AI - Development & Deployment Guide

## Overview

SafeBite AI is an AI-powered menu safety scanner that uses AWS Textract for OCR and Amazon Nova 2 Lite for allergen reasoning.

## Project Structure

```
bounty-recon-ai/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── admin_routes.py         # Admin analytics endpoints
│   ├── database.py             # SQLAlchemy models
│   ├── nova_textract_ocr.py    # AWS Textract OCR
│   ├── nova_lite_reasoner.py   # Nova 2 Lite AI reasoning
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment template
│   └── bounty-recon-api.service # SystemD service file
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Main application
│   │   ├── layout.tsx          # App layout
│   │   ├── admin/page.tsx      # Admin dashboard
│   │   └── components/         # React components
│   ├── package.json            # Node dependencies
│   └── .env.example            # Environment template
├── nginx.conf                  # Nginx configuration
└── README.md                   # Project overview
```

---

## Local Development

### Prerequisites

- Python 3.11+
- Node.js 18+
- AWS Account with Bedrock access
- AWS CLI configured

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your AWS credentials
# AWS_REGION=us-east-1
# AWS_ACCESS_KEY_ID=your_key
# AWS_SECRET_ACCESS_KEY=your_secret

# Run the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### Testing the Application

1. Open `http://localhost:3000` in your browser
2. Select your allergens (e.g., Peanuts, Milk)
3. Upload a menu image (JPG, PNG) or PDF
4. Click "Scan Menu"
5. View the color-coded results:
   - 🟢 Green: Safe dishes
   - 🟡 Yellow: Caution (verify with staff)
   - 🔴 Red: Unsafe (contains allergens)

---

## EC2 Deployment

### Prerequisites

- AWS EC2 instance (Ubuntu 22.04 recommended)
- Security group with ports 22, 80, 443 open
- Domain name (optional, for HTTPS)

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
# Press Ctrl+C to stop
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

## Nginx Configuration Reference

```nginx
server {
    listen 80;
    server_name _;

    # Frontend
    root /var/www/html;
    index index.html;

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
        proxy_read_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
    }
}
```

---

## Environment Variables

### Backend (.env)

```env
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

### Frontend (.env.production)

```env
NEXT_PUBLIC_API_URL=/api
```

---

## Troubleshooting

### Backend Issues

```bash
# Check service status
sudo systemctl status bounty-recon-api

# View logs
sudo journalctl -u bounty-recon-api -n 100

# Restart service
sudo systemctl restart bounty-recon-api

# Check port usage
sudo lsof -i :8000
```

### Frontend Issues

```bash
# Check Nginx status
sudo systemctl status nginx

# View Nginx logs
sudo tail -f /var/log/nginx/error.log

# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### AWS Credentials Issues

```bash
# Test AWS credentials
aws sts get-caller-identity

# Test Bedrock access
aws bedrock list-foundation-models --region us-east-1
```

---

## Updating the Application

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

---

## Optional: HTTPS with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate (replace with your domain)
sudo certbot --nginx -d yourdomain.com

# Auto-renewal is configured automatically
```

---

## Support

- **Repository**: https://github.com/tufstraka/bounty-recon-ai
- **Issues**: https://github.com/tufstraka/bounty-recon-ai/issues
