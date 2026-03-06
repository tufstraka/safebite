"""
AWS Textract OCR for Menu Extraction
"""

import boto3
import json
import base64
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class TextractMenuExtractor:
    """Extract menu text and structure using AWS Textract"""
    
    def __init__(self):
        self.textract = boto3.client('textract', region_name='us-east-1')
    
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
        Parse individual dishes from extracted text
        Strategy:
        1. Look for lines with prices ($ € £)
        2. Group nearby lines as dish name + description
        3. Extract dish → ingredients mapping
        """
        dishes = []
        lines = full_text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if line contains a price
            if any(symbol in line for symbol in ['$', '€', '£']):
                # This is likely a dish with price
                dish_name = line.split('$')[0].split('€')[0].split('£')[0].strip()
                price = line.split(dish_name)[-1].strip() if dish_name else line
                
                # Get description from next line(s)
                description = []
                j = i + 1
                while j < len(lines) and j < i + 3:  # Look ahead max 2 lines
                    next_line = lines[j].strip()
                    if next_line and not any(symbol in next_line for symbol in ['$', '€', '£']):
                        description.append(next_line)
                        j += 1
                    else:
                        break
                
                if dish_name:
                    dishes.append({
                        'name': dish_name,
                        'description': ' '.join(description),
                        'price': price,
                        'raw_text': line + ' ' + ' '.join(description)
                    })
                
                i = j
            else:
                i += 1
        
        # If no dishes found with price strategy, try capitalized names
        if not dishes:
            for line in lines:
                line = line.strip()
                if line and line[0].isupper() and len(line.split()) <= 5:
                    # Likely a dish name
                    dishes.append({
                        'name': line,
                        'description': '',
                        'price': 'N/A',
                        'raw_text': line
                    })
        
        logger.info(f"Parsed {len(dishes)} dishes from text")
        return dishes
    
    async def extract_from_pdf(self, pdf_bytes: bytes) -> Dict:
        """
        Extract text from PDF menu using Textract
        """
        try:
            logger.info("Calling AWS Textract for PDF extraction...")
            
            response = self.textract.detect_document_text(
                Document={'Bytes': pdf_bytes}
            )
            
            # Extract all text
            text_blocks = []
            for block in response.get('Blocks', []):
                if block['BlockType'] == 'LINE':
                    text_blocks.append({
                        'text': block['Text'],
                        'confidence': block['Confidence']
                    })
            
            full_text = '\n'.join([b['text'] for b in text_blocks])
            dishes = self._parse_dishes_from_text(full_text, text_blocks)
            
            return {
                'success': True,
                'full_text': full_text,
                'dishes': dishes,
                'extraction_confidence': sum(b['confidence'] for b in text_blocks) / len(text_blocks) if text_blocks else 0
            }
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'dishes': []
            }
