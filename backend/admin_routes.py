"""
Admin analytics endpoints for SafeBite
"""
from fastapi import APIRouter
from sqlalchemy import func, desc
from database import Scan, SessionLocal
from datetime import datetime, timedelta
from collections import Counter

router = APIRouter()

@router.get("/admin/stats")
async def get_admin_stats():
    """Get comprehensive admin statistics"""
    db = SessionLocal()
    
    try:
        # Total scans
        total_scans = db.query(func.count(Scan.id)).scalar() or 0
        
        # Total dishes analyzed
        total_dishes = db.query(func.sum(Scan.total_dishes)).scalar() or 0
        
        # Average safety
        avg_safe = db.query(func.avg(Scan.safe_count)).scalar() or 0
        avg_unsafe = db.query(func.avg(Scan.unsafe_count)).scalar() or 0
        avg_unknown = db.query(func.avg(Scan.unknown_count)).scalar() or 0
        
        # Recent scans (last 24h)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_scans = db.query(func.count(Scan.id)).filter(
            Scan.timestamp >= yesterday
        ).scalar() or 0
        
        # Top allergens
        all_scans = db.query(Scan.allergens).all()
        allergen_counter = Counter()
        for (allergens,) in all_scans:
            if allergens:
                allergen_counter.update(allergens)
        
        top_allergens = [
            {"allergen": k, "count": v} 
            for k, v in allergen_counter.most_common(10)
        ]
        
        # Recent activity
        recent_activity = db.query(Scan).order_by(
            desc(Scan.timestamp)
        ).limit(10).all()
        
        activity_list = [
            {
                "id": scan.id,
                "timestamp": scan.timestamp.isoformat(),
                "filename": scan.filename,
                "total_dishes": scan.total_dishes,
                "safe_count": scan.safe_count,
                "unsafe_count": scan.unsafe_count,
                "allergens": scan.allergens
            }
            for scan in recent_activity
        ]
        
        # File type breakdown
        file_types = db.query(
            Scan.file_type, 
            func.count(Scan.id)
        ).group_by(Scan.file_type).all()
        
        file_type_breakdown = {ft: count for ft, count in file_types}
        
        return {
            "total_scans": total_scans,
            "total_dishes": total_dishes,
            "recent_scans_24h": recent_scans,
            "average_safe": round(avg_safe, 1),
            "average_unsafe": round(avg_unsafe, 1),
            "average_unknown": round(avg_unknown, 1),
            "top_allergens": top_allergens,
            "recent_activity": activity_list,
            "file_types": file_type_breakdown
        }
        
    finally:
        db.close()

@router.get("/admin/scans")
async def get_all_scans(limit: int = 100, offset: int = 0):
    """Get all scans with pagination"""
    db = SessionLocal()
    
    try:
        scans = db.query(Scan).order_by(
            desc(Scan.timestamp)
        ).limit(limit).offset(offset).all()
        
        return {
            "scans": [
                {
                    "id": s.id,
                    "timestamp": s.timestamp.isoformat(),
                    "filename": s.filename,
                    "file_type": s.file_type,
                    "allergens": s.allergens,
                    "custom_allergens": s.custom_allergens,
                    "total_dishes": s.total_dishes,
                    "safe_count": s.safe_count,
                    "unsafe_count": s.unsafe_count,
                    "unknown_count": s.unknown_count,
                    "restaurant_name": s.restaurant_name,
                    "voice_summary": s.voice_summary
                }
                for s in scans
            ],
            "total": db.query(func.count(Scan.id)).scalar(),
            "limit": limit,
            "offset": offset
        }
        
    finally:
        db.close()
