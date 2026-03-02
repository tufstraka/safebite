"""
Database models for SafeBite
"""
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

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
