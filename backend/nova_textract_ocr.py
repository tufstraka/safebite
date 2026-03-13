"""
AWS Textract OCR for Menu Extraction
"""

import boto3
import json
import base64
import io
import re
from typing import List, Dict, Optional
import logging
from PyPDF2 import PdfReader

logger = logging.getLogger(__name__)

class TextractMenuExtractor:
    """Extract menu text and structure using AWS Textract"""
    
    def __init__(self):
        self.textract = boto3.client('textract', region_name='us-east-1')
        
        # Patterns to filter out non-dish items
        self.skip_patterns = [
            r'^page\s*\d+',  # Page numbers
            r'^\d+\s*$',  # Just numbers
            r'^\d+\s+\d+',  # Multiple numbers (like "820 890650")
            r'^\d{6,}',  # Long number sequences (like "990690690690")
            r'^box\s*\d+',  # Box numbers
            r'^\+',  # Items starting with +
            r'^(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',  # Days
            r'^(january|february|march|april|may|june|july|august|september|october|november|december)',  # Months
            r'^(breakfast|lunch|dinner|brunch|menu|specials?|sides?|desserts?|drinks?|beverages?|wines?|beers?|cocktails?|starters?|mains?|appetizers?|entrees?|salads?|soups?|sandwiches?|burgers?|pizzas?|pastas?|seafood|vegetarian|vegan|gluten.?free|gf|v|vg)\s*$',  # Section headers
            r'^(to start|to share|from the grill|from the sea|chef.?s? specials?|today.?s? specials?|house specials?)\s*$',
            r'^(accompanied by|served with|choice of|includes?|add|extra)\s*:?\s*$',
            r'^(white|red|rose|sparkling|champagne|prosecco)\s*$',  # Wine categories
            r'^\d+\s*ml\s*$',  # Volume measurements
            r'^bottle\s*$',
            r'^glass\s*$',
            r'^(small|medium|large|regular|half|full)\s*$',  # Sizes
            r'^(hot|cold|iced)\s*$',
            r'^\s*$',  # Empty lines
            r'^[a-z\s]{1,3}$',  # Very short text (likely abbreviations)
            r'^(all|our|the|a|an|and|or|with|for|from|by)\s',  # Starting with articles/prepositions
            r'(allergen|allergy|dietary|nutrition|calorie|kcal|kj)',  # Allergen info headers
            r'(please ask|ask your server|let us know|inform)',  # Service notes
            r'(copyright|©|\(c\)|all rights reserved)',  # Copyright
            r'(www\.|http|\.com|\.co\.uk|@)',  # URLs/emails
            r'(tel:|phone:|fax:|email:)',  # Contact info
            r'(opening hours|open|closed|reservation)',  # Business info
            r'^\d+\s*litre',  # Volume items like "2 litre"
            r'^cold\s*drink',  # Generic drink items
            r'^soft\s*drink',
            r'^\d+\s*piece',  # Piece counts
            r'^combo\s*\d+',  # Combo numbers
            r'^meal\s*\d+',  # Meal numbers
            r'^deal\s*\d+',  # Deal numbers
            r'^offer\s*\d+',  # Offer numbers
        ]
        
        # Patterns that indicate a real dish (must have price or be substantial)
        self.dish_indicators = [
            r'\d+\.\d{2}',  # Price pattern (e.g., 12.95)
            r'[£$€]\s*\d+',  # Currency symbol with number
            r'KSh\s*\d+',  # Kenyan Shilling
        ]
    
    def _is_likely_dish(self, text: str) -> bool:
        """Check if text is likely a dish name vs header/footer"""
        text_lower = text.lower().strip()
        
        # Skip if matches any skip pattern
        for pattern in self.skip_patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return False
        
        # Skip if too short (less than 4 chars) or too long (more than 100 chars)
        if len(text_lower) < 4 or len(text_lower) > 100:
            return False
        
        # Skip if all uppercase and short (likely a header)
        if text.isupper() and len(text.split()) <= 2 and not any(re.search(p, text) for p in self.dish_indicators):
            return False
        
        return True
    
    def _clean_dish_name(self, text: str) -> str:
        """Clean up dish name by removing prices and extra formatting"""
        # Remove price patterns
        cleaned = re.sub(r'\s*[£$€]?\s*\d+\.\d{2}\s*', ' ', text)
        cleaned = re.sub(r'\s*KSh\s*\d+\s*', ' ', cleaned)
        
        # Remove dietary indicators at the end (keep them for description)
        cleaned = re.sub(r'\s+(V|VG|GF|DF|N)\s*$', '', cleaned, flags=re.IGNORECASE)
        
        # Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
    
    def _extract_price(self, text: str) -> str:
        """Extract price from text"""
        # Look for price patterns
        price_match = re.search(r'([£$€]?\s*\d+\.\d{2}|KSh\s*\d+)', text)
        if price_match:
            return price_match.group(1).strip()
        return 'N/A'
    
    def _extract_dietary_info(self, text: str) -> str:
        """Extract dietary indicators (V, VG, GF, etc.)"""
        indicators = []
        if re.search(r'\bV\b', text):
            indicators.append('Vegetarian')
        if re.search(r'\bVG\b', text):
            indicators.append('Vegan')
        if re.search(r'\bGF\b', text):
            indicators.append('Gluten-Free')
        if re.search(r'\bDF\b', text):
            indicators.append('Dairy-Free')
        if re.search(r'\bN\b', text):
            indicators.append('Contains Nuts')
        return ', '.join(indicators) if indicators else ''
    
    async def extract_menu_from_image(self, image_bytes: bytes) -> Dict:
        """
        Extract text from menu image using AWS Textract
        Returns structured dish data
        """
        try:
            logger.info("Calling AWS Textract for menu extraction...")
            
            response = self.textract.detect_document_text(
                Document={'Bytes': image_bytes}
            )
            
            # Extract all text blocks
            text_blocks = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_blocks.append({
                        'text': block['Text'],
                        'confidence': block['Confidence']
                    })
            
            # Combine into full text
            full_text = '\n'.join([b['text'] for b in text_blocks])
            
            logger.info(f"Textract extracted {len(text_blocks)} text lines")
            
            # Parse dishes from extracted text
            dishes = self._parse_dishes_from_text(full_text, text_blocks)
            
            return {
                'success': True,
                'full_text': full_text,
                'text_blocks': text_blocks,
                'dishes': dishes,
                'extraction_confidence': sum(b['confidence'] for b in text_blocks) / len(text_blocks) if text_blocks else 0
            }
            
        except Exception as e:
            logger.error(f"Textract extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'dishes': []
            }
    
    def _parse_dishes_from_text(self, full_text: str, text_blocks: List[Dict]) -> List[Dict]:
        """
        Parse individual dishes from extracted text with smart filtering
        """
        dishes = []
        lines = full_text.split('\n')
        seen_names = set()  # Avoid duplicates
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Check if line has a price (strong indicator of a dish)
            has_price = bool(re.search(r'\d+\.\d{2}', line))
            
            # Skip if not likely a dish
            if not self._is_likely_dish(line):
                continue
            
            # Extract components
            dish_name = self._clean_dish_name(line)
            price = self._extract_price(line)
            dietary_info = self._extract_dietary_info(line)
            
            # Skip if dish name is too short after cleaning
            if len(dish_name) < 3:
                continue
            
            # Skip duplicates
            name_lower = dish_name.lower()
            if name_lower in seen_names:
                continue
            seen_names.add(name_lower)
            
            # Get description from next line if it doesn't look like another dish
            description = dietary_info
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                # If next line is descriptive (no price, lowercase start, etc.)
                if next_line and not re.search(r'\d+\.\d{2}', next_line) and len(next_line) > 10:
                    if next_line[0].islower() or next_line.startswith('with') or next_line.startswith('served'):
                        description = (description + ' ' + next_line).strip() if description else next_line
            
            dishes.append({
                'name': dish_name,
                'description': description,
                'price': price,
                'raw_text': line
            })
        
        logger.info(f"Parsed {len(dishes)} dishes from text (filtered from {len(lines)} lines)")
        return dishes
    
    async def clean_dishes_with_ai(self, raw_dishes: List[Dict]) -> List[Dict]:
        """
        Use Nova AI to filter and clean the extracted dishes
        Removes non-food items, garbage text, and formats dish names properly
        """
        if not raw_dishes:
            return []
        
        try:
            import boto3
            bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            
            # Prepare dish names for AI review
            dish_names = [d['name'] for d in raw_dishes[:50]]  # Limit to 50 for API
            
            prompt = f"""You are a menu parser. From this list of extracted text, identify ONLY actual food/drink items.

**Extracted text:**
{chr(10).join(dish_names)}

**STRICT RULES - EXCLUDE these:**
1. Single words like "Sticky", "Chicken", "Original" (incomplete names)
2. Items with numbers attached like "Lunch Box390", "Streetwise Mix330"
3. Menu titles like "KFC Full Menu", "Restaurant Menu"
4. Generic items like "Recipe", "Burger" alone
5. Items starting with numbers or symbols
6. Concatenated words like "BurgerLegend" (should be "Legend Burger")
7. Items with "Box" in the name (usually combo codes)

**INCLUDE only:**
- Complete dish names like "Zinger Burger", "Hot Wings", "Caesar Salad"
- Drinks like "Coca Cola", "Orange Juice"
- Sides like "French Fries", "Coleslaw"

**Clean up names:**
- Separate concatenated words: "BurgerDouble" → "Double Burger"
- Remove trailing numbers: "Wings390" → "Wings"
- Fix spacing: "HotWings" → "Hot Wings"

**Return ONLY a JSON array of clean, complete dish names:**
["Zinger Burger", "Hot Wings", "French Fries"]

If no valid dishes found, return: []

JSON array:"""

            response = bedrock.invoke_model(
                modelId='us.amazon.nova-lite-v1:0',
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    'messages': [{'role': 'user', 'content': [{'text': prompt}]}],
                    'inferenceConfig': {'temperature': 0.1, 'maxTokens': 2000}
                })
            )
            
            response_body = json.loads(response['body'].read())
            ai_text = response_body['output']['message']['content'][0]['text']
            
            # Parse JSON array from response
            start = ai_text.find('[')
            end = ai_text.rfind(']') + 1
            
            if start >= 0 and end > start:
                clean_names = json.loads(ai_text[start:end])
                
                # Create clean dishes with the AI-cleaned names
                clean_dishes = []
                for clean_name in clean_names:
                    # Skip if name is too short or looks invalid
                    if len(clean_name) < 4:
                        continue
                    if clean_name.lower() in ['menu', 'recipe', 'original', 'sticky', 'chicken', 'burger']:
                        continue
                    
                    # Find matching original dish for price/description
                    matched_dish = None
                    clean_lower = clean_name.lower()
                    for dish in raw_dishes:
                        if clean_lower in dish['name'].lower() or dish['name'].lower() in clean_lower:
                            matched_dish = dish
                            break
                    
                    clean_dishes.append({
                        'name': clean_name,
                        'description': matched_dish.get('description', '') if matched_dish else '',
                        'price': matched_dish.get('price', 'N/A') if matched_dish else 'N/A',
                        'raw_text': matched_dish.get('raw_text', '') if matched_dish else ''
                    })
                
                logger.info(f"AI cleaned {len(raw_dishes)} dishes to {len(clean_dishes)} valid items")
                return clean_dishes
            
            return raw_dishes  # Fallback to original if parsing fails
            
        except Exception as e:
            logger.error(f"AI dish cleaning failed: {str(e)}")
            return raw_dishes  # Fallback to original dishes
    
    async def extract_from_pdf(self, pdf_bytes: bytes) -> Dict:
        """
        Extract text from PDF menu using PyPDF2
        Falls back to Textract for scanned PDFs
        """
        try:
            logger.info("Extracting text from PDF using PyPDF2...")
            
            # Try PyPDF2 first (works for text-based PDFs)
            pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
            
            all_text = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    all_text.append(page_text)
            
            full_text = '\n'.join(all_text)
            
            if full_text.strip():
                logger.info(f"PyPDF2 extracted {len(full_text)} characters from PDF")
                
                # Create text blocks for compatibility
                text_blocks = [{'text': line, 'confidence': 95} for line in full_text.split('\n') if line.strip()]
                
                dishes = self._parse_dishes_from_text(full_text, text_blocks)
                
                return {
                    'success': True,
                    'full_text': full_text,
                    'dishes': dishes,
                    'extraction_confidence': 95,
                    'method': 'pypdf2'
                }
            else:
                # PDF might be scanned (image-based), return error
                logger.warning("PDF appears to be scanned/image-based. Please upload as image instead.")
                return {
                    'success': False,
                    'error': 'PDF appears to be scanned/image-based. Please take a photo of the menu or upload as an image (JPG, PNG).',
                    'dishes': []
                }
                
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return {
                'success': False,
                'error': f'PDF extraction failed: {str(e)}. Try uploading as an image instead.',
                'dishes': []
            }
