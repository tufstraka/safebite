"""
SafeBite AI - Complete Nova Integration
Updated Backend with Textract + Nova 2 Lite + Nova Sonic + Embeddings + Agentic AI
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

# Import our Nova components
from nova_textract_ocr import TextractMenuExtractor
from nova_lite_reasoner import NovaLiteAllergenReasoner
from admin_routes import router as admin_router

# Import new Nova features
from nova_sonic_voice import NovaSonicVoice
from nova_embeddings import NovaEmbeddingsAllergenMatcher
from safebite_agent import SafeBiteAgent

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SafeBite AI API - Nova Powered",
    description="AI Menu Safety Scanner with AWS Textract + Nova 2 Lite + Nova Sonic + Embeddings + Agentic AI",
    version="3.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include admin routes
app.include_router(admin_router)

# Initialize Nova components
textract_extractor = TextractMenuExtractor()
nova_reasoner = NovaLiteAllergenReasoner()
nova_voice = NovaSonicVoice()
nova_embeddings = NovaEmbeddingsAllergenMatcher()
safebite_agent = SafeBiteAgent()

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

# COMMON ALLERGENS - Keywords for detecting allergens in dish names/descriptions
# IMPORTANT: Only check for allergens the user has specified they are allergic to
ALLERGEN_KEYWORDS = {
    "peanuts": ["peanut", "groundnut", "arachis"],
    "tree nuts": ["almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia"],
    "nuts": ["nut", "almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia", "peanut"],
    "milk": ["milk", "cheese", "cream", "butter", "yogurt", "dairy", "lactose", "whey", "casein"],
    "eggs": ["egg", "albumin", "mayonnaise", "meringue", "aioli", "custard", "hollandaise"],
    "wheat": ["wheat", "flour", "bread", "pasta", "gluten", "breadcrumb"],
    "soy": ["soy", "tofu", "edamame", "soy sauce", "soya"],
    "fish": ["fish", "salmon", "tuna", "cod", "anchovy", "bass", "trout", "halibut"],
    "shellfish": ["shrimp", "crab", "lobster", "clam", "oyster", "mussel", "scallop", "prawn"],
    "sesame": ["sesame", "tahini"],
    "gluten": ["gluten", "wheat", "barley", "rye", "flour"],
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
    allergens: str = Form(default=""),  # Made optional with default empty string
    custom_allergens: str = Form(default="")
):
    """
    Complete menu analysis pipeline:
    1. Textract OCR extraction (for menus)
    2. Nova 2 Lite vision analysis (for food photos)
    3. Allergen reasoning
    4. Formatted output with color coding
    """
    try:
        # Parse allergens - combine both standard and custom
        user_allergens = []
        if allergens:
            user_allergens.extend([a.strip().lower() for a in allergens.split(",") if a.strip()])
        if custom_allergens:
            user_allergens.extend([a.strip().lower() for a in custom_allergens.split(",") if a.strip()])
        
        # Require at least one allergen
        if not user_allergens:
            raise HTTPException(status_code=400, detail="Please select at least one allergen to check for")
        
        logger.info(f"Analyzing for allergens: {user_allergens}")
        
        # Read file
        file_bytes = await file.read()
        file_extension = file.filename.split('.')[-1].lower()
        
        # Determine file type and extract content
        dishes = []
        extraction_method = "unknown"
        
        if file_extension == 'pdf':
            # PDF: Use PyPDF2
            extraction_result = await textract_extractor.extract_from_pdf(file_bytes)
            extraction_method = "pypdf2"
            if extraction_result['success']:
                dishes = extraction_result['dishes']
        else:
            # Image: Try Textract OCR first
            extraction_result = await textract_extractor.extract_menu_from_image(file_bytes)
            extraction_method = "textract_ocr"
            if extraction_result['success']:
                dishes = extraction_result['dishes']
        
        # If we got dishes from OCR/PDF, clean them with AI
        if dishes and len(dishes) > 3:
            logger.info(f"Cleaning {len(dishes)} extracted dishes with AI...")
            dishes = await textract_extractor.clean_dishes_with_ai(dishes)
        
        # If no dishes found from OCR, treat as food photo and use Nova vision
        if not dishes:
            logger.info("No menu dishes found, analyzing as food photo with Nova vision...")
            extraction_method = "nova_vision"
            
            # Use Nova to identify the food in the image
            food_analysis = await nova_reasoner.analyze_food_photo(
                image_bytes=file_bytes,
                user_allergens=user_allergens
            )
            
            if food_analysis and food_analysis.get('food_name'):
                # Create a single dish entry from the food photo
                dishes = [{
                    'name': food_analysis.get('food_name', 'Unknown Food'),
                    'description': food_analysis.get('description', ''),
                    'price': 'N/A',
                    'raw_text': food_analysis.get('description', '')
                }]
            else:
                raise HTTPException(
                    status_code=400, 
                    detail="Could not identify food in image. Please upload a clear photo of food or a menu."
                )
        
        logger.info(f"Extracted {len(dishes)} items using {extraction_method}")
        
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


# ============================================
# NEW FEATURES: Voice AI, Embeddings, Agentic
# ============================================

@app.post("/analyze/voice")
async def analyze_with_voice(
    file: UploadFile = File(...),
    allergens: str = Form(...),
    custom_allergens: str = Form(default="")
):
    """
    Analyze menu and return audio summary using Nova 2 Sonic
    Returns: JSON with base64 encoded audio
    """
    try:
        # First, do the regular analysis
        user_allergens = [a.strip().lower() for a in allergens.split(",") if a.strip()]
        if custom_allergens:
            user_allergens.extend([a.strip().lower() for a in custom_allergens.split(",") if a.strip()])
        
        file_bytes = await file.read()
        
        # Extract dishes
        extraction_result = await textract_extractor.extract_menu_from_image(file_bytes)
        
        if not extraction_result['success'] or not extraction_result['dishes']:
            return {
                "success": False,
                "error": "Could not extract menu items",
                "audio": None
            }
        
        dishes = extraction_result['dishes']
        
        # Analyze each dish
        safe_count = 0
        caution_count = 0
        unsafe_count = 0
        all_detected = []
        top_safe_dish = None
        
        for dish in dishes:
            ai_analysis = await nova_reasoner.analyze_allergens(
                dish_name=dish['name'],
                dish_description=dish.get('description', ''),
                user_allergens=user_allergens
            )
            
            safety_level = ai_analysis.get('safety_level', 'unknown')
            detected = ai_analysis.get('detected_allergens', [])
            all_detected.extend(detected)
            
            if safety_level == 'safe':
                safe_count += 1
                if not top_safe_dish:
                    top_safe_dish = dish['name']
            elif safety_level == 'caution':
                caution_count += 1
            else:
                unsafe_count += 1
        
        # Generate voice summary
        audio_base64 = await nova_voice.generate_safety_audio(
            safe_count=safe_count,
            caution_count=caution_count,
            unsafe_count=unsafe_count,
            detected_allergens=all_detected,
            top_safe_dish=top_safe_dish
        )
        
        return {
            "success": True,
            "summary": {
                "safe": safe_count,
                "caution": caution_count,
                "unsafe": unsafe_count,
                "top_recommendation": top_safe_dish
            },
            "audio": audio_base64,
            "audio_format": "mp3"
        }
        
    except Exception as e:
        logger.error(f"Voice analysis failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "audio": None
        }


@app.post("/analyze/semantic")
async def analyze_with_embeddings(
    dish_name: str = Form(...),
    dish_description: str = Form(default=""),
    allergens: str = Form(...)
):
    """
    Semantic allergen matching using Nova Embeddings
    More accurate than keyword matching
    """
    try:
        user_allergens = [a.strip().lower() for a in allergens.split(",") if a.strip()]
        
        result = await nova_embeddings.semantic_allergen_match(
            dish_name=dish_name,
            dish_description=dish_description,
            user_allergens=user_allergens
        )
        
        return {
            "success": True,
            "dish": dish_name,
            "detected_allergens": result["detected_allergens"],
            "confidence_scores": result["confidence_scores"],
            "semantic_matches": result["semantic_matches"],
            "method": result["method"]
        }
        
    except Exception as e:
        logger.error(f"Semantic analysis failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.post("/analyze/agent")
async def analyze_with_agent(
    file: UploadFile = File(...),
    allergens: str = Form(...),
    custom_allergens: str = Form(default="")
):
    """
    Full agentic analysis with multi-step reasoning
    Shows execution trace and reasoning steps
    """
    try:
        user_allergens = [a.strip().lower() for a in allergens.split(",") if a.strip()]
        if custom_allergens:
            user_allergens.extend([a.strip().lower() for a in custom_allergens.split(",") if a.strip()])
        
        file_bytes = await file.read()
        
        # Extract dishes
        extraction_result = await textract_extractor.extract_menu_from_image(file_bytes)
        
        if not extraction_result['success'] or not extraction_result['dishes']:
            return {
                "success": False,
                "error": "Could not extract menu items"
            }
        
        dishes = extraction_result['dishes']
        
        # Run agentic analysis
        agent_result = await safebite_agent.analyze_menu_with_reasoning(
            dishes=dishes,
            user_allergens=user_allergens
        )
        
        return {
            "success": True,
            "agent_analysis": agent_result,
            "execution_summary": safebite_agent.get_execution_summary()
        }
        
    except Exception as e:
        logger.error(f"Agent analysis failed: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@app.get("/health")
async def health_check():
    return {
        "name": "SafeBite AI API (Nova Powered)",
        "version": "3.0.0",
        "status": "operational",
        "models": {
            "ocr": "AWS Textract",
            "reasoning": "Amazon Nova 2 Lite",
            "voice": "Amazon Nova 2 Sonic / Polly",
            "embeddings": "Amazon Titan Embeddings",
            "agent": "SafeBite Agentic AI"
        },
        "features": [
            "Menu OCR extraction",
            "AI allergen reasoning",
            "Voice audio summaries",
            "Semantic allergen matching",
            "Multi-step agentic analysis"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
