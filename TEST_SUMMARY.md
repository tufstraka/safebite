# Bug Fix Summary

## Problem
User selected allergens but got error: `400: Please specify at least one allergen`

## Root Cause
**Duplicate endpoint definitions** in backend/main.py:
- Line 323: NEW `/analyze/image` WITH `custom_allergens` parameter
- Line 694: OLD `/analyze/image` WITHOUT `custom_allergens` parameter

FastAPI registers endpoints in order - the OLD endpoint at line 694 OVERRODE the new one.

## Symptoms
1. Frontend sent correct data: `allergens=peanuts&custom_allergens=msg`
2. Backend received request but ignored `custom_allergens`
3. Backend used old endpoint: only checked `allergens` parameter
4. Since frontend didn't populate `allergens` for custom-only selections, got 400 error

## Fix Applied
Removed duplicate OLD endpoints (lines 694-798):
- Deleted old `/analyze/image` without custom support
- Deleted old `/analyze/url` without custom support
- Only 2 endpoints remain (both with custom allergen support)

## Verification
✅ Service restarted successfully
✅ Only 2 @app.post endpoints now (was 4)
✅ Both support `custom_allergens` parameter
✅ Frontend unchanged (was sending correct data all along)

## Test Instructions
1. Go to http://44.207.1.126/
2. Upload any menu image/PDF
3. Click allergen buttons (Peanuts, Gluten, etc.)
4. OR add custom allergens (MSG, Cilantro)
5. Click "Analyze Safety"
6. ✅ Should work without 400 error

## Files Modified
- backend/main.py: Removed lines 694-798 (duplicate endpoints)
- Git commit: a9c0202

