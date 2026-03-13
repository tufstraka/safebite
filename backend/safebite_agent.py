"""
SafeBite Agentic AI - Multi-Step Reasoning Agent
Demonstrates advanced agentic capabilities using Amazon Nova
"""

import boto3
import json
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AgentAction(Enum):
    """Actions the agent can take"""
    EXTRACT_MENU = "extract_menu"
    ANALYZE_DISH = "analyze_dish"
    CHECK_ALLERGEN = "check_allergen"
    INFER_INGREDIENTS = "infer_ingredients"
    CALCULATE_SAFETY = "calculate_safety"
    GENERATE_RECOMMENDATION = "generate_recommendation"
    FIND_ALTERNATIVES = "find_alternatives"
    COMPLETE = "complete"


@dataclass
class AgentStep:
    """Represents a single step in the agent's reasoning"""
    action: AgentAction
    input_data: Dict
    output_data: Optional[Dict] = None
    reasoning: str = ""
    confidence: float = 0.0


class SafeBiteAgent:
    """
    Agentic AI system for comprehensive menu safety analysis
    Uses multi-step reasoning with tool use capabilities
    """
    
    def __init__(self):
        """Initialize the SafeBite Agent"""
        try:
            self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
            self.model_id = 'us.amazon.nova-lite-v1:0'
            self.execution_trace: List[AgentStep] = []
            logger.info("SafeBite Agent initialized")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}")
            self.bedrock = None
    
    async def analyze_menu_with_reasoning(
        self,
        dishes: List[Dict],
        user_allergens: List[str],
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """
        Perform multi-step agentic analysis of menu
        
        This demonstrates:
        1. Planning - Determine analysis steps
        2. Tool Use - Call specialized functions
        3. Reasoning - Chain-of-thought analysis
        4. Memory - Track execution history
        """
        
        self.execution_trace = []
        
        # Step 1: Plan the analysis
        plan = await self._create_analysis_plan(dishes, user_allergens)
        
        # Step 2: Execute analysis for each dish
        analyzed_dishes = []
        for dish in dishes:
            dish_analysis = await self._analyze_single_dish(dish, user_allergens)
            analyzed_dishes.append(dish_analysis)
        
        # Step 3: Generate overall assessment
        assessment = await self._generate_assessment(analyzed_dishes, user_allergens)
        
        # Step 4: Find safe recommendations
        recommendations = await self._generate_recommendations(
            analyzed_dishes, user_allergens, user_preferences
        )
        
        # Step 5: Compile final result
        result = {
            "dishes": analyzed_dishes,
            "assessment": assessment,
            "recommendations": recommendations,
            "execution_trace": [
                {
                    "action": step.action.value,
                    "reasoning": step.reasoning,
                    "confidence": step.confidence
                }
                for step in self.execution_trace
            ],
            "agent_version": "1.0",
            "reasoning_steps": len(self.execution_trace)
        }
        
        return result
    
    async def _create_analysis_plan(
        self,
        dishes: List[Dict],
        user_allergens: List[str]
    ) -> Dict:
        """Create a plan for analyzing the menu"""
        
        step = AgentStep(
            action=AgentAction.EXTRACT_MENU,
            input_data={"dish_count": len(dishes), "allergens": user_allergens},
            reasoning=f"Planning analysis of {len(dishes)} dishes for {len(user_allergens)} allergens"
        )
        
        # Use Nova to plan
        if self.bedrock:
            try:
                prompt = f"""You are SafeBite AI Agent. Plan the analysis of a menu.

Menu has {len(dishes)} dishes.
User allergens: {', '.join(user_allergens)}

Create a brief analysis plan. Return JSON:
{{
    "steps": ["step1", "step2", ...],
    "priority_allergens": ["most_dangerous", ...],
    "estimated_risk_level": "low/medium/high"
}}"""

                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps({
                        "messages": [{"role": "user", "content": prompt}],
                        "inferenceConfig": {"temperature": 0.3, "maxTokens": 500}
                    })
                )
                
                result = json.loads(response['body'].read())
                plan_text = result['output']['message']['content'][0]['text']
                
                # Parse JSON from response
                start = plan_text.find('{')
                end = plan_text.rfind('}') + 1
                if start >= 0 and end > start:
                    plan = json.loads(plan_text[start:end])
                    step.output_data = plan
                    step.confidence = 0.9
                    
            except Exception as e:
                logger.error(f"Planning failed: {e}")
                step.output_data = {"steps": ["analyze_each_dish", "calculate_safety", "recommend"]}
                step.confidence = 0.5
        
        self.execution_trace.append(step)
        return step.output_data or {}
    
    async def _analyze_single_dish(
        self,
        dish: Dict,
        user_allergens: List[str]
    ) -> Dict:
        """Analyze a single dish with multi-step reasoning"""
        
        dish_name = dish.get('name', 'Unknown')
        dish_desc = dish.get('description', '')
        
        # Step: Infer hidden ingredients
        infer_step = AgentStep(
            action=AgentAction.INFER_INGREDIENTS,
            input_data={"dish": dish_name},
            reasoning=f"Inferring hidden ingredients in {dish_name}"
        )
        
        hidden_ingredients = []
        if self.bedrock:
            try:
                prompt = f"""What hidden ingredients are typically in "{dish_name}"?
Description: {dish_desc}

List ingredients that might not be obvious but are commonly used.
Return JSON array: ["ingredient1", "ingredient2", ...]"""

                response = self.bedrock.invoke_model(
                    modelId=self.model_id,
                    contentType='application/json',
                    accept='application/json',
                    body=json.dumps({
                        "messages": [{"role": "user", "content": prompt}],
                        "inferenceConfig": {"temperature": 0.2, "maxTokens": 300}
                    })
                )
                
                result = json.loads(response['body'].read())
                text = result['output']['message']['content'][0]['text']
                
                start = text.find('[')
                end = text.rfind(']') + 1
                if start >= 0 and end > start:
                    hidden_ingredients = json.loads(text[start:end])
                    
            except Exception as e:
                logger.error(f"Ingredient inference failed: {e}")
        
        infer_step.output_data = {"hidden_ingredients": hidden_ingredients}
        infer_step.confidence = 0.8
        self.execution_trace.append(infer_step)
        
        # Step: Check allergens - ONLY check for user's specified allergens
        check_step = AgentStep(
            action=AgentAction.CHECK_ALLERGEN,
            input_data={"dish": dish_name, "allergens": user_allergens},
            reasoning=f"Checking {dish_name} ONLY against user's specified allergens: {', '.join(user_allergens)}"
        )
        
        detected_allergens = []
        all_text = f"{dish_name} {dish_desc} {' '.join(hidden_ingredients)}".lower()
        
        # Keywords for each allergen type - ONLY used for allergens the user specified
        allergen_keywords = {
            "peanuts": ["peanut", "groundnut"],
            "tree nuts": ["almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia"],
            "nuts": ["nut", "almond", "walnut", "cashew", "pistachio", "pecan", "hazelnut", "macadamia", "peanut"],
            "milk": ["milk", "cheese", "cream", "butter", "dairy", "whey", "casein", "lactose"],
            "eggs": ["egg", "albumin", "mayonnaise", "meringue", "aioli"],
            "wheat": ["wheat", "flour", "bread", "pasta", "gluten", "breadcrumb"],
            "soy": ["soy", "tofu", "edamame", "soya"],
            "fish": ["fish", "salmon", "tuna", "cod", "anchovy", "bass", "trout"],
            "shellfish": ["shrimp", "crab", "lobster", "clam", "oyster", "mussel", "scallop", "prawn"],
            "sesame": ["sesame", "tahini"],
            "gluten": ["gluten", "wheat", "barley", "rye", "flour"]
        }
        
        # IMPORTANT: Only check for allergens the user is actually allergic to
        for allergen in user_allergens:
            allergen_lower = allergen.lower().strip()
            keywords = allergen_keywords.get(allergen_lower, [allergen_lower])
            if any(kw in all_text for kw in keywords):
                detected_allergens.append(allergen)
        
        check_step.output_data = {"detected": detected_allergens}
        check_step.confidence = 0.85
        self.execution_trace.append(check_step)
        
        # Step: Calculate safety score
        safety_step = AgentStep(
            action=AgentAction.CALCULATE_SAFETY,
            input_data={"detected_count": len(detected_allergens)},
            reasoning=f"Calculating safety score based on {len(detected_allergens)} detected allergens"
        )
        
        if detected_allergens:
            safety_score = max(0, 50 - len(detected_allergens) * 25)
            safety_level = "unsafe" if safety_score < 30 else "caution"
        else:
            safety_score = 90
            safety_level = "safe"
        
        safety_step.output_data = {"score": safety_score, "level": safety_level}
        safety_step.confidence = 0.9
        self.execution_trace.append(safety_step)
        
        return {
            "name": dish_name,
            "description": dish_desc,
            "price": dish.get('price', 'N/A'),
            "hidden_ingredients": hidden_ingredients,
            "detected_allergens": detected_allergens,
            "safety_score": safety_score,
            "safety_level": safety_level,
            "reasoning_steps": 3
        }
    
    async def _generate_assessment(
        self,
        analyzed_dishes: List[Dict],
        user_allergens: List[str]
    ) -> Dict:
        """Generate overall menu assessment"""
        
        safe_count = sum(1 for d in analyzed_dishes if d['safety_level'] == 'safe')
        caution_count = sum(1 for d in analyzed_dishes if d['safety_level'] == 'caution')
        unsafe_count = sum(1 for d in analyzed_dishes if d['safety_level'] == 'unsafe')
        
        total = len(analyzed_dishes)
        safe_percentage = (safe_count / total * 100) if total > 0 else 0
        
        if safe_percentage >= 70:
            overall_rating = "SAFE_RESTAURANT"
            message = "This restaurant has many safe options for you."
        elif safe_percentage >= 40:
            overall_rating = "MODERATE_RISK"
            message = "This restaurant has some safe options, but be careful."
        else:
            overall_rating = "HIGH_RISK"
            message = "This restaurant has limited safe options. Consider alternatives."
        
        return {
            "safe_count": safe_count,
            "caution_count": caution_count,
            "unsafe_count": unsafe_count,
            "safe_percentage": round(safe_percentage, 1),
            "overall_rating": overall_rating,
            "message": message
        }
    
    async def _generate_recommendations(
        self,
        analyzed_dishes: List[Dict],
        user_allergens: List[str],
        user_preferences: Optional[Dict] = None
    ) -> Dict:
        """Generate personalized recommendations"""
        
        step = AgentStep(
            action=AgentAction.GENERATE_RECOMMENDATION,
            input_data={"dish_count": len(analyzed_dishes)},
            reasoning="Generating personalized safe dish recommendations"
        )
        
        safe_dishes = [d for d in analyzed_dishes if d['safety_level'] == 'safe']
        
        # Sort by safety score
        safe_dishes.sort(key=lambda x: x['safety_score'], reverse=True)
        
        top_picks = safe_dishes[:3] if safe_dishes else []
        
        recommendation_text = ""
        if top_picks:
            names = [d['name'] for d in top_picks]
            recommendation_text = f"I recommend: {', '.join(names)}. These are your safest options."
        else:
            recommendation_text = "No completely safe dishes found. Please ask staff about modifications."
        
        step.output_data = {
            "top_picks": top_picks,
            "recommendation_text": recommendation_text
        }
        step.confidence = 0.85
        self.execution_trace.append(step)
        
        return step.output_data
    
    def get_execution_summary(self) -> str:
        """Get a human-readable summary of the agent's execution"""
        
        summary_lines = ["SafeBite Agent Execution Summary:", "=" * 40]
        
        for i, step in enumerate(self.execution_trace, 1):
            summary_lines.append(f"\nStep {i}: {step.action.value}")
            summary_lines.append(f"  Reasoning: {step.reasoning}")
            summary_lines.append(f"  Confidence: {step.confidence * 100:.0f}%")
        
        summary_lines.append(f"\nTotal Steps: {len(self.execution_trace)}")
        
        return "\n".join(summary_lines)
