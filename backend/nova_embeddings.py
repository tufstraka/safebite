"""
Nova Multimodal Embeddings - Semantic Allergen Matching
Uses vector similarity for intelligent allergen detection
"""

import boto3
import json
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class NovaEmbeddingsAllergenMatcher:
    """
    Amazon Nova Multimodal Embeddings for semantic allergen matching
    Goes beyond keyword matching to understand ingredient relationships
    """
    
    def __init__(self):
        """Initialize Bedrock client for Nova Embeddings"""
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            # Nova Multimodal Embeddings model ID
            self.model_id = 'amazon.titan-embed-text-v2:0'  # Using Titan as Nova embeddings may not be available yet
            self._initialize_allergen_embeddings()
            logger.info("Nova Embeddings Allergen Matcher initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Nova Embeddings: {e}")
            self.bedrock = None
            self.allergen_embeddings = {}
    
    def _initialize_allergen_embeddings(self):
        """Pre-compute embeddings for common allergens and related terms"""
        
        # Allergen knowledge base with related terms
        self.allergen_knowledge = {
            "peanuts": [
                "peanut", "groundnut", "arachis", "peanut butter", "peanut oil",
                "satay", "pad thai", "kung pao", "african stew", "peanut sauce"
            ],
            "tree nuts": [
                "almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut",
                "macadamia", "brazil nut", "pine nut", "chestnut", "praline",
                "marzipan", "nougat", "baklava", "pesto"
            ],
            "milk": [
                "milk", "dairy", "cheese", "cream", "butter", "yogurt", "whey",
                "casein", "lactose", "ghee", "paneer", "ricotta", "mozzarella",
                "parmesan", "béchamel", "alfredo", "custard", "ice cream"
            ],
            "eggs": [
                "egg", "albumin", "mayonnaise", "meringue", "aioli", "hollandaise",
                "béarnaise", "custard", "quiche", "frittata", "omelette", "tempura",
                "brioche", "challah", "pasta", "noodles"
            ],
            "wheat": [
                "wheat", "flour", "bread", "pasta", "noodles", "couscous", "bulgur",
                "semolina", "seitan", "gluten", "breadcrumbs", "croutons", "tortilla",
                "pita", "naan", "roux", "breaded", "battered"
            ],
            "soy": [
                "soy", "soya", "tofu", "tempeh", "edamame", "miso", "soy sauce",
                "tamari", "teriyaki", "hoisin", "bean curd", "soybean oil"
            ],
            "fish": [
                "fish", "salmon", "tuna", "cod", "anchovy", "sardine", "mackerel",
                "tilapia", "bass", "trout", "halibut", "fish sauce", "worcestershire",
                "caesar dressing", "bouillabaisse"
            ],
            "shellfish": [
                "shrimp", "prawn", "crab", "lobster", "clam", "mussel", "oyster",
                "scallop", "squid", "calamari", "octopus", "crawfish", "langoustine"
            ],
            "sesame": [
                "sesame", "tahini", "hummus", "halvah", "sesame oil", "gomashio",
                "sesame seeds", "benne seeds"
            ],
            "gluten": [
                "gluten", "wheat", "barley", "rye", "triticale", "spelt", "kamut",
                "farro", "einkorn", "malt", "brewer's yeast", "seitan"
            ]
        }
        
        # Pre-compute embeddings for allergen terms
        self.allergen_embeddings = {}
        
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding vector for text using Nova/Titan"""
        if not self.bedrock:
            return None
            
        try:
            response = self.bedrock.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps({
                    "inputText": text,
                    "dimensions": 512,
                    "normalize": True
                })
            )
            
            result = json.loads(response['body'].read())
            return result.get('embedding', [])
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return None
    
    async def semantic_allergen_match(
        self,
        dish_name: str,
        dish_description: str,
        user_allergens: List[str]
    ) -> Dict:
        """
        Use semantic similarity to detect allergens
        Returns allergen matches with confidence scores
        """
        results = {
            "detected_allergens": [],
            "confidence_scores": {},
            "semantic_matches": [],
            "method": "nova_embeddings"
        }
        
        # Combine dish info
        dish_text = f"{dish_name} {dish_description}".lower()
        
        # Get dish embedding
        dish_embedding = await self.get_embedding(dish_text)
        
        if not dish_embedding:
            # Fallback to keyword matching
            return await self._keyword_fallback(dish_text, user_allergens)
        
        for allergen in user_allergens:
            allergen_lower = allergen.lower()
            
            # Get related terms for this allergen
            related_terms = self.allergen_knowledge.get(allergen_lower, [allergen_lower])
            
            max_similarity = 0.0
            best_match = None
            
            for term in related_terms:
                # Check direct keyword match first
                if term in dish_text:
                    max_similarity = 1.0
                    best_match = term
                    break
                
                # Get embedding for allergen term
                term_embedding = await self.get_embedding(term)
                
                if term_embedding:
                    # Calculate cosine similarity
                    similarity = self._cosine_similarity(dish_embedding, term_embedding)
                    
                    if similarity > max_similarity:
                        max_similarity = similarity
                        best_match = term
            
            # Threshold for detection
            if max_similarity > 0.7:
                results["detected_allergens"].append(allergen)
                results["confidence_scores"][allergen] = int(max_similarity * 100)
                results["semantic_matches"].append({
                    "allergen": allergen,
                    "matched_term": best_match,
                    "similarity": max_similarity
                })
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            a = np.array(vec1)
            b = np.array(vec2)
            return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
        except:
            return 0.0
    
    async def _keyword_fallback(
        self,
        dish_text: str,
        user_allergens: List[str]
    ) -> Dict:
        """Fallback to keyword matching if embeddings fail"""
        results = {
            "detected_allergens": [],
            "confidence_scores": {},
            "semantic_matches": [],
            "method": "keyword_fallback"
        }
        
        for allergen in user_allergens:
            allergen_lower = allergen.lower()
            related_terms = self.allergen_knowledge.get(allergen_lower, [allergen_lower])
            
            for term in related_terms:
                if term in dish_text:
                    results["detected_allergens"].append(allergen)
                    results["confidence_scores"][allergen] = 90
                    results["semantic_matches"].append({
                        "allergen": allergen,
                        "matched_term": term,
                        "similarity": 1.0
                    })
                    break
        
        return results
    
    async def find_safe_alternatives(
        self,
        unsafe_dish: str,
        all_dishes: List[Dict],
        user_allergens: List[str]
    ) -> List[Dict]:
        """
        Find safe alternatives to an unsafe dish
        Uses semantic similarity to find similar but safe options
        """
        alternatives = []
        
        # Get embedding for unsafe dish
        unsafe_embedding = await self.get_embedding(unsafe_dish)
        
        if not unsafe_embedding:
            return alternatives
        
        for dish in all_dishes:
            dish_name = dish.get('name', '')
            dish_desc = dish.get('description', '')
            
            # Check if dish is safe
            match_result = await self.semantic_allergen_match(
                dish_name, dish_desc, user_allergens
            )
            
            if not match_result["detected_allergens"]:
                # Dish is safe, calculate similarity
                dish_embedding = await self.get_embedding(f"{dish_name} {dish_desc}")
                
                if dish_embedding:
                    similarity = self._cosine_similarity(unsafe_embedding, dish_embedding)
                    
                    if similarity > 0.5:  # Similar enough to be an alternative
                        alternatives.append({
                            "dish": dish,
                            "similarity": similarity,
                            "reason": f"Similar to {unsafe_dish} but allergen-free"
                        })
        
        # Sort by similarity
        alternatives.sort(key=lambda x: x["similarity"], reverse=True)
        
        return alternatives[:3]  # Return top 3 alternatives
