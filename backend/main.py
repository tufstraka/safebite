"""
SafeBite - Restaurant Menu Safety Scanner
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import logging
from datetime import datetime, timezone, timedelta, timezone
import base64
import json
import io
from PyPDF2 import PdfReader
import boto3
import os
from menu_validator import is_food_menu
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Timezone for timestamps
NAIROBI_OFFSET = timezone(timedelta(hours=3))  # EAT = UTC+3

app = FastAPI(
    title="SafeBite API",
    description="Menu Safety Scanner",
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
    analysis_time_eat: str  # East Africa Time
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
    "fish": [r"fish", "salmon", "tuna", "cod", "anchov", "sardine"],
    "shellfish": ["shrimp", "crab", "lobster", "prawn", "crawfish", "crayfish"],
    "sesame": ["sesame", "tahini"],
    "gluten": ["wheat", "barley", "rye", "flour", "bread"]
}

# NOVA INTEGRATION
class NovaMenuAnalyzer:
    """Integration with all Nova models for menu analysis"""
    
    def __init__(self):
        logger.info("Nova Menu Analyzer initialized")
        # Initialize Bedrock client for Nova Pro
        try:
            self.bedrock = boto3.client(
                service_name='bedrock-runtime',
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
            )
            logger.info("Bedrock client initialized successfully")
        except Exception as e:
            logger.warning(f"Bedrock client initialization failed: {e}")
            self.bedrock = None
    
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
            return {"allergens": "", "reasoning": ""}
    
    async def analyze_menu_image(self, image_data: bytes, filename: str = "") -> Dict:
        """OCR images OR extract text from PDFs"""
        
        # For PDFs: Use PyPDF2 text extraction (Nova Pro doesn't support PDF format)
        if filename.lower().endswith('.pdf'):
            logger.info(f"Processing PDF: {filename}")
            text = await self.extract_text_from_pdf(image_data)
            
            # Validate it's actually a food menu
            if text and len(text.strip()) > 50:
                if not is_food_menu(text):
                    # Generate humorous rejection message with Nova 2 Lite
                    try:
                        prompt = f"""The user uploaded something that's not a restaurant menu. Based on the text content, create a SHORT (1-2 sentences), humorous, casual rejection message in Keith's voice (Nairobi dev, lowercase, direct, funny). Tell them what they uploaded and ask for an actual menu.

Text preview: {text[:200]}

Reply in lowercase, be funny but helpful:"""
                        
                        response = self.bedrock.invoke_model(
                            modelId="us.amazon.nova-lite-v1:0",
                            body=json.dumps({
                                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                                "inferenceConfig": {"max_new_tokens": 100, "temperature": 0.9}
                            })
                        )
                        ai_message = json.loads(response['body'].read())['output']['message']['content'][0]['text'].strip()
                        raise ValueError(ai_message)
                    except Exception as e:
                        # Fallback if AI fails
                        raise ValueError("bruh, that's not a menu. upload something with food on it 🍕")
                logger.info(f"Extracted {len(text)} characters from PDF")
                # Parse dishes from extracted text with improved parser
                dishes = self._parse_dishes_from_text(text)
                if dishes and len(dishes) > 0:
                    logger.info(f"✓ Parsed {len(dishes)} dishes from PDF text")
                    return {"text": text, "dishes": dishes}
                else:
                    logger.warning(f"PDF text extraction succeeded but parser found no dishes")
                    logger.warning(f"First 500 chars of PDF text: {text[:500]}")
            else:
                logger.warning("PDF text extraction failed or insufficient text")
            
                raise ValueError("Could not extract menu items. Please upload a clear photo of a restaurant menu or food.")
        
        # For images: Use Nova Pro
        if self.bedrock:
            try:
                logger.info(f"Calling Nova Pro for image analysis (file: {filename})...")
                
                # Encode image to base64
                image_base64 = base64.b64encode(image_data).decode('utf-8')
                
                # Determine image format (Nova Pro: jpeg, png, gif, webp only)
                image_format = "jpeg"
                if filename.lower().endswith('.png'):
                    image_format = "png"
                elif filename.lower().endswith('.webp'):
                    image_format = "webp"
                elif filename.lower().endswith('.gif'):
                    image_format = "gif"
                
                # Nova Pro request for images
                body = json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "image": {
                                        "format": image_format,
                                        "source": {"bytes": image_base64}
                                    }
                                },
                                {
                                    "text": """Analyze this image carefully. It could be:
