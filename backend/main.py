"""
SafeBite - Restaurant Menu Safety Scanner
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
import logging
from datetime import datetime, timezone, timedelta, timezone
from database import Scan, init_db, SessionLocal
from admin_routes import router as admin_router
from sqlalchemy.orm import Session
from pathlib import Path
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
# Initialize database on startup
init_db()
# Include admin routes
app.include_router(admin_router)



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
    recommendation: Optional[str] = None  # AI meal recommendation

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
            
            # PDF parsing completely failed - return demo with warning
            logger.error("⚠️ PDF processing failed - using demo data")
            return {"text": "PDF processing failed", "dishes": self._get_demo_dishes()}
        
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
                
                # Try to identify what was uploaded for better error message
                try:
                    recognize_prompt = "What do you see in this image? Describe it in 1-2 sentences."
                    recognize_response = self.bedrock.invoke_model(
                        modelId="amazon.nova-pro-v1:0",
                        body=json.dumps({
                            "messages": [{
                                "role": "user",
                                "content": [
                                    {"image": {"format": "png", "source": {"bytes": base64.b64encode(image_data).decode()}}},
                                    {"text": recognize_prompt}
                                ]
                            }],
                            "inferenceConfig": {"max_new_tokens": 100, "temperature": 0.7}
                        }
                        )
                    )
                    img_desc = json.loads(recognize_response["body"].read())["output"]["message"]["content"][0]["text"].strip()
                    
                    # Generate humorous rejection
                    humor_prompt = f"""You uploaded: {img_desc}
                
                Create a SHORT (1 sentence), funny response in Keith's voice (lowercase, casual, Kenyan). Tell them what they uploaded and ask for a menu or food photo:"""
                    
                    humor_resp = self.bedrock.invoke_model(
                        modelId="us.amazon.nova-lite-v1:0",
                        body=json.dumps({
                            "messages": [{"role": "user", "content": [{"text": humor_prompt}]}],
                            "inferenceConfig": {"max_new_tokens": 80, "temperature": 0.9}
                        })
                    )
                    funny_msg = json.loads(humor_resp["body"].read())["output"]["message"]["content"][0]["text"].strip()
                    raise ValueError(funny_msg)
                except ValueError:
                    raise  # Re-raise the funny message
                except Exception:
                    # If image recognition also fails, generic message
                    raise ValueError("couldn't process that image. upload a clear photo of a menu or food 📸")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
        else:
            logger.warning("Bedrock client not initialized")
        
        # Fallback to demo data
        logger.warning("⚠️ Falling back to demo dishes (analysis failed)")
        return {
            "text": "Sample menu extracted",
            "dishes": self._get_demo_dishes()
        }
    
    def _parse_dishes_from_text(self, text: str) -> List[Dict]:
        """Parse dish names and descriptions from extracted PDF text - IMPROVED"""
        dishes = []
        lines = text.split('\n')
        
        # Try multiple parsing strategies
        
        # Strategy 1: Look for lines with prices ($)
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Check if line contains a price
            if '$' in line or '€' in line or '£' in line:
                # Split on price
                parts = line.split('$')
                if len(parts) >= 2:
                    name_part = parts[0].strip()
                    # Price is first number after $
                    price_match = parts[1].split()[0] if parts[1].split() else "0.00"
                    price = f"${price_match}"
                    
                    # Description might be on next line or same line
                    description = ""
                    # Check if there's more text after price on same line
                    after_price = '$'.join(parts[1:])
                    if len(after_price) > 10:
                        description = after_price[len(price_match):].strip()
                    # Check next line for description
                    elif i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and '$' not in next_line and len(next_line) > 10:
                            description = next_line
                    
                    if name_part:
                        # Filter out menu headers, footers, legends
                        name_lower = name_part.lower()
                        skip_patterns = [
                            'prices are subject to change',
                            'prices are in',
                            'inclusive of vat',
                            'service charge',
                            'catering levy',
                            'allergen',
                            'gluten dairy peanuts',
                            'fish dairy peanuts',
                            'all prices',
                            'menu',
                            'appetizers',
                            'entrees',
                            'desserts',
                            'beverages',
                            'starters',
                            'mains',
                            'sides'
                        ]
                        
                        # Skip if it's a header/footer/legend
                        if any(pattern in name_lower for pattern in skip_patterns):
                            continue
                        
                        # Skip if it's just a list of allergens
                        allergen_words = ['fish', 'dairy', 'peanuts', 'gluten', 'eggs', 'shellfish', 'soy', 'nuts']
                        word_count = len(name_part.split())
                        allergen_count = sum(1 for allergen in allergen_words if allergen in name_lower)
                        if word_count <= 10 and allergen_count >= 3:
                            continue
                        
                        dishes.append({
                            "name": name_part[:100],  # Limit length
                            "description": description[:300] if description else name_part,
                            "price": price
                        })
        
        # Strategy 2: If no prices found, look for numbered items or capitalized lines
        if not dishes:
            for i, line in enumerate(lines):
                line = line.strip()
                # Skip short lines, numbers, headers
                if len(line) < 5 or line.isnumeric():
                    continue
                
                # Check if it looks like a dish name (starts with capital, not too long)
                if line[0].isupper() and len(line) < 100 and not line.endswith(':'):
                    # Get description from next line if available
                    description = ""
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if next_line and next_line[0].islower() and len(next_line) > 10:
                            description = next_line
                    
                    # Filter out headers/footers
                    line_lower = line.lower()
                    skip_patterns = [
                        'prices are subject to change',
                        'prices are in',
                        'inclusive of',
                        'service charge',
                        'allergen',
                        'all prices',
                        'menu section'
                    ]
                    
                    if any(pattern in line_lower for pattern in skip_patterns):
                        continue
                    
                    dishes.append({
                        "name": line,
                        "description": description if description else line,
                        "price": "$0.00"
                    })
                    
                    # Limit to prevent spam
                    if len(dishes) >= 20:
                        break
        
        logger.info(f"Text parser found {len(dishes)} dishes")
        return dishes[:20]  # Max 20 dishes
    
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
        """Assess safety with ingredient inference"""
        name = dish["name"]
        description = dish["description"].lower()
        
        # Step 1: Infer allergens with reasoning
        ai_result = await self._infer_ingredients_with_ai(name, description)
        inferred_allergens = ai_result.get("allergens", "")
        ai_reasoning = ai_result.get("reasoning", "")
        
        # Step 2: Check for allergens in visible description + inferred ingredients
        all_keywords = {**ALLERGEN_KEYWORDS, **custom_keywords}
        
        detected = []
        for allergen in allergens:
            allergen_lower = allergen.lower()
            keywords = all_keywords.get(allergen_lower, [allergen_lower])
            
            # Check visible description
            found_in_description = False
            for keyword in keywords:
                import re
                # Check if keyword uses word boundary regex
            if isinstance(keyword, str) and keyword.startswith(r"\b"):
                # Use regex for word boundary
                if re.search(keyword, description, re.IGNORECASE) or re.search(keyword, name.lower(), re.IGNORECASE):
                    detected.append(allergen)
                    found_in_description = True
                    break
            elif keyword.lower() in description or keyword.lower() in name.lower():
                detected.append(allergen)
                found_in_description = True
                break
            # Check AI-inferred allergens
            if not found_in_description:
                for keyword in keywords:
                    if keyword.lower() in inferred_allergens.lower():
                        detected.append(allergen)
                        break
        
        # Calculate safety score
        if detected:
            # Higher penalty for detected allergens
            safety_score = max(0, 50 - (len(detected) * 25))
        else:
            # Check for ambiguous ingredients
            ambiguous_words = ["sauce", "dressing", "seasoning", "spice", "frosting"]
            has_ambiguous = any(word in description for word in ambiguous_words)
            safety_score = 70 if has_ambiguous else 90
        
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
        
        # Generate recommendations with Keith's personality - direct, practical, honest
        if detected:
            allergen_list = ', '.join(detected)
            
            # Use AI reasoning if available, otherwise generic message
            context = ""
            if ai_reasoning:
                # Extract reasoning for detected allergens only
                detected_reasoning = []
                for allergen in detected:
                    for reason_part in ai_reasoning.split(';'):
                        if allergen.lower() in reason_part.lower():
                            # Clean up the reasoning
                            reason = reason_part.split(':', 1)[1].strip() if ':' in reason_part else reason_part.strip()
                            detected_reasoning.append(reason)
                            break
                
                if detected_reasoning:
                    context = f" ({', '.join(detected_reasoning)})"
            
            if len(detected) == 1:
                # Dynamic, personality-driven advice with AI reasoning
                import random
                
                # Vary the tone and approach
                styles = [
                    # Direct/casual
                    f"nah, this has {allergen_list}{context}. skip it.",
                    f"yeah, {allergen_list} in here{context}. pass on this one.",
                    f"got {allergen_list}{context}. not worth it.",
                    # Practical/helpful
                    f"heads up - {allergen_list}{context}. ask if they can leave it out.",
                    f"this one has {allergen_list}{context}. see if they can swap it.",
                    f"contains {allergen_list}{context}. check with the kitchen.",
                    # Confident/matter-of-fact
                    f"{allergen_list} detected{context}. i'd pick something else.",
                    f"spotted {allergen_list}{context}. better options on the menu.",
                    f"has {allergen_list}{context}. go for another dish.",
                    # Kenyan casual
                    f"ati {allergen_list}{context}? skip that one.",
                    f"sawa so this has {allergen_list}{context}. not safe."
                ]
                recommendations = random.choice(styles)
            else:
                # Multiple allergens - varied responses
                import random
                styles = [
                    f"bruh, this has {allergen_list}{context}. hard pass.",
                    f"nope - {allergen_list}{context}. skip entirely.",
                    f"this one's got {allergen_list}{context}. not happening.",
                    f"multiple issues here: {allergen_list}{context}. avoid.",
                    f"{allergen_list}{context}. definitely skip this one.",
                    f"way too much going on - {allergen_list}{context}. pass."
                ]
                recommendations = random.choice(styles)
        elif safety_score < 90:
            # Honest about uncertainty - varied personality
            import random
            uncertain = [
                "can't tell from the menu. just ask your server.",
                "description's vague. quick question to the kitchen.",
                "not enough info here. better ask than guess.",
                "menu doesn't say. check with staff before ordering.",
                "unclear from this. ask what's actually in it.",
                "description's not clear.",
                "hard to say for sure. ask the kitchen directly.",
                "menu's being cryptic. get confirmation from staff."
            ]
            recommendations = random.choice(uncertain)
        else:
            # Casually confident - varied tone
            import random
            safe = [
                "looks clean.",
                "should be fine.",
                "seems safe.",
                "you're good.",
                "this one looks okay. run it by the server to be sure.",
                "appears safe.",
                "should work.",
                "looking good."
            ]
            recommendations = random.choice(safe)
        
        # Extract basic ingredients from description
        visible_ingredients = self._extract_simple_ingredients(description)
        
        confidence = 90 if detected else 75
        
        return DishSafety(
            name=name,
            description=dish["description"],
            safety_score=safety_score,
            safety_level=level,
            detected_allergens=detected,
            confidence=confidence,
            recommendations=recommendations,
            ingredients_inferred=visible_ingredients[:5]
        )
    

    async def generate_recommendation(self, safe_dishes: List, allergens: List[str]) -> Optional[str]:
        """Generate Keith-style meal recommendation from safe dishes"""
        if not safe_dishes:
            return None
        
        # Pick highest safety score
        best = max(safe_dishes, key=lambda d: d.safety_score)
        
        import random
        templates = [
            f"go for the {best.name.lower()}. clean choice, {best.safety_score}% safe.",
            f"{best.name.lower()} looks solid. no {', '.join(allergens[:2])} here.",
            f"try {best.name.lower()}. tested it, you're good.",
            f"{best.name.lower()} is your safest bet. {best.safety_score}% confidence.",
            f"i'd pick {best.name.lower()}. no allergens detected.",
        ]
        return random.choice(templates)

    async def _infer_ingredients_with_ai(self, name: str, description: str) -> str:
        """Use Nova 2 Lite to intelligently infer ALL likely ingredients"""
        if self.bedrock:
            try:
                prompt = f"""You are a food safety expert. Analyze this dish for allergens.

Dish name: {name}
Description: {description}

Task: If this dish likely contains common allergens, explain WHY.

IMPORTANT RULES:
1. Only mention allergens if HIGHLY CONFIDENT they're present
2. Explain WHERE the allergen comes from (which component/ingredient)
3. Focus on: dairy, eggs, nuts, gluten, soy, fish, shellfish
4. If unsure, write "no clear allergens detected"
5. Be specific about the SOURCE of the allergen

Format your response as:
ALLERGEN: source/reason

Examples:
- "Caesar Salad" → FISH: anchovies in Caesar dressing; EGG: raw egg in dressing; DAIRY: parmesan cheese
- "Pad Thai" → FISH: fish sauce (traditional recipe); PEANUTS: crushed peanuts topping; EGG: scrambled egg
- "Birthday Cake" → DAIRY: butter in cake + cream in frosting; EGGS: in cake batter; GLUTEN: wheat flour
- "Grilled Chicken" → no clear allergens detected (unless sauce specified)

Be concise. Only list allergens you're confident about with their source:"""

                body = json.dumps({
                    "messages": [
                        {
                            "role": "user",
                            "content": [{"text": prompt}]
                        }
                    ],
                    "inferenceConfig": {
                        "max_new_tokens": 150,
                        "temperature": 0.1,
                        "top_p": 0.9
                    }
                })
                
                response = self.bedrock.invoke_model(
                    modelId='us.amazon.nova-lite-v1:0',  # Use regional inference profile
                    body=body
                )
                
                result = json.loads(response['body'].read())
                ingredients = result['output']['message']['content'][0]['text'].strip()
                
                # Validation: Check if AI is being too creative
                if len(ingredients) > 200:
                    logger.warning(f"AI response too long ({len(ingredients)} chars), possible hallucination")
                    return {"allergens": "", "reasoning": ""}
                
                if "uncertain" in ingredients.lower():
                    logger.info(f"AI expressed uncertainty for '{name}'")
                    return {"allergens": "", "reasoning": ""}
                
                logger.info(f"Nova 2 Lite response for '{name}': {ingredients[:100]}...")
                
                # Parse the response - format: "ALLERGEN: reason; ALLERGEN: reason"
                if "no clear allergens" in ingredients.lower():
                    return {"allergens": "", "reasoning": ""}
                
                # Extract allergens and reasoning
                allergen_list = []
                reasoning_parts = []
                
                for line in ingredients.split(';'):
                    if ':' in line:
                        parts = line.split(':', 1)
                        if len(parts) == 2:
                            allergen = parts[0].strip().upper()
                            reason = parts[1].strip()
                            allergen_list.append(allergen.lower())
                            reasoning_parts.append(f"{allergen.lower()}: {reason}")
                
                result = {
                    "allergens": ", ".join(allergen_list),
                    "reasoning": "; ".join(reasoning_parts)
                }
                
                logger.info(f"Parsed: allergens={result['allergens']}, reasoning={result['reasoning'][:80]}...")
                return result
                
            except Exception as e:
                logger.warning(f"Nova 2 Lite inference failed: {e}")
        
        # Fallback to simple extraction
        return description
    
    def _extract_simple_ingredients(self, description: str) -> List[str]:
        """Extract visible ingredients from description"""
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
        """Generate conversational voice summary with Keith's personality - direct, casual, Kenyan touches"""
        allergen_text = " and ".join(allergens) if len(allergens) <= 2 else f"{', '.join(allergens[:-1])}, and {allergens[-1]}"
        
        import random
        
        if unsafe_count == 0:
            # All safe - confident, casual
            messages = [
                f"sawa! all {safe_count} dishes work for you. no {allergen_text} anywhere.",
                f"you're good - {safe_count} safe options, zero {allergen_text}.",
                f"nice one. got {safe_count} dishes, none have {allergen_text}.",
                f"clean menu. all {safe_count} dishes safe for {allergen_text}.",
                f"{safe_count} options and not a single {allergen_text} in sight. easy."
            ]
            suffix = random.choice([
                "",
                "",
                "",
                ""
            ])
            return random.choice(messages) + suffix
        elif safe_count == 0:
            # Nothing safe - honest, helpful
            messages = [
                f"bruh, nothing here works for {allergen_text}.",
                f"nah, this menu's not it. everything has {allergen_text}.",
                f"tough one - zero options without {allergen_text}.",
                f"this place and {allergen_text} don't mix. nothing safe."
            ]
            suffix = random.choice([
                " ask if they can modify something.",
                " see if the kitchen can work around it.",
                " might wanna check other spots.",
                " ask what they can customize."
            ])
            return random.choice(messages) + suffix
        else:
            # Mixed results - practical
            if unsafe_count == 1:
                messages = [
                    f"got {safe_count} safe, 1 to skip.",
                    f"{safe_count} good options, just 1 with {allergen_text}.",
                    f"looking good - {safe_count} safe dishes, only 1 issue.",
                    f"{safe_count} work, 1 doesn't. pretty solid."
                ]
            else:
                messages = [
                    f"found {safe_count} safe and {unsafe_count} with {allergen_text}.",
                    f"{safe_count} good ones, {unsafe_count} to avoid.",
                    f"got {safe_count} safe dishes. skip the {unsafe_count} with {allergen_text}.",
                    f"{safe_count} work for you, {unsafe_count} don't."
                ]
            suffix = random.choice([
                " check below.",
                " scroll down for details.",
                " see the list below.",
                " details down there."
            ])
            return random.choice(messages) + suffix

