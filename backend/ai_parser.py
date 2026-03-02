"""
AI-powered menu parsing using Nova 2 Lite
"""
import json
import logging

logger = logging.getLogger(__name__)

async def parse_menu_with_ai(bedrock_client, text: str):
    """Use Nova 2 Lite to intelligently parse dishes from menu text"""
    if not bedrock_client or not text or len(text) < 50:
        return []
    
    try:
        logger.info("Using AI to parse menu text...")
        
        # Clean and prepare text (limit to reasonable size)
        text = text[:4000]  # Limit for token efficiency
        
        prompt = f"""Extract all food/drink items from this menu text. Return ONLY a JSON array.

Menu text:
{text}

Rules:
1. Include ONLY actual food/drink items (dishes, meals, beverages)
2. Skip headers, footers, restaurant info, "prices subject to change", etc.
3. Include the dish name and brief description if available
4. If price is visible, include it

Format (valid JSON array):
[
  {{"name": "Grilled Chicken Caesar", "description": "Romaine, parmesan, croutons", "price": "$12.99"}},
  {{"name": "Margherita Pizza", "description": "Fresh mozzarella, basil", "price": "$14.50"}}
]

Return ONLY the JSON array, no other text:"""

        response = bedrock_client.invoke_model(
            modelId="us.amazon.nova-lite-v1:0",
            body=json.dumps({
                "messages": [{"role": "user", "content": [{"text": prompt}]}],
                "inferenceConfig": {
                    "temperature": 0.1,  # Low temperature for structured output
                    "maxTokens": 2000
                }
            })
        )
        
        result = json.loads(response['body'].read())
        ai_text = result['output']['message']['content'][0]['text'].strip()
        
        # Extract JSON array from response
        # Handle cases where AI adds markdown formatting
        if '```json' in ai_text:
            ai_text = ai_text.split('```json')[1].split('```')[0].strip()
        elif '```' in ai_text:
            ai_text = ai_text.split('```')[1].split('```')[0].strip()
        
        # Remove any leading/trailing text
        start = ai_text.find('[')
        end = ai_text.rfind(']')
        if start >= 0 and end > start:
            ai_text = ai_text[start:end+1]
        
        dishes = json.loads(ai_text)
        
        # Validate structure
        if isinstance(dishes, list) and len(dishes) > 0:
            logger.info(f"AI parsed {len(dishes)} dishes")
            
            # Ensure all dishes have required fields
            validated = []
            for dish in dishes:
                if isinstance(dish, dict) and 'name' in dish:
                    validated.append({
                        'name': dish.get('name', '').strip(),
                        'description': dish.get('description', dish.get('name', '')).strip(),
                        'price': dish.get('price', '$0.00')
                    })
            
            return validated if len(validated) > 0 else []
        
        logger.warning("AI parsing returned invalid structure")
        return []
        
    except json.JSONDecodeError as e:
        logger.error(f"AI parsing JSON decode error: {e}")
        return []
    except Exception as e:
        logger.error(f"AI parsing failed: {e}")
        return []
