from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

# SQLite database configuration
DATABASE_URL = "sqlite:///./finbot_users.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# User model
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)

# Database session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Function to add test users (remove in production)
def add_test_users():
    from .auth import get_password_hash
    
    db = SessionLocal()
    
    # Check if users already exist
    existing_users = db.query(User).count()
    if existing_users > 0:
        db.close()
        return
    
    # Add some test users
    test_users = [
        {"name": "Admin User", "email": "admin@finbot.com", "password": "admin123"},
        {"name": "Test User", "email": "test@finbot.com", "password": "test123"},
        {"name": "Demo User", "email": "demo@finbot.com", "password": "demo123"},
    ]
    
    for user_data in test_users:
        hashed_password = get_password_hash(user_data["password"])
        db_user = User(
            name=user_data["name"],
            email=user_data["email"],
            password_hash=hashed_password
        )
        db.add(db_user)
    
    db.commit()
    db.close()
    print("✅ Test users added to database")