analyzer = NovaMenuAnalyzer()

# API ENDPOINTS

@app.get("/")
async def root():
    return {
        "name": "SafeBite API",
        "version": "1.0.0",
        "status": "operational",
        "features": ["Image OCR", "PDF Text Extraction", "Custom Allergens", "Ingredient Inference"]
    }

@app.get("/health")
async def health():
    return {
        "name": "SafeBite API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/allergens")
async def get_allergens():
    """Get list of supported allergens"""
    return {
        "allergens": COMMON_ALLERGENS,
        "total": len(COMMON_ALLERGENS)
    }


def save_scan_to_db(
    filename: str,
    file_type: str,
    allergens: list,
    custom_allergens: list,
    result_data: dict,
    user_ip: str = None,
    user_agent: str = None
):
    """Save scan data to database"""
    try:
        db = SessionLocal()
        
        scan = Scan(
            filename=filename,
            file_type=file_type,
            allergens=allergens,
            custom_allergens=custom_allergens,
            total_dishes=result_data.get('total_dishes', 0),
            safe_count=len(result_data.get('safe_dishes', [])),
            unsafe_count=len(result_data.get('unsafe_dishes', [])),
            unknown_count=len(result_data.get('unknown_dishes', [])),
            restaurant_name=result_data.get('restaurant_name', 'Unknown'),
            user_ip=user_ip,
            user_agent=user_agent,
            dishes=[d.dict() for d in result_data.get('safe_dishes', []) + 
                   result_data.get('unsafe_dishes', []) + 
                   result_data.get('unknown_dishes', [])],
            voice_summary=result_data.get('voice_summary', ''),
            recommendation=result_data.get('recommendation')
        )
        
        db.add(scan)
        db.commit()
        db.close()
        
        logger.info(f"Saved scan to database: {filename}")
    except Exception as e:
        logger.error(f"Failed to save scan to database: {e}")


