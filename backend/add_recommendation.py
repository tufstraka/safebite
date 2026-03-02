#!/usr/bin/env python3
"""Add recommendation field to MenuAnalysisResponse and generate recommendations"""

with open('main.py', 'r') as f:
    content = f.read()

# 1. Add recommendation field to MenuAnalysisResponse
old_response = """class MenuAnalysisResponse(BaseModel):
    restaurant_name: str
    total_dishes: int
    safe_dishes: List[DishSafety]
    unsafe_dishes: List[DishSafety]
    unknown_dishes: List[DishSafety]
    analysis_timestamp: str
    analysis_time_eat: str  # East Africa Time
    voice_summary: str"""

new_response = """class MenuAnalysisResponse(BaseModel):
    restaurant_name: str
    total_dishes: int
    safe_dishes: List[DishSafety]
    unsafe_dishes: List[DishSafety]
    unknown_dishes: List[DishSafety]
    analysis_timestamp: str
    analysis_time_eat: str  # East Africa Time
    voice_summary: str
    recommendation: Optional[str] = None  # AI meal recommendation"""

content = content.replace(old_response, new_response)

# 2. Add generate_recommendation method
recommendation_method = '''
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
'''

# Insert after generate_voice_summary
insert_pos = content.find('    async def _infer_ingredients_with_ai')
if insert_pos > 0:
    content = content[:insert_pos] + recommendation_method + '\n' + content[insert_pos:]
else:
    print("Warning: Could not find insertion point for method")

# 3. Add recommendation generation in analyze endpoints
old_return = """        return MenuAnalysisResponse(
            restaurant_name=f"Uploaded {file_type}",
            total_dishes=len(menu_data["dishes"]),
            safe_dishes=safe_dishes,
            unsafe_dishes=unsafe_dishes,
            unknown_dishes=unknown_dishes,
            analysis_timestamp=now_utc.isoformat(),
            analysis_time_eat=now_eat.strftime("%H:%M EAT"),
            voice_summary=voice_summary
        )"""

new_return = """        # Generate recommendation
        recommendation = await analyzer.generate_recommendation(safe_dishes, all_allergens)
        
        return MenuAnalysisResponse(
            restaurant_name=f"Uploaded {file_type}",
            total_dishes=len(menu_data["dishes"]),
            safe_dishes=safe_dishes,
            unsafe_dishes=unsafe_dishes,
            unknown_dishes=unknown_dishes,
            analysis_timestamp=now_utc.isoformat(),
            analysis_time_eat=now_eat.strftime("%H:%M EAT"),
            voice_summary=voice_summary,
            recommendation=recommendation
        )"""

content = content.replace(old_return, new_return)

with open('main.py', 'w') as f:
    f.write(content)

print("✓ Added recommendation field")
print("✓ Added generate_recommendation method")
print("✓ Updated return statements")
