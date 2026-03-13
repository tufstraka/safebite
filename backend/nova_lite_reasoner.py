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
            
            # Extract JSON from AI response
            analysis = self._parse_ai_response(ai_text)
            
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
    
    def _parse_ai_response(self, ai_text: str) -> Dict:
        """Parse JSON from AI response"""
        try:
            # Try to extract JSON from response
            start = ai_text.find('{')
            end = ai_text.rfind('}') + 1
            
            if start >= 0 and end > start:
                json_str = ai_text[start:end]
                return json.loads(json_str)
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
            
            prompt = f"""Look at this food image and identify:
1. What food/dish is this?
2. What are the likely ingredients?
3. Check for these allergens: {', '.join(user_allergens)}

Return JSON:
{{
    "food_name": "name of the food",
    "description": "brief description",
    "likely_ingredients": ["ingredient1", "ingredient2"],
    "detected_allergens": ["allergen1"] or [],
    "confidence": 0-100
}}

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
                    'inferenceConfig': {'temperature': 0.3, 'maxTokens': 500}
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
                return result
            else:
                return {
                    'food_name': 'Unknown Food',
                    'description': ai_text,
                    'likely_ingredients': [],
                    'detected_allergens': [],
                    'confidence': 30
                }
                
        except Exception as e:
            logger.error(f"Food photo analysis failed: {str(e)}")
            return None
