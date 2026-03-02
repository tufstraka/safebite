"""
Admin analytics endpoints for SafeBite
"""
from fastapi import APIRouter, HTTPException, Header, Depends
from sqlalchemy import func, desc
from database import Scan, User, SessionLocal, get_user_stats
from datetime import datetime, timedelta
from collections import Counter

router = APIRouter()

ADMIN_PASSCODE = "8992"

def verify_admin(x_admin_passcode: str = Header(None)):
    """Verify admin passcode from header"""
    if x_admin_passcode != ADMIN_PASSCODE:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True

@router.get("/admin/stats")
async def get_admin_stats(authorized: bool = Depends(verify_admin)):
    """Get comprehensive admin statistics"""
    db = SessionLocal()
    
    try:
        # User stats
        user_stats = get_user_stats(db)
        
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
            "users": user_stats,
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
async def get_all_scans(limit: int = 100, offset: int = 0, authorized: bool = Depends(verify_admin)):
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

@router.get("/admin/users/stats")
async def get_user_statistics(authorized: bool = Depends(verify_admin)):
    """Get aggregated user statistics"""
    db = SessionLocal()
    try:
        stats = get_user_stats(db)
        return stats
    finally:
        db.close()

@router.get("/admin/users/list")
async def get_users_list(limit: int = 50, offset: int = 0, authorized: bool = Depends(verify_admin)):
    """Get list of users with their details"""
    db = SessionLocal()
    try:
        users = db.query(User)\
            .order_by(desc(User.last_seen))\
            .limit(limit)\
            .offset(offset)\
            .all()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "user_hash": user.user_hash[:8] + "...",  # Truncate for privacy
                "first_seen": user.first_seen.isoformat(),
                "last_seen": user.last_seen.isoformat(),
                "total_scans": user.total_scans,
                "total_dishes_checked": user.total_dishes_checked,
                "top_allergens": user.top_allergens or {},
                "ip_address": user.ip_address,
                "user_agent": user.user_agent[:50] + "..." if user.user_agent and len(user.user_agent) > 50 else user.user_agent,
            })
        
        return {"users": user_list, "total": len(user_list)}
    finally:
        db.close()
