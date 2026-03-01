"""
Menu validation helper - detects if uploaded document is actually a food menu
"""

def is_food_menu(text: str) -> bool:
    """Check if text looks like a food menu, not some other document"""
    text_lower = text.lower()
    
    # Food-related keywords that should appear in menus
    food_keywords = [
        'menu', 'dish', 'served', 'grilled', 'fried', 'baked', 
        'chicken', 'beef', 'fish', 'pasta', 'salad', 'pizza',
        'soup', 'appetizer', 'entree', 'dessert', 'sandwich',
        'burger', 'rice', 'noodles', 'curry', 'sauce', 'fresh',
        'breakfast', 'lunch', 'dinner', 'beverage', 'drink'
    ]
    
    # Non-food keywords that indicate wrong document type
    non_food_keywords = [
        'vulnerability', 'security', 'exploit', 'cvss', 'penetration',
        'reconnaissance', 'bug bounty', 'xss', 'sql injection',
        'findings', 'severity', 'remediation', 'assessment',
        'invoice', 'receipt', 'payment', 'balance due',
        'report', 'executive summary', 'conclusion', 'recommendations',
        'client', 'contract', 'agreement', 'policy', 'terms'
    ]
    
    # Count food-related words
    food_count = sum(1 for keyword in food_keywords if keyword in text_lower)
    
    # Count non-food words (red flags)
    non_food_count = sum(1 for keyword in non_food_keywords if keyword in text_lower)
    
    # Decision logic
    if non_food_count > 3:
        # Clearly not a menu (security report, invoice, etc.)
        return False
    
    if food_count < 2:
        # No food words found
        return False
    
    # Looks like a menu
    return True
