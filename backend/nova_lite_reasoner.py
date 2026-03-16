"""
Nova 2 Lite - AI Allergen Reasoning Engine
"""

import boto3
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class NovaLiteAllergenReasoner:
    """Use Nova 2 Lite for intelligent allergen detection and reasoning"""
    
    def __init__(self):
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
        self.model_id = 'us.amazon.nova-lite-v1:0'
    
    async def analyze_allergens(
        self,
        dish_name: str,
        dish_description: str,
        user_allergens: List[str],
        extracted_ingredients: Optional[List[str]] = None
    ) -> Dict:
        """
        Use Nova 2 Lite to reason about allergens in a dish
        
        Returns:
        - detected_allergens: List of allergens found
        - confidence: 0-100 score
        - hidden_ingredients: Ingredients not explicitly mentioned
        - reasoning: AI explanation
        - safety_level: safe/caution/unsafe
        """
        try:
            # Build prompt for Nova 2 Lite
            prompt = self._build_allergen_prompt(
                dish_name,
                dish_description,
                user_allergens,
                extracted_ingredients
            )
            
            logger.info(f"Calling Nova 2 Lite for allergen analysis: {dish_name}")
            
            # Call Nova 2 Lite - content must be an array
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'messages': [
                        {
                            'role': 'user',
                            'content': [{'text': prompt}]  # Must be array of content blocks
                        }
                    ],
                    'inferenceConfig': {
                        'temperature': 0.1,  # Low for accuracy
                        'maxTokens': 500,
                        'topP': 0.9
                    }
                })
            )
            
            # Parse response
            response_body = json.loads(response['body'].read())
            ai_text = response_body['output']['message']['content'][0]['text']
            
            # Extract JSON from AI response and validate against user allergens
            analysis = self._parse_ai_response(ai_text, user_allergens)
            
            logger.info(f"Nova 2 Lite detected {len(analysis.get('detected_allergens', []))} allergens")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Nova 2 Lite analysis failed: {str(e)}")
            return {
                'detected_allergens': [],
                'confidence': 0,
                'hidden_ingredients': [],
                'reasoning': f"Analysis failed: {str(e)}",
                'safety_level': 'unknown'
            }
    
    def _build_allergen_prompt(
        self,
        dish_name: str,
        dish_description: str,
        user_allergens: List[str],
        extracted_ingredients: Optional[List[str]]
    ) -> str:
        """Build detailed prompt for Nova 2 Lite with empathetic messaging"""
        
        allergens_list = ', '.join(user_allergens)
        
        prompt = f"""You are a caring food safety assistant helping someone with food allergies stay safe while dining out.

**Dish to analyze:**
- Name: {dish_name}
- Description: {dish_description}
{f"- Known Ingredients: {', '.join(extracted_ingredients)}" if extracted_ingredients else ""}

**CRITICAL: This person is ONLY allergic to: {allergens_list}**

**Your task:**
1. ONLY check if this dish contains the allergens listed above: {allergens_list}
2. DO NOT flag other allergens that the user is NOT allergic to
3. Think about hidden ingredients that might contain {allergens_list}
4. Consider cross-contamination risks ONLY for {allergens_list}

**VERY IMPORTANT RULES:**
- ONLY include allergens from this list in "detected_allergens": {allergens_list}
- If the dish contains nuts but user is NOT allergic to nuts, do NOT flag it
- If the dish contains shellfish but user is NOT allergic to shellfish, do NOT flag it
- ONLY flag allergens the user specifically told you they are allergic to
- The "detected_allergens" array should ONLY contain items from: [{allergens_list}]

**Write the "reasoning" in a warm, caring, conversational tone like you're talking to a friend but do not include a greeting:**
- If SAFE: Be encouraging! The dish doesn't contain {allergens_list}
- If CAUTION: Be helpful and caring. There might be {allergens_list} hidden
- If UNSAFE: Be clear but kind. The dish contains {allergens_list}

**Return ONLY valid JSON:**
{{
    "detected_allergens": [],
    "confidence": 85,
    "hidden_ingredients": ["list of typical ingredients"],
    "reasoning": "Your friendly message here",
    "safety_level": "safe"
}}

**Safety Levels (based ONLY on {allergens_list}):**
- "safe" - No {allergens_list} detected, looks good to eat!
- "caution" - Might contain {allergens_list}, worth double-checking with staff
- "unsafe" - Contains confirmed {allergens_list}, skip this one

Remember: ONLY flag {allergens_list}. Ignore all other allergens.

Analyze now:"""
        
        return prompt
    
    def _parse_ai_response(self, ai_text: str, user_allergens: List[str] = None) -> Dict:
        """Parse JSON from AI response and validate allergens"""
        try:
            # Try to extract JSON from response
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = ai_text[start:end]
                result = json.loads(json_str)
                
                # Validate allergens if user_allergens provided
                if user_allergens:
                    result = self._validate_allergen_response(result, user_allergens)
                
                return result
            else:
                # Fallback parsing
                return {
                    'detected_allergens': [],
                    'confidence': 50,
                    'hidden_ingredients': [],
                    'reasoning': ai_text,
                    'safety_level': 'unknown'
                }
                
        except json.JSONDecodeError:
            logger.warning(f"Could not parse AI response as JSON: {ai_text[:100]}")
            return {
                'detected_allergens': [],
                'confidence': 50,
                'hidden_ingredients': [],
                'reasoning': ai_text,
                'safety_level': 'unknown'
            }
    
    def _validate_allergen_response(self, result: Dict, user_allergens: List[str]) -> Dict:
        """
        CRITICAL: Validate AI response to prevent hallucination
        
        1. Ensure detected_allergens only contains user's specified allergens
        2. Cross-reference hidden_ingredients against user allergens
        3. Recalculate safety_level based on validated allergens
        """
        
        # Allergen keywords mapping
        allergen_indicators = {
            "eggs": ["egg", "eggs", "albumin", "mayonnaise", "mayo", "meringue", "aioli",
                     "custard", "hollandaise", "brioche", "pasta", "noodles", "cake",
                     "cookie", "cookies", "brownie", "muffin", "pancake", "waffle"],
            "milk": ["milk", "cream", "butter", "cheese", "yogurt", "dairy", "whey",
                     "casein", "lactose", "ghee", "ice cream", "chocolate", "caramel"],
            "wheat": ["wheat", "flour", "bread", "pasta", "noodles", "breadcrumb",
                      "breaded", "fried", "battered", "cookie", "cookies", "cake",
                      "pastry", "pie", "croissant", "muffin", "pancake", "waffle"],
            "gluten": ["wheat", "flour", "bread", "pasta", "noodles", "breadcrumb",
                       "breaded", "fried", "battered", "cookie", "cookies", "cake",
                       "pastry", "barley", "rye", "malt", "soy sauce"],
            "peanuts": ["peanut", "peanuts", "groundnut", "satay", "pad thai"],
            "tree nuts": ["almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut",
                          "macadamia", "praline", "marzipan", "nougat", "pesto"],
            "nuts": ["nut", "nuts", "almond", "walnut", "cashew", "pistachio", "pecan",
                     "hazelnut", "macadamia", "peanut", "praline", "marzipan"],
            "soy": ["soy", "soya", "tofu", "tempeh", "edamame", "miso", "soy sauce", "teriyaki"],
            "fish": ["fish", "salmon", "tuna", "cod", "anchovy", "bass", "trout", "halibut",
                     "fish sauce", "worcestershire"],
            "shellfish": ["shrimp", "prawn", "crab", "lobster", "clam", "oyster", "mussel",
                          "scallop", "crawfish"],
            "sesame": ["sesame", "tahini", "hummus"],
            "mustard": ["mustard", "dijon"],
            "celery": ["celery", "celeriac"]
        }
        
        user_allergens_lower = [a.lower().strip() for a in user_allergens]
        
        # Get AI's response data
        ai_detected = result.get('detected_allergens', [])
        hidden_ingredients = result.get('hidden_ingredients', [])
        
        # Combine all text for cross-reference
        all_text = ' '.join(hidden_ingredients).lower()
        
        # Step 1: Filter to only user's allergens
        validated_allergens = []
        for allergen in ai_detected:
            allergen_lower = allergen.lower().strip()
            if allergen_lower in user_allergens_lower:
                validated_allergens.append(allergen_lower)
        
        # Step 2: Cross-reference hidden ingredients
        for user_allergen in user_allergens_lower:
            if user_allergen in validated_allergens:
                continue
            
            indicators = allergen_indicators.get(user_allergen, [user_allergen])
            for indicator in indicators:
                if indicator.lower() in all_text:
                    validated_allergens.append(user_allergen)
                    logger.info(f"Cross-reference found {user_allergen} via '{indicator}' in hidden ingredients")
                    break
        
        # Remove duplicates
        validated_allergens = list(dict.fromkeys(validated_allergens))
        
        # Step 3: Recalculate safety level based on validated allergens
        if validated_allergens:
            result['safety_level'] = 'unsafe'
            result['detected_allergens'] = validated_allergens
        else:
            # Only mark as safe if we're confident no user allergens are present
            if result.get('safety_level') == 'safe':
                result['safety_level'] = 'safe'
            elif result.get('safety_level') == 'caution':
                result['safety_level'] = 'caution'
            result['detected_allergens'] = []
        
        # Log validation
        if set(ai_detected) != set(validated_allergens):
            logger.info(f"Allergen validation: AI detected {ai_detected} -> validated to {validated_allergens}")
        
        return result
    
    async def infer_hidden_ingredients(
        self,
        dish_name: str,
        dish_description: str
    ) -> List[str]:
        """
        Use Nova 2 Lite to infer ingredients not explicitly mentioned
        Useful for detecting hidden allergens
        """
        try:
            prompt = f"""Based on standard recipes, what ingredients does "{dish_name}" typically contain?

Description: {dish_description}

List ALL ingredients including hidden ones (butter, milk, eggs in baked goods, flour in breading, etc.).

Return ONLY a JSON array of ingredient names:
["flour", "butter", "milk", "eggs", "sugar"]

Respond now:"""
            
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'messages': [{'role': 'user', 'content': [{'text': prompt}]}],
                    'inferenceConfig': {'temperature': 0.2, 'maxTokens': 200}
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_text = response_body['output']['message']['content'][0]['text']
            
            # Extract JSON array
            start = ai_text.find('[')
            end = ai_text.rfind(']') + 1
            
            if start >= 0 and end > start:
                ingredients = json.loads(ai_text[start:end])
                return ingredients
            else:
                return []
                
        except Exception as e:
            logger.error(f"Hidden ingredient inference failed: {str(e)}")
            return []
    
    async def analyze_food_photo(
        self,
        image_bytes: bytes,
        user_allergens: List[str]
    ) -> Dict:
        """
        Analyze a food photo (not a menu) using Nova's vision capabilities
        Identifies the food and potential allergens
        
        CRITICAL: This function validates that detected allergens are ONLY from user's list
        and cross-references inferred ingredients against user allergens
        """
        try:
            import base64
            
            # Encode image to base64
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
            
            # Determine image type
            if image_bytes[:8] == b'\x89PNG\r\n\x1a\n':
                media_type = 'image/png'
            elif image_bytes[:2] == b'\xff\xd8':
                media_type = 'image/jpeg'
            else:
                media_type = 'image/jpeg'  # Default
            
            allergens_list = ', '.join(user_allergens)
            
            prompt = f"""You are a caring food safety assistant helping someone with food allergies stay safe. Look at this food image and help them understand if it's safe to eat.

**CRITICAL: This person is ONLY allergic to: {allergens_list}**
Their wellbeing depends on your careful analysis.

**Your task:**
1. Identify what food/dish this is
2. List ALL likely ingredients (including hidden ones like eggs in baked goods, butter, flour, etc.)
3. Check if ANY of the likely ingredients contain or are related to: {allergens_list}

**IMPORTANT RULES:**
- ONLY include allergens from this exact list in "detected_allergens": [{allergens_list}]
- If you identify an ingredient that contains a user's allergen (e.g., cookies often contain eggs, and user is allergic to eggs), you MUST flag it
- Be thorough - baked goods often contain eggs, milk, wheat
- Fried foods often contain wheat (flour)
- Many sauces contain eggs (mayonnaise, aioli)
- If there's ANY possibility the food contains {allergens_list}, flag it

**Write the "safety_reasoning" in a warm, caring, conversational tone like you're talking to a friend (but do not include a greeting):**
- If SAFE: Be encouraging and reassuring! "This looks great for you! No {allergens_list} detected here..."
- If CAUTION: Be helpful and caring. "I'd suggest double-checking this one - there might be {allergens_list} hidden..."
- If UNSAFE: Be clear but kind and supportive. "I'd skip this one - it contains {allergens_list}..."

**Return JSON:**
{{
    "food_name": "name of the food",
    "description": "brief description",
    "likely_ingredients": ["ingredient1", "ingredient2", "..."],
    "detected_allergens": ["ONLY allergens from: {allergens_list}"],
    "confidence": 0-100,
    "safety_reasoning": "Your friendly, empathetic message here - be warm and supportive!"
}}

Remember: If cookies likely contain eggs and user is allergic to eggs, detected_allergens MUST include "eggs".
If the food likely contains ANY of [{allergens_list}], it MUST be in detected_allergens.

Respond with ONLY the JSON:"""

            logger.info("Calling Nova for food photo analysis...")
            
            # Call Nova with image
            response = self.bedrock.invoke_model(
                modelId='us.amazon.nova-lite-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'messages': [{
                        'role': 'user',
                        'content': [
                            {
                                'image': {
                                    'format': media_type.split('/')[1],
                                    'source': {'bytes': image_base64}
                                }
                            },
                            {'text': prompt}
                        ]
                    }],
                    'inferenceConfig': {'temperature': 0.2, 'maxTokens': 700}  # Lower temp for accuracy
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_text = response_body['output']['message']['content'][0]['text']
            
            # Parse JSON response
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                result = json.loads(ai_text[start:end])
                logger.info(f"Nova identified food: {result.get('food_name', 'Unknown')}")
                
                # CRITICAL POST-PROCESSING: Validate and cross-reference allergens
                result = self._validate_and_cross_reference_allergens(result, user_allergens)
                
                return result
            else:
                return {
                    'food_name': 'Unknown Food',
                    'description': ai_text,
                    'likely_ingredients': [],
                    'detected_allergens': [],
                    'confidence': 30,
                    'safety_reasoning': 'Could not analyze image properly'
                }
                
        except Exception as e:
            logger.error(f"Food photo analysis failed: {str(e)}")
            return None
    
    def _validate_and_cross_reference_allergens(
        self,
        ai_result: Dict,
        user_allergens: List[str]
    ) -> Dict:
        """
        CRITICAL: Post-process AI response to prevent hallucination
        
        1. Remove any detected allergens NOT in user's list
        2. Cross-reference inferred ingredients against user allergens
        3. Add any missed allergens based on ingredient analysis
        """
        
        # Allergen keywords mapping - ingredients that indicate presence of allergens
        allergen_indicators = {
            "eggs": ["egg", "eggs", "albumin", "mayonnaise", "mayo", "meringue", "aioli",
                     "custard", "hollandaise", "béarnaise", "brioche", "challah", "pasta",
                     "noodles", "cake", "cookie", "cookies", "brownie", "muffin", "pancake",
                     "waffle", "french toast", "quiche", "soufflé", "ice cream", "gelato"],
            "milk": ["milk", "cream", "butter", "cheese", "yogurt", "dairy", "whey",
                     "casein", "lactose", "ghee", "ice cream", "gelato", "chocolate",
                     "caramel", "custard", "pudding", "béchamel", "alfredo"],
            "wheat": ["wheat", "flour", "bread", "pasta", "noodles", "breadcrumb",
                      "breaded", "fried", "battered", "cookie", "cookies", "cake",
                      "pastry", "pie", "croissant", "muffin", "pancake", "waffle",
                      "cracker", "cereal", "couscous", "bulgur", "seitan", "soy sauce"],
            "gluten": ["wheat", "flour", "bread", "pasta", "noodles", "breadcrumb",
                       "breaded", "fried", "battered", "cookie", "cookies", "cake",
                       "pastry", "pie", "croissant", "muffin", "barley", "rye", "malt",
                       "beer", "soy sauce", "seitan"],
            "peanuts": ["peanut", "peanuts", "groundnut", "arachis", "satay", "pad thai"],
            "tree nuts": ["almond", "almonds", "walnut", "walnuts", "cashew", "cashews",
                          "pistachio", "pistachios", "pecan", "pecans", "hazelnut",
                          "hazelnuts", "macadamia", "brazil nut", "pine nut", "pine nuts",
                          "praline", "marzipan", "nougat", "pesto"],
            "nuts": ["nut", "nuts", "almond", "walnut", "cashew", "pistachio", "pecan",
                     "hazelnut", "macadamia", "peanut", "praline", "marzipan", "nougat"],
            "soy": ["soy", "soya", "tofu", "tempeh", "edamame", "miso", "soy sauce",
                    "teriyaki", "tamari"],
            "fish": ["fish", "salmon", "tuna", "cod", "anchovy", "anchovies", "bass",
                     "trout", "halibut", "tilapia", "sardine", "sardines", "mackerel",
                     "fish sauce", "worcestershire"],
            "shellfish": ["shrimp", "prawn", "prawns", "crab", "lobster", "clam", "clams",
                          "oyster", "oysters", "mussel", "mussels", "scallop", "scallops",
                          "crawfish", "crayfish", "langoustine"],
            "sesame": ["sesame", "tahini", "hummus", "halvah", "gomashio"],
            "mustard": ["mustard", "dijon"],
            "celery": ["celery", "celeriac"]
        }
        
        # Normalize user allergens
        user_allergens_lower = [a.lower().strip() for a in user_allergens]
        
        # Get AI's detected allergens and likely ingredients
        ai_detected = ai_result.get('detected_allergens', [])
        likely_ingredients = ai_result.get('likely_ingredients', [])
        food_name = ai_result.get('food_name', '').lower()
        description = ai_result.get('description', '').lower()
        
        # Combine all text for searching
        all_text = f"{food_name} {description} {' '.join(likely_ingredients)}".lower()
        
        # Step 1: Filter AI detected allergens to ONLY include user's allergens
        validated_allergens = []
        for allergen in ai_detected:
            allergen_lower = allergen.lower().strip()
            if allergen_lower in user_allergens_lower:
                validated_allergens.append(allergen_lower)
        
        # Step 2: Cross-reference ingredients against user allergens
        # This catches cases where AI identified "eggs" in ingredients but didn't flag it
        for user_allergen in user_allergens_lower:
            if user_allergen in validated_allergens:
                continue  # Already detected
            
            # Get indicators for this allergen
            indicators = allergen_indicators.get(user_allergen, [user_allergen])
            
            # Check if any indicator is present in the text
            for indicator in indicators:
                if indicator.lower() in all_text:
                    validated_allergens.append(user_allergen)
                    logger.info(f"Cross-reference detected {user_allergen} via indicator '{indicator}'")
                    break
        
        # Remove duplicates while preserving order
        validated_allergens = list(dict.fromkeys(validated_allergens))
        
        # Update the result
        ai_result['detected_allergens'] = validated_allergens
        
        # Add validation note if we modified the results
        original_count = len(ai_detected)
        final_count = len(validated_allergens)
        
        if original_count != final_count or set(ai_detected) != set(validated_allergens):
            ai_result['validation_applied'] = True
            ai_result['validation_note'] = (
                f"Cross-referenced {len(likely_ingredients)} ingredients against "
                f"user allergens [{', '.join(user_allergens)}]. "
                f"Found {final_count} relevant allergens."
            )
            logger.info(f"Allergen validation: {original_count} AI detected -> {final_count} validated")
        
        return ai_result
