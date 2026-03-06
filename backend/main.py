"""
SafeBite AI - Complete Nova Integration
Updated Backend with Textract + Nova 2 Lite
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import logging
from datetime import datetime, timezone, timedelta
import base64
import json
import io
from PyPDF2 import PdfReader
import os
from dotenv import load_dotenv
import asyncio

# Import our new Nova components
from nova_textract_ocr import TextractMenuExtractor
from nova_lite_reasoner import NovaLiteAllergenReasoner

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SafeBite AI API - Nova Powered",
    description="AI Menu Safety Scanner with AWS Textract + Nova 2 Lite",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Nova components
textract_extractor = TextractMenuExtractor()
nova_reasoner = NovaLiteAllergenReasoner()

# DATA MODELS

class DishAnalysis(BaseModel):
    name: str
    description: str
    price: str
    safety_score: int  # 0-100
    safety_level: str  # "safe", "caution", "unsafe"
    detected_allergens: List[str]
    confidence: int  # 0-100
    hidden_ingredients: List[str]
    reasoning: str
    color_code: str  # "green", "yellow", "red"

class MenuScanResponse(BaseModel):
    restaurant_name: str
    total_dishes: int
    safe_dishes: List[DishAnalysis]
    caution_dishes: List[DishAnalysis]
    unsafe_dishes: List[DishAnalysis]
    analysis_timestamp: str
    extraction_method: str  # "textract_image" or "textract_pdf"
    ai_summary: str

# COMMON ALLERGENS
ALLERGEN_KEYWORDS = {
    "peanuts": ["peanut", "groundnut", "arachis"],
    "tree nuts": ["almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia"],
    "milk": ["milk", "cheese", "cream", "butter", "yogurt", "dairy", "lactose", "whey", "casein"],
    "eggs": ["egg", "albumin", "mayonnaise"],
    "wheat": ["wheat", "flour", "bread", "pasta", "gluten"],
    "soy": ["soy", "tofu", "edamame", "soy sauce"],
    "fish": ["fish", "salmon", "tuna", "cod", "anchovy"],
    "shellfish": ["shrimp", "crab", "lobster", "clam", "oyster"],
    "sesame": ["sesame", "tahini"],
    "gluten": ["gluten", "wheat", "barley", "rye"],
    "mustard": ["mustard"],
    "celery": ["celery"]
}

@app.get("/health")
async def health_check():
    return {
        "name": "SafeBite AI API (Nova Powered)",
        "version": "2.0.0",
        "status": "operational",
        "models": {
            "ocr": "AWS Textract",
            "reasoning": "Amazon Nova 2 Lite",
            "formatting": "SafeBite AI"
        }
    }

@app.post("/analyze/image", response_model=MenuScanResponse)
async def analyze_menu_image(
    file: UploadFile = File(...),
    allergens: str = Form(...),
    custom_allergens: str = Form(default="")
):
    """
    Complete menu analysis pipeline:
    1. Textract OCR extraction
    2. Nova 2 Lite allergen reasoning
    3. Formatted menu output with color coding
    """
    try:
        # Parse allergens
        user_allergens = [a.strip().lower() for a in allergens.split(",") if a.strip()]
        if custom_allergens:
            user_allergens.extend([a.strip().lower() for a in custom_allergens.split(",") if a.strip()])
        
        logger.info(f"Analyzing menu for allergens: {user_allergens}")
        
        # Read file
        file_bytes = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        
        # Step 1: Extract text with Textract
        if file_extension == 'pdf':
            extraction_result = await textract_extractor.extract_from_pdf(file_bytes)
            extraction_method = "textract_pdf"
        else:
            extraction_result = await textract_extractor.extract_menu_from_image(file_bytes)
            extraction_method = "textract_image"
        
        if not extraction_result['success']:
            raise HTTPException(status_code=400, detail=f"OCR failed: {extraction_result.get('error', 'Unknown error')}")
        
        dishes = extraction_result['dishes']
        logger.info(f"Textract extracted {len(dishes)} dishes")
        
        if not dishes:
            raise HTTPException(status_code=400, detail="No dishes found in image. Please upload a clear menu photo.")
        
        # Step 2: Analyze each dish with Nova 2 Lite
        analyzed_dishes = []
        
        for dish in dishes:
            try:
                # Get AI reasoning from Nova 2 Lite
                ai_analysis = await nova_reasoner.analyze_allergens(
                    dish_name=dish['name'],
                    dish_description=dish.get('description', ''),
                    user_allergens=user_allergens,
                    extracted_ingredients=None  # Textract doesn't extract ingredients directly
                )
                
                # Also infer hidden ingredients
                hidden_ingredients = await nova_reasoner.infer_hidden_ingredients(
                    dish_name=dish['name'],
                    dish_description=dish.get('description', '')
                )
                
                # Combine analysis
                detected = ai_analysis.get('detected_allergens', [])
                confidence = ai_analysis.get('confidence', 50)
                safety_level = ai_analysis.get('safety_level', 'unknown')
                
                # Calculate safety score
                if safety_level == 'safe':
                    safety_score = 90
                    color_code = 'green'
                elif safety_level == 'caution':
                    safety_score = 50
                    color_code = 'yellow'
                else:  # unsafe or unknown
                    safety_score = 10 if safety_level == 'unsafe' else 50
                    color_code = 'red' if safety_level == 'unsafe' else 'yellow'
                
                analyzed_dish = DishAnalysis(
                    name=dish['name'],
                    description=dish.get('description', ''),
                    price=dish.get('price', 'N/A'),
                    safety_score=safety_score,
                    safety_level=safety_level,
                    detected_allergens=detected,
                    confidence=confidence,
                    hidden_ingredients=hidden_ingredients,
                    reasoning=ai_analysis.get('reasoning', 'AI analysis unavailable'),
                    color_code=color_code
                )
                
                analyzed_dishes.append(analyzed_dish)
                
            except Exception as dish_error:
                logger.warning(f"Failed to analyze dish '{dish['name']}': {str(dish_error)}")
                # Add dish with unknown safety
                analyzed_dishes.append(DishAnalysis(
                    name=dish['name'],
                    description=dish.get('description', ''),
                    price=dish.get('price', 'N/A'),
                    safety_score=50,
                    safety_level='unknown',
                    detected_allergens=[],
                    confidence=0,
                    hidden_ingredients=[],
                    reasoning=f"Analysis failed: {str(dish_error)}",
                    color_code='yellow'
                ))
        
        # Step 3: Categorize dishes
        safe_dishes = [d for d in analyzed_dishes if d.color_code == 'green']
        caution_dishes = [d for d in analyzed_dishes if d.color_code == 'yellow']
        unsafe_dishes = [d for d in analyzed_dishes if d.color_code == 'red']
        
        # Generate AI summary
        ai_summary = f"Found {len(safe_dishes)} safe dishes, {len(caution_dishes)} dishes needing caution, and {len(unsafe_dishes)} unsafe dishes for your allergen profile."
        
        return MenuScanResponse(
            restaurant_name=file.filename.replace('.jpg', '').replace('.png', '').replace('.pdf', '').title(),
            total_dishes=len(analyzed_dishes),
            safe_dishes=safe_dishes,
            caution_dishes=caution_dishes,
            unsafe_dishes=unsafe_dishes,
            analysis_timestamp=datetime.now(timezone.utc).isoformat(),
            extraction_method=extraction_method,
            ai_summary=ai_summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

@app.post("/analyze/photo")
async def analyze_single_dish_photo(
    file: UploadFile = File(...),
    allergens: str = Form(...)
):
    """
    Quick analysis for single dish photo
    Returns: Safe ✅ or Unsafe ⚠️ with reasoning
    """
    try:
        user_allergens = [a.strip().lower() for a in allergens.split(",") if a.strip()]
        file_bytes = await file.read()
        
        # Extract text
        extraction_result = await textract_extractor.extract_menu_from_image(file_bytes)
        
        if not extraction_result['success'] or not extraction_result['dishes']:
            # Fallback: Use full text for basic keyword matching
            full_text = extraction_result.get('full_text', '').lower()
            detected = []
            
            for allergen in user_allergens:
                keywords = ALLERGEN_KEYWORDS.get(allergen, [allergen])
                if any(kw in full_text for kw in keywords):
                    detected.append(allergen)
            
            if detected:
                return {
                    "result": "Unsafe ⚠️",
                    "detected_allergens": detected,
                    "reasoning": f"Detected {', '.join(detected)} in text",
                    "confidence": 60
                }
            else:
                return {
                    "result": "Likely Safe ✅",
                    "detected_allergens": [],
                    "reasoning": "No allergens detected in visible text",
                    "confidence": 70
                }
        
        # Use Nova 2 Lite for analysis
        dish = extraction_result['dishes'][0]  # First dish
        ai_analysis = await nova_reasoner.analyze_allergens(
            dish_name=dish['name'],
            dish_description=dish.get('description', ''),
            user_allergens=user_allergens
        )
        
        detected = ai_analysis.get('detected_allergens', [])
        
        if detected:
            return {
                "result": "Unsafe ⚠️",
                "detected_allergens": detected,
                "reasoning": ai_analysis.get('reasoning', ''),
                "confidence": ai_analysis.get('confidence', 0)
            }
        else:
            return {
                "result": "Safe ✅",
                "detected_allergens": [],
                "reasoning": ai_analysis.get('reasoning', 'No allergens detected'),
                "confidence": ai_analysis.get('confidence', 0)
            }
            
    except Exception as e:
        logger.error(f"Photo analysis failed: {str(e)}")
        return {
            "result": "Error",
            "detected_allergens": [],
            "reasoning": f"Analysis failed: {str(e)}",
            "confidence": 0
        }

@app.get("/allergens")
async def list_allergens():
    """List supported allergens"""
    return {
        "common_allergens": list(ALLERGEN_KEYWORDS.keys()),
        "total": len(ALLERGEN_KEYWORDS),
        "supports_custom": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
