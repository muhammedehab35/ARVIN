from passlib.context import CryptContext
from sqlalchemy.orm import Session
import re
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from .database import get_db, User

security = HTTPBearer(auto_error=False)

# Configuration for password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    """Verify if plain password matches the hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Hash a password"""
    return pwd_context.hash(password)

def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_name(name):
    """Validate name (at least 2 characters, not just spaces)"""
    return len(name.strip()) >= 2

def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate a user"""
    user = get_user_by_email(db, email)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def create_user(db: Session, name: str, email: str, password: str):
    """Create a new user"""
    # Validations
    if not validate_name(name):
        raise ValueError("Name must contain at least 2 characters")
        
    if not validate_email(email):
        raise ValueError("Invalid email format")
        
    if len(password) < 4:
        raise ValueError("Password must contain at least 4 characters")
        
    # Check if email already exists
    if get_user_by_email(db, email):
        raise ValueError("This email is already in use")
        
    # Create the user
    hashed_password = get_password_hash(password)
    db_user = User(
        name=name.strip(),
        email=email.lower().strip(),
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current user (simplified version)"""
    user = db.query(User).filter(User.email == "test@test.com").first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user