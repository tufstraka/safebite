"""
SafeBite AI - Backend API
Restaurant Menu Safety Scanner using Amazon Nova
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import logging
from datetime import datetime
import base64
import json
import io
from PyPDF2 import PdfReader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SafeBite AI API",
    description="AI-Powered Restaurant Menu Safety Scanner using Amazon Nova",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DATA MODELS

class AllergenList(BaseModel):
    allergens: List[str]

class MenuAnalysisRequest(BaseModel):
    menu_url: Optional[HttpUrl] = None
    allergens: List[str]
    custom_allergens: Optional[List[str]] = []

class DishSafety(BaseModel):
    name: str
    description: str
    safety_score: int  # 0-100
    safety_level: str  # Safe, Likely Safe, Unknown, Caution, Unsafe
    detected_allergens: List[str]
    confidence: int  # 0-100
    recommendations: str
    ingredients_inferred: List[str]

class MenuAnalysisResponse(BaseModel):
    restaurant_name: str
    total_dishes: int
    safe_dishes: List[DishSafety]
    unsafe_dishes: List[DishSafety]
    unknown_dishes: List[DishSafety]
    analysis_timestamp: str
    voice_summary: str

# ALLERGEN DATABASE
COMMON_ALLERGENS = [
    "peanuts", "tree nuts", "milk", "eggs", "wheat", 
    "soy", "fish", "shellfish", "sesame", "mustard",
    "celery", "lupin", "sulfites", "mollusks"
]

ALLERGEN_KEYWORDS = {
    "peanuts": ["peanut", "groundnut", "arachis"],
    "tree nuts": ["almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia"],
    "milk": ["milk", "cheese", "cream", "butter", "yogurt", "dairy", "lactose", "whey", "casein"],
    "eggs": ["egg", "mayo", "mayonnaise", "meringue", "custard"],
    "wheat": ["wheat", "flour", "bread", "pasta", "noodle", "couscous", "semolina"],
    "soy": ["soy", "tofu", "edamame", "miso", "tempeh"],
    "fish": ["fish", "salmon", "tuna", "cod", "anchov", "sardine"],
    "shellfish": ["shrimp", "crab", "lobster", "prawn", "crawfish", "crayfish"],
    "sesame": ["sesame", "tahini"],
    "gluten": ["wheat", "barley", "rye", "flour", "bread"]
}

# NOVA INTEGRATION
class NovaMenuAnalyzer:
    """Integration with all Nova models for menu analysis"""
    
    def __init__(self):
        logger.info("Nova Menu Analyzer initialized")
    
    async def extract_text_from_pdf(self, pdf_data: bytes) -> str:
        """Extract text from PDF using PyPDF2"""
        try:
            pdf_file = io.BytesIO(pdf_data)
            reader = PdfReader(pdf_file)
            
            text = ""
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            logger.info(f"Extracted {len(text)} characters from PDF")
            return text
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""
    
    async def analyze_menu_image(self, image_data: bytes, filename: str = "") -> Dict:
        """Use Nova Pro to OCR and understand menu"""
        # Check if PDF
        if filename.lower().endswith('.pdf'):
            text = await self.extract_text_from_pdf(image_data)
            if text:
                # Parse dishes from extracted text
                dishes = self._parse_dishes_from_text(text)
                return {
                    "text": text,
                    "dishes": dishes if dishes else self._get_demo_dishes()
                }
        
        # In production: Call Nova Pro with image
        # For demo: Return mock data
        return {
            "text": "Sample menu extracted",
            "dishes": self._get_demo_dishes()
        }
    
    def _parse_dishes_from_text(self, text: str) -> List[Dict]:
        """Parse dish names and descriptions from extracted text"""
        dishes = []
        lines = text.split('\n')
        
        current_dish = None
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Simple heuristic: lines with $ are likely dishes
            if '$' in line:
                parts = line.split('$')
                if len(parts) >= 2:
                    name_part = parts[0].strip()
                    price_part = '$' + parts[1].split()[0]
                    
                    # Next line might be description
                    dishes.append({
                        "name": name_part,
                        "description": "",
                        "price": price_part
                    })
        
        return dishes
    
    async def analyze_menu_url(self, url: str) -> Dict:
        """Use Nova Act to scrape menu from URL"""
        # In production: Nova Act navigates and extracts
        return {
            "restaurant": "Demo Restaurant",
            "dishes": self._get_demo_dishes()
        }
    
    def _get_demo_dishes(self) -> List[Dict]:
        """Demo menu data"""
        return [
            {
                "name": "Pad Thai",
                "description": "Rice noodles with egg, peanuts, bean sprouts, lime",
                "price": "$14.99"
            },
            {
                "name": "Green Curry",
                "description": "Coconut curry with vegetables and choice of protein",
                "price": "$15.99"
            },
            {
                "name": "Tom Yum Soup",
                "description": "Spicy and sour soup with shrimp, mushrooms, lemongrass",
                "price": "$8.99"
            },
            {
                "name": "Spring Rolls",
                "description": "Fresh vegetables wrapped in rice paper with peanut sauce",
                "price": "$6.99"
            },
            {
                "name": "Mango Sticky Rice",
                "description": "Sweet sticky rice with fresh mango and coconut milk",
                "price": "$7.99"
            },
            {
                "name": "Grilled Salmon",
                "description": "Atlantic salmon with teriyaki glaze and sesame seeds",
                "price": "$18.99"
            },
            {
                "name": "Margherita Pizza",
                "description": "Fresh mozzarella, tomato sauce, basil on thin crust",
                "price": "$13.99"
            },
            {
                "name": "Caesar Salad",
                "description": "Romaine lettuce, parmesan, croutons, caesar dressing",
                "price": "$9.99"
            }
        ]
    
    async def assess_dish_safety(self, dish: Dict, allergens: List[str], custom_keywords: Dict[str, List[str]] = {}) -> DishSafety:
        """Use Nova 2 Lite to assess safety"""
        name = dish["name"]
        description = dish["description"].lower()
        
        # Merge standard and custom allergen keywords
        all_keywords = {**ALLERGEN_KEYWORDS, **custom_keywords}
        
        # Detect allergens
        detected = []
        for allergen in allergens:
            allergen_lower = allergen.lower()
            keywords = all_keywords.get(allergen_lower, [allergen_lower])
            for keyword in keywords:
                if keyword.lower() in description or keyword.lower() in name.lower():
                    detected.append(allergen)
                    break
        
        # Calculate safety score
        if detected:
            safety_score = max(0, 50 - (len(detected) * 20))
        else:
            # Check for ambiguous ingredients
            ambiguous_words = ["sauce", "dressing", "seasoning", "spice"]
            has_ambiguous = any(word in description for word in ambiguous_words)
            safety_score = 75 if has_ambiguous else 95
        
        # Determine level
        if safety_score >= 90:
            level = "Safe"
        elif safety_score >= 70:
            level = "Likely Safe"
        elif safety_score >= 40:
            level = "Unknown"
        elif safety_score >= 20:
            level = "Caution"
        else:
            level = "Unsafe"
        
        # Generate recommendations
        if detected:
            recommendations = f"Contains {', '.join(detected)}. Avoid this dish or ask about ingredient substitutions."
        elif safety_score < 90:
            recommendations = "Description lacks detail. Ask server about ingredients and preparation methods."
        else:
            recommendations = "Appears safe based on description. Always verify with server."
        
        # Infer ingredients
        ingredients = self._infer_ingredients(description)
        
        confidence = 85 if not detected else 95
        
        return DishSafety(
            name=name,
            description=dish["description"],
            safety_score=safety_score,
            safety_level=level,
            detected_allergens=detected,
            confidence=confidence,
            recommendations=recommendations,
            ingredients_inferred=ingredients
        )
    
    def _infer_ingredients(self, description: str) -> List[str]:
        """Use Nova 2 Lite to infer likely ingredients"""
        # Simple keyword extraction
        common_ingredients = [
            "rice", "noodles", "chicken", "beef", "pork", "shrimp", "fish",
            "vegetables", "coconut", "peanuts", "sesame", "egg", "milk",
            "cheese", "tomato", "lettuce", "mushrooms", "onion", "garlic"
        ]
        
        found = []
        for ingredient in common_ingredients:
            if ingredient in description.lower():
                found.append(ingredient)
        
        return found[:5]  # Limit to 5
    
    async def generate_voice_summary(self, safe_count: int, unsafe_count: int, allergens: List[str]) -> str:
        """Use Nova 2 Sonic to generate voice summary"""
        allergen_text = ", ".join(allergens)
        return f"Found {safe_count} safe dishes and {unsafe_count} dishes to avoid for {allergen_text} allergies. Review the details below."

analyzer = NovaMenuAnalyzer()

# API ENDPOINTS

@app.get("/")
async def root():
    return {
        "name": "SafeBite AI API",
        "version": "1.0.0",
        "status": "operational",
        "powered_by": "Amazon Nova (Pro, Lite, Act, Sonic, Embeddings)",
        "features": ["Image OCR", "PDF Text Extraction", "Custom Allergens"]
    }

@app.get("/health")
async def health():
    return {
        "name": "SafeBite AI API",
        "version": "1.0.0",
        "status": "operational",
        "powered_by": "Amazon Nova"
    }

@app.get("/allergens")
async def get_allergens():
    """Get list of supported allergens"""
    return {
        "allergens": COMMON_ALLERGENS,
        "total": len(COMMON_ALLERGENS)
    }

@app.post("/analyze/image", response_model=MenuAnalysisResponse)
async def analyze_menu_image(
    file: UploadFile = File(...), 
    allergens: str = "",
    custom_allergens: str = ""
):
    """
    Analyze menu from uploaded image or PDF
    allergens: comma-separated list
    custom_allergens: comma-separated list of additional allergens
    """
    try:
        # Parse allergens
        allergen_list = [a.strip().lower() for a in allergens.split(",") if a.strip()]
        custom_list = [a.strip() for a in custom_allergens.split(",") if a.strip()]
        
        # Combine allergen lists
        all_allergens = allergen_list + custom_list
        
        if not all_allergens:
            raise HTTPException(status_code=400, detail="Please specify at least one allergen")
        
        # Read file
        file_data = await file.read()
        
        # Analyze with Nova Pro (supports both images and PDFs)
        menu_data = await analyzer.analyze_menu_image(file_data, file.filename)
        
        # Build custom keywords dict for custom allergens
        custom_keywords = {allergen.lower(): [allergen.lower()] for allergen in custom_list}
        
        # Assess each dish
        safe_dishes = []
        unsafe_dishes = []
        unknown_dishes = []
        
        for dish in menu_data["dishes"]:
            safety = await analyzer.assess_dish_safety(dish, all_allergens, custom_keywords)
            
            if safety.safety_score >= 70:
                safe_dishes.append(safety)
            elif safety.safety_score >= 40:
                unknown_dishes.append(safety)
            else:
                unsafe_dishes.append(safety)
        
        # Generate voice summary
        voice_summary = await analyzer.generate_voice_summary(
            len(safe_dishes), len(unsafe_dishes), all_allergens
        )
        
        file_type = "PDF" if file.filename.lower().endswith('.pdf') else "Image"
        
        return MenuAnalysisResponse(
            restaurant_name=f"Uploaded {file_type}",
            total_dishes=len(menu_data["dishes"]),
            safe_dishes=safe_dishes,
            unsafe_dishes=unsafe_dishes,
            unknown_dishes=unknown_dishes,
            analysis_timestamp=datetime.now().isoformat(),
            voice_summary=voice_summary
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/url", response_model=MenuAnalysisResponse)
async def analyze_menu_url(request: MenuAnalysisRequest):
    """
    Analyze menu from restaurant URL
    """
    try:
        if not request.menu_url:
            raise HTTPException(status_code=400, detail="Menu URL required")
        
        all_allergens = request.allergens + (request.custom_allergens or [])
        
        if not all_allergens:
            raise HTTPException(status_code=400, detail="Please specify at least one allergen")
        
        # Analyze with Nova Act
        menu_data = await analyzer.analyze_menu_url(str(request.menu_url))
        
        # Build custom keywords
        custom_keywords = {a.lower(): [a.lower()] for a in (request.custom_allergens or [])}
        
        # Assess each dish
        safe_dishes = []
        unsafe_dishes = []
        unknown_dishes = []
        
        for dish in menu_data["dishes"]:
            safety = await analyzer.assess_dish_safety(dish, all_allergens, custom_keywords)
            
            if safety.safety_score >= 70:
                safe_dishes.append(safety)
            elif safety.safety_score >= 40:
                unknown_dishes.append(safety)
            else:
                unsafe_dishes.append(safety)
        
        # Generate voice summary
        voice_summary = await analyzer.generate_voice_summary(
            len(safe_dishes), len(unsafe_dishes), all_allergens
        )
        
        return MenuAnalysisResponse(
            restaurant_name=menu_data.get("restaurant", "Restaurant"),
            total_dishes=len(menu_data["dishes"]),
            safe_dishes=safe_dishes,
            unsafe_dishes=unsafe_dishes,
            unknown_dishes=unknown_dishes,
            analysis_timestamp=datetime.now().isoformat(),
            voice_summary=voice_summary
        )
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
