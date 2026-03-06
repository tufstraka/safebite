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
            
            # Call Nova 2 Lite
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'messages': [
                        {
                            'role': 'user',
                            'content': prompt
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
        """Build detailed prompt for Nova 2 Lite"""
        
        prompt = f"""You are SafeBite AI, an expert food allergen detection system.

**Task:** Analyze this dish for potential allergens.

**Dish Information:**
- Name: {dish_name}
- Description: {dish_description}
{f"- Extracted Ingredients: {', '.join(extracted_ingredients)}" if extracted_ingredients else ""}

**User's Allergens:** {', '.join(user_allergens)}

**Your Job:**
1. Identify if this dish contains ANY of the user's allergens
2. Consider HIDDEN allergens (e.g., butter in vegetables, flour in breading, fish sauce in Asian dishes)
3. Assess cross-contamination risks
4. Provide confidence score (0-100)

**Return ONLY valid JSON:**
{{
    "detected_allergens": ["peanuts", "milk"],
    "confidence": 95,
    "hidden_ingredients": ["butter used in cooking", "possible flour in batter"],
    "reasoning": "Pad Thai explicitly contains peanuts. Likely cooked in oil that may have peanut traces.",
    "safety_level": "unsafe",
    "ingredient_interactions": ["noodles fried in shared oil"]
}}

**Safety Levels:**
- "safe" - No allergens detected, high confidence
- "caution" - Possible allergen presence or cross-contamination
- "unsafe" - Confirmed allergen detected

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
                    'messages': [{'role': 'user', 'content': prompt}],
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