1. A restaurant menu with dishes listed
2. A photo of a single food item
3. A photo of multiple food items on a table

Your task: Extract ALL visible food items with detailed descriptions.

For EACH food item you see, create a JSON object with:
- "name": The dish/food name (if on menu) OR describe what you see (e.g., "Grilled chicken breast", "Pasta with sauce")
- "description": Detailed ingredients and preparation you can identify from the image (be specific about visible ingredients like cheese, nuts, vegetables, sauces, etc.)
- "price": The price if visible, otherwise "$0.00"

Return ONLY a JSON array in this exact format:
[{"name": "Item Name", "description": "detailed ingredients visible", "price": "$X.XX"}]

If you see multiple items, include them all. If it's a single plate, describe everything on it.
Be thorough about visible ingredients - this is for allergen detection."""
                                }
                            ]
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": 3000,
                        "temperature": 0.3
                    }
                })
                
                response = self.bedrock.invoke_model(
                    modelId='amazon.nova-pro-v1:0',
                    body=body
                )
                
                result = json.loads(response['body'].read())
                text_response = result['output']['message']['content'][0]['text']
                
                logger.info(f"Nova Pro raw response: {text_response[:300]}...")
                
                # Try to parse JSON from response
                try:
                    # Extract JSON array from response (handle markdown code blocks)
                    import re
                    # Remove markdown code blocks if present
                    cleaned = re.sub(r'```json\s*|\s*```', '', text_response)
                    # Find JSON array
                    json_match = re.search(r'\[.*\]', cleaned, re.DOTALL)
                    if json_match:
                        dishes = json.loads(json_match.group(0))
                        if dishes and len(dishes) > 0:
                            logger.info(f"✓ Nova Pro extracted {len(dishes)} items successfully")
                            return {"text": text_response, "dishes": dishes}
                        else:
                            logger.warning("Nova Pro returned empty array")
                    else:
                        logger.warning(f"Could not find JSON array in response")
                except Exception as e:
                    logger.error(f"JSON parsing failed: {e}")
                    logger.error(f"Raw response was: {text_response[:500]}")
                
            except Exception as e:
                logger.error(f"Nova Pro API call failed: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning("Bedrock client not initialized")
        
                # Use Nova Pro to identify what was uploaded
                try:
                    prompt = "Describe what you see in this image in 1-2 sentences. Be specific and direct."
                    response = self.bedrock.invoke_model(
                        modelId="amazon.nova-pro-v1:0",
                        body=json.dumps({
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"image": {"format": "png", "source": {"bytes": base64.b64encode(image_data).decode()}}},
                                    {"text": prompt}
                                ]
                            }],
                            "inferenceConfig": {"max_new_tokens": 100, "temperature": 0.7}
                        })
                    )
                    image_description = json.loads(response['body'].read())['output']['message']['content'][0]['text'].strip()
                    
                    # Generate humorous rejection with Nova 2 Lite
                    humor_prompt = f"""You uploaded: {image_description}

Create a SHORT (1 sentence), funny response in Keith's voice (Nairobi dev, lowercase, casual). Tell them what they uploaded and ask for a menu or food photo. Be funny but helpful:"""
                    
                    humor_response = self.bedrock.invoke_model(
                        modelId="us.amazon.nova-lite-v1:0",
                        body=json.dumps({
                            "messages": [{"role": "user", "content": [{"text": humor_prompt}]}],
                            "inferenceConfig": {"max_new_tokens": 80, "temperature": 0.9}
                        })
                    )
                    funny_message = json.loads(humor_response['body'].read())['output']['message']['content'][0]['text'].strip()
                    raise ValueError(funny_message)
                except ValueError:
                    raise  # Re-raise ValueError (the funny message)
                except Exception as inner_e:
                    # Fallback if AI description fails
                    raise ValueError("bruh, that doesn't look like a menu. upload a photo of food or a restaurant menu 🍕")