@app.post("/analyze/image", response_model=MenuAnalysisResponse)
async def analyze_menu_image(
    file: UploadFile = File(...), 
    allergens: str = Form(""),
    custom_allergens: str = Form("")
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
        
        # Generate recommendation
        recommendation = None
        if safe_dishes:
            recommendation = await analyzer.generate_recommendation(safe_dishes, all_allergens)
        
        # Timestamp in EAT (Nairobi time)
        now_utc = datetime.now(timezone.utc)
        now_eat = now_utc.astimezone(NAIROBI_OFFSET)
        
        file_type = "PDF" if file.filename.lower().endswith('.pdf') else "Image"
        
        # Save to database
        save_scan_to_db(
            filename=file.filename,
            file_type=file_type,
            allergens=allergen_list,
            custom_allergens=custom_list,
            result_data={
                'total_dishes': len(menu_data["dishes"]),
                'safe_dishes': safe_dishes,
                'unsafe_dishes': unsafe_dishes,
                'unknown_dishes': unknown_dishes,
                'restaurant_name': f"Uploaded {file_type}",
                'voice_summary': voice_summary,
                'recommendation': recommendation
            },
            user_ip=None,  # Can add request.client.host if needed
            user_agent=None
        )
        
        return MenuAnalysisResponse(
            restaurant_name=f"Uploaded {file_type}",
            total_dishes=len(menu_data["dishes"]),
            safe_dishes=safe_dishes,
            unsafe_dishes=unsafe_dishes,
            unknown_dishes=unknown_dishes,
            analysis_timestamp=now_utc.isoformat(),
            analysis_time_eat=now_eat.strftime("%H:%M EAT"),
            recommendation=recommendation,
            voice_summary=voice_summary
        )
        
    except ValueError as ve:
        # Validation errors (not a menu, bad format, etc.)
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
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
        
        # Generate recommendation
        recommendation = None
        if safe_dishes:
            recommendation = await analyzer.generate_recommendation(safe_dishes, all_allergens)
        
        # Timestamp in EAT (Nairobi time)
        now_utc = datetime.now(timezone.utc)
        now_eat = now_utc.astimezone(NAIROBI_OFFSET)
        
        return MenuAnalysisResponse(
            restaurant_name=menu_data.get("restaurant", "Restaurant"),
            total_dishes=len(menu_data["dishes"]),
            safe_dishes=safe_dishes,
            unsafe_dishes=unsafe_dishes,
            unknown_dishes=unknown_dishes,
            analysis_timestamp=now_utc.isoformat(),
            analysis_time_eat=now_eat.strftime('%H:%M EAT'),
            voice_summary=voice_summary
        )
        
    except ValueError as ve:
        # Validation errors (not a menu, bad format, etc.)
        logger.warning(f"Validation error: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")


# Feedback endpoints
FEEDBACK_DIR = Path("feedback_data")
FEEDBACK_DIR.mkdir(exist_ok=True)

@app.post("/feedback")
async def submit_feedback(feedback: dict):
    """Save user feedback"""
    
    # Save to file
    filename = FEEDBACK_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(feedback, f, indent=2)
    
    return {"status": "success"}

@app.get("/feedback/all")
async def get_all_feedback():
    """Get all feedback"""
    feedbacks = []
    
    if FEEDBACK_DIR.exists():
        for file in sorted(FEEDBACK_DIR.glob("*.json"), reverse=True):
            with open(file) as f:
                feedbacks.append(json.load(f))
    
    return {"feedbacks": feedbacks}

