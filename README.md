<div align="center">

<img src="frontend/public/icon.svg" alt="SafeBite Logo" width="80" height="80">

# SafeBite

**AI-powered food safety, built for people who can't afford mistakes.**

Scan any food label. Detect allergens instantly. Know what's safe — before you eat it.

[![Live Demo](https://img.shields.io/badge/Live%20Demo-safebite.locsafe.org-black?style=for-the-badge)](https://safebite.locsafe.org)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)
[![Built with](https://img.shields.io/badge/Powered%20by-Amazon%20Nova-orange?style=for-the-badge)](https://aws.amazon.com/ai/)

</div>

---

## What is SafeBite?

SafeBite is an AI-powered food label scanner that helps people with dietary restrictions, allergies, and health conditions instantly understand what's in their food.

Point your camera at any food product. SafeBite reads the label, identifies allergens, cross-references ingredients, and tells you whether it's safe — in seconds.

**No more squinting at tiny print. No more guessing. No more risk.**

---

## Features

- **📸 Instant Label Scanning** — Point, scan, done. Works on any packaging.
- **🧠 AI Allergen Detection** — Identifies the 14 major allergens + custom restrictions
- **🔍 Cross-Reference Validation** — Catches hidden allergens in ingredient aliases and derivatives
- **🗣️ Voice Mode** — Audio readout via Amazon Nova Sonic for eyes-free use
- **🔎 Semantic Search** — Find products and ingredients using natural language
- **📊 Admin Dashboard** — Track usage, feedback, and safety incidents
- **⚡ Real-time Results** — Sub-second response times on standard hardware

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | FastAPI, Python 3.11 |
| OCR | AWS Textract |
| AI Reasoning | Amazon Nova 2 Lite |
| Voice | Amazon Nova Sonic |
| Embeddings | Amazon Nova Embeddings |
| Reverse Proxy | Caddy |
| Process Manager | PM2 |
| Hosting | AWS EC2 |

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- AWS account with access to Bedrock + Textract

### Clone & Install

```bash
git clone https://github.com/tufstraka/safebite.git
cd safebite
```

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### Environment Variables

**Backend** — copy `backend/.env.example` to `backend/.env`:

```env
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_DEFAULT_REGION=us-east-1
```

**Frontend** — copy `frontend/.env.example` to `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Run Locally

```bash
# Backend
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Frontend (separate terminal)
cd frontend && npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

---

## Deployment

SafeBite runs on a single EC2 instance managed by PM2 and Caddy.

### Services

| PM2 Process | Description | Port |
|---|---|---|
| `safebite-backend` | FastAPI + Uvicorn | 8000 |
| `safebite-frontend` | Next.js static (python http.server) | 3000 |
| `safebite-caddy` | HTTPS reverse proxy | 80/443 |
| `safebite-webhook` | GitHub deploy webhook | 9000 |

### Auto-Deploy

Every push to `main` triggers an automatic deployment:

```
git push origin main
  → GitHub Actions
  → POST /webhook (HMAC-signed)
  → Caddy → webhook server
  → git pull + npm build + pm2 restart
```

To deploy manually on the server:

```bash
/opt/safebite/deploy.sh
```

---

## API Reference

### Health Check
```
GET /health
```
```json
{
  "name": "SafeBite AI API (Nova Powered)",
  "version": "2.0.0",
  "status": "operational"
}
```

### Scan a Food Label
```
POST /analyze
Content-Type: multipart/form-data

image: <file>
```

### Feedback
```
POST /feedback
GET  /feedbacks
```

Full API docs available at `/docs` when running locally.

---

## Project Structure

```
safebite/
├── backend/
│   ├── main.py                  # FastAPI app + routes
│   ├── safebite_agent.py        # Core AI agent
│   ├── nova_lite_reasoner.py    # Allergen reasoning (Amazon Nova)
│   ├── nova_textract_ocr.py     # Label OCR (AWS Textract)
│   ├── nova_sonic_voice.py      # Voice output
│   ├── nova_embeddings.py       # Semantic search
│   ├── admin_routes.py          # Admin endpoints
│   └── database.py              # Feedback storage
├── frontend/
│   └── app/
│       ├── page.tsx             # Main scanner UI
│       ├── admin/               # Admin dashboard
│       └── feedbacks/           # Feedback view
├── caddy/
│   └── Caddyfile                # Reverse proxy config
├── deploy.sh                    # Deploy script
├── webhook_server.py            # Auto-deploy webhook
└── ecosystem.config.js          # PM2 process config
```

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-feature`
3. Commit your changes: `git commit -m 'feat: add your feature'`
4. Push and open a Pull Request

Please keep commits conventional (`feat:`, `fix:`, `docs:`, `ci:`).

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">

Built with ❤️ using Amazon Nova & AWS

**[safebite.locsafe.org](https://safebite.locsafe.org)**

</div>
