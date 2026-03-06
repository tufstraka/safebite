"""
Database models for SafeBite
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import hashlib

Base = declarative_base()

class Scan(Base):
    """Store all menu scan data"""
    __tablename__ = 'scans'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # File info
    filename = Column(String(500))
    file_type = Column(String(50))  # PDF, Image
    
    # Allergens
    allergens = Column(JSON)  # List of allergen strings
    custom_allergens = Column(JSON)  # Custom allergens
    
    # Results
    total_dishes = Column(Integer)
    safe_count = Column(Integer)
    unsafe_count = Column(Integer)
    unknown_count = Column(Integer)
    
    # Metadata
    restaurant_name = Column(String(500))
    user_ip = Column(String(50))
    user_agent = Column(String(500))
    
    # Response data
    dishes = Column(JSON)  # Full dish analysis
    voice_summary = Column(String(1000))
    recommendation = Column(String(1000))

class User(Base):
    """Track unique users"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_hash = Column(String(64), unique=True, nullable=False)  # Hash of IP + user agent
    
    # First/Last activity
    first_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Activity stats
    total_scans = Column(Integer, default=0)
    total_dishes_checked = Column(Integer, default=0)
    
    # User details
    ip_address = Column(String(50))
    user_agent = Column(String(500))
    country = Column(String(100))  # Can be added later with IP geolocation
    city = Column(String(100))
    
    # Most common allergens
    top_allergens = Column(JSON)  # {allergen: count}

class Analytics(Base):
    """Store aggregated analytics"""
    __tablename__ = 'analytics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Daily stats
    total_scans = Column(Integer, default=0)
    total_dishes_scanned = Column(Integer, default=0)
    avg_safe_percentage = Column(Float, default=0.0)
    
    # Top allergens
    top_allergens = Column(JSON)  # {allergen: count}
    
    # Device info
    device_breakdown = Column(JSON)  # {device_type: count}


class Feedback(Base):
    """User feedback"""
    __tablename__ = 'feedback'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Feedback content
    message = Column(String(2000), nullable=False)
    rating = Column(Integer)  # 1-5 optional rating
    email = Column(String(200))  # Optional email for follow-up
    
    # Context
    page = Column(String(100))  # Which page they were on
    user_ip = Column(String(50))
    user_agent = Column(String(500))
    
    # Status
    status = Column(String(20), default='new')  # new, read, resolved
    admin_notes = Column(String(1000))

# Database setup
DB_PATH = os.path.join(os.path.dirname(__file__), 'safebite.db')
engine = create_engine(f'sqlite:///{DB_PATH}', echo=False)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(engine)
    print("✓ Database initialized")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_user_hash(ip_address: str, user_agent: str) -> str:
    """Generate unique hash for user based on IP + User-Agent"""
    combined = f"{ip_address}:{user_agent}"
    return hashlib.sha256(combined.encode()).hexdigest()

def track_user(db, ip_address: str, user_agent: str, allergens: list, total_dishes: int):
    """Track or update user activity"""
    user_hash = get_user_hash(ip_address, user_agent)
    
    user = db.query(User).filter(User.user_hash == user_hash).first()
    
    if user:
        # Update existing user
        user.last_seen = datetime.utcnow()
        user.total_scans += 1
        user.total_dishes_checked += total_dishes
        
        # Update top allergens
        if user.top_allergens is None:
            user.top_allergens = {}
        for allergen in allergens:
            user.top_allergens[allergen] = user.top_allergens.get(allergen, 0) + 1
    else:
        # Create new user
        top_allergens = {}
        for allergen in allergens:
            top_allergens[allergen] = 1
        
        user = User(
            user_hash=user_hash,
            ip_address=ip_address,
            user_agent=user_agent,
            total_scans=1,
            total_dishes_checked=total_dishes,
            top_allergens=top_allergens
        )
        db.add(user)
    
    db.commit()
    return user

def get_user_stats(db):
    """Get aggregated user statistics"""
    total_users = db.query(User).count()
    
    # Get active users (scanned in last 30 days)
    from datetime import timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(User).filter(User.last_seen >= thirty_days_ago).count()
    
    # Get returning users (>1 scan)
    returning_users = db.query(User).filter(User.total_scans > 1).count()
    
    # Get users by scan count
    users = db.query(User).all()
    avg_scans = sum(u.total_scans for u in users) / total_users if total_users > 0 else 0
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "returning_users": returning_users,
        "new_users": total_users - returning_users,
        "avg_scans_per_user": round(avg_scans, 2)
    }
