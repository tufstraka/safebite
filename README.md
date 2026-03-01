# SafeBite AI

AI-Powered Restaurant Menu Safety Scanner for Food Allergies

**Built for:** Amazon Nova Hackathon 2026  
**Category:** Multimodal Understanding  
**Prize:** $3,000 + $5,000 AWS Credits

## The Problem

32 million Americans have food allergies. Restaurant menus don't list ingredients clearly. Calling restaurants doesn't help - staff don't know exact ingredients. **One wrong dish can be life-threatening.**

## The Solution

Upload a menu photo or URL. Select your allergies. Get instant dish-by-dish safety analysis with confidence scores.

## Technology Stack

### Full Amazon Nova Integration:

**Nova Pro (Multimodal Understanding)**
- OCR menu images
- Understands dish descriptions
- Extracts ingredient lists

**Nova 2 Lite (Fast Reasoning)**
- Infers ingredients from dish names
- Assesses allergen risk
- Calculates confidence scores

**Nova Act (UI Automation)**
- Scrapes restaurant websites
- Finds allergen information
- Navigates menu pages

**Nova 2 Sonic (Voice AI)**
- Audio recommendations
- Voice-guided menu navigation
- Real-time safety alerts

**Nova Embeddings**
- Matches dishes to allergen database
- Learns cuisine-specific patterns
- Cross-references ingredient combinations

## Features

- Photo or URL menu upload
- 14 common allergens tracked
- Dish-by-dish safety scores
- Ingredient inference AI
- Voice recommendations
- Multi-language support
- Restaurant database learning

## Use Cases

- Dining out with allergies
- Family meal planning
- Travel food safety
- Severe allergy management
- Cross-contamination awareness

## Quick Start

### Backend
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add AWS credentials
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run build
```

## Live Demo

**URL:** http://44.207.1.126/

## Architecture

```
Menu Upload → Nova Pro → Dish Analysis → Nova 2 Lite
    ↓              ↓            ↓              ↓
Nova Act    Allergen DB   Safety Score   Recommendations
```

## Safety Score Algorithm

- **Safe (90-100%):** No detected allergens
- **Likely Safe (70-89%):** Low risk ingredients
- **Unknown (40-69%):** Insufficient information
- **Caution (20-39%):** Possible allergen presence
- **Unsafe (0-19%):** Confirmed allergens

## Market

- 32M Americans with food allergies
- 200M+ people with dietary restrictions
- Growing awareness of cross-contamination
- International travelers with allergies

## Monetization

- Free: 5 scans/month
- Premium: $4.99/month unlimited
- Enterprise: Custom pricing for restaurant chains

## Technical Implementation

- FastAPI backend with async processing
- Next.js 14 frontend with SSG
- Real-time allergen analysis
- Confidence-based recommendations
- Multi-model orchestration

## Why This Wins

1. **Life-saving application** - Real health impact
2. **Unsolved problem** - No good solution exists
3. **Full Nova stack** - Uses all 5 models
4. **Clear value** - Safety = willingness to pay
5. **Scalable** - Global food allergy market
6. **Demo-friendly** - Visual, immediate results

## Privacy

- No data stored without consent
- Local processing when possible
- HIPAA-aware design
- User-controlled data deletion

## Future Roadmap

- Restaurant partnerships
- Crowd-sourced allergen data
- Wearable device integration
- Multi-language expansion
- API for other apps

## License

MIT

## Author

Keith Kadima ([@tufstraka](https://github.com/tufstraka))

**Built with Amazon Nova** - Multimodal Understanding, Voice AI, and UI Automation